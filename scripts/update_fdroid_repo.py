import os
import glob
import json
import yaml
import shutil
import requests
import subprocess
import sys
import traceback
import argparse

"""
F-Droid Repository Update Script
================================

This script handles the core logic for the F-Droid repository build process.
It operates in two distinct phases:

1. Download Phase (--download):
   - Reads 'apps.yaml' to identify tracked apps.
   - Fetches the latest APKs (up to MAX_VERSIONS) from GitHub Releases.
   - Verifies APK integrity and metadata using 'androguard'.
   - Generates metadata files for the Index phase.

2. Index Phase (--index):
   - Prepares the 'fdroid/repo' directory.
   - Copies downloaded APKs into the repo directory.
   - Runs 'fdroid update' (via fdroidserver) to generate the signed repository index.

Usage:
    python3 update_fdroid_repo.py --download
    python3 update_fdroid_repo.py --index
    python3 update_fdroid_repo.py --download --index (Run both)
"""

try:
    from androguard.core.bytecodes.apk import APK
except ImportError:
    try:
        from androguard.core.apk import APK
    except ImportError:
        # Fallback or maybe it's just 'androguard.apk' in some versions
        from androguard.apk import APK

# --- Config ---
APKS_DIR = "apks"
REPO_DIR = "fdroid/repo"
METADATA_DIR = "fdroid/metadata"
MAX_VERSIONS = 2

def get_github_headers(token):
    return {
        'Accept': 'application/vnd.github.v3+json',
        'Authorization': f'token {token}',
        'User-Agent': 'Fury-FDroid-Builder/3.0'
    }

def download_file(url, path):
    print(f"    ⬇ Downloading {url} -> {path}")
    with requests.get(url, stream=True, timeout=120) as r:
        r.raise_for_status()
        with open(path, 'wb') as f:
            for chunk in r.iter_content(chunk_size=8192):
                f.write(chunk)

def get_releases(repo_url, token, prefer_prerelease):
    owner, repo = repo_url.replace('https://github.com/', '').split('/')[:2]
    api_url = f"https://api.github.com/repos/{owner}/{repo}/releases"
    
    try:
        r = requests.get(api_url, headers=get_github_headers(token), timeout=30)
        r.raise_for_status()
        data = r.json()
    except Exception as e:
        print(f"    ⚠ Error fetching releases: {e}")
        return []

    valid_releases = []
    for rel in data:
        apk_assets = [a for a in rel['assets'] if a['name'].endswith('.apk')]
        if not apk_assets:
            continue
            
        is_pre = rel.get('prerelease', False)
        if not prefer_prerelease and is_pre:
            continue
            
        valid_releases.append({
            'tag': rel['tag_name'],
            'is_pre': is_pre,
            'assets': apk_assets,
            'body': rel.get('body', ''),
            'date': rel.get('published_at', '')
        })
        
    return valid_releases

def select_best_apk(assets):
    priority = ['arm64-v8a', 'universal', 'armeabi-v7a', 'x86_64', 'x86']
    for arch in priority:
        for asset in assets:
            if arch in asset['name'].lower():
                return asset
    return assets[0]

def clean_versions(app_dir):
    apks = sorted(glob.glob(os.path.join(app_dir, "*.apk")), key=os.path.getmtime, reverse=True)
    keep = apks[:MAX_VERSIONS]
    remove = apks[MAX_VERSIONS:]
    for f in remove:
        try:
            os.remove(f)
            print(f"    🗑 Deleted old version: {os.path.basename(f)}")
        except Exception as e:
            print(f"    ⚠ Failed to delete {f}: {e}")
            
def task_download():
    print("--- 📥 Starting Download Phase ---")
    token = os.environ.get('GH_TOKEN')
    if not token:
        print("Error: GH_TOKEN missing")
        sys.exit(1)

    with open('apps.yaml') as f:
        config = yaml.safe_load(f)

    for app in config.get('apps', []):
        app_id = app['id']
        name = app['name']
        repo_url = app.get('url') or app.get('source', {}).get('url')
        print(f"\n📦 Processing {name} ({app_id})...")
        
        app_dir = os.path.join(APKS_DIR, app_id)
        os.makedirs(app_dir, exist_ok=True)
        
        prefer_pre = app.get('fdroid', {}).get('prefer_prerelease', False)
        releases = get_releases(repo_url, token, prefer_pre)
        
        target_releases = releases[:MAX_VERSIONS]
        builds_metadata = []
        
        for rel in target_releases:
            asset = select_best_apk(rel['assets'])
            version = rel['tag']
            
            # Temporary filename for download
            temp_filename = f"{app_id}_{version.replace('/', '_')}_temp.apk"
            temp_filepath = os.path.join(app_dir, temp_filename)
            
            # 1. Download (if matching final file doesn't exist yet)
            # We don't know the final filename (with versionCode) yet, so we might redownload.
            # Optimization: Check if ANY file in dir matches expected checksum? Too slow.
            # Just download to temp and inspect.
            
            if not os.path.exists(temp_filepath):
                # Check if we already have a processed APK for this version?
                # Hard to know without metadata.
                # Let's download to temp.
                download_file(asset['browser_download_url'], temp_filepath)
            
            # 2. Inspect with Androguard
            try:
                apk = APK(temp_filepath)
                version_code = int(apk.get_androidversion_code())
                package_name = apk.get_package()
                
                # Verify package name matches (Optional but good safety)
                if package_name != app_id:
                    print(f"    ⚠ Warning: APK package {package_name} != config ID {app_id}")
                
                # 3. Rename to standard F-Droid format
                final_filename = f"{app_id}_{version_code}.apk"
                final_filepath = os.path.join(app_dir, final_filename)
                
                if not os.path.exists(final_filepath):
                    os.rename(temp_filepath, final_filepath)
                    print(f"    ✓ Processed: {final_filename}")
                else:
                    print(f"    ✓ Already exists: {final_filename}")
                    if os.path.exists(temp_filepath):
                        os.remove(temp_filepath) # Cleanup temp
                
                # 4. Add to Metadata
                builds_metadata.append({
                    'versionName': version,
                    'versionCode': version_code,
                    'commit': version,
                    'output': final_filename,
                    'disable': False
                })
                
            except Exception as e:
                print(f"    ✗ Failed to parse APK {temp_filename}: {e}")
                if os.path.exists(temp_filepath):
                    os.remove(temp_filepath)
                continue

        clean_versions(app_dir)
        
        # Write Metadata
        meta_path = os.path.join(METADATA_DIR, f"{app_id}.yml")
        metadata = {
            'Categories': app.get('categories', []) or app.get('fdroid', {}).get('categories', ['Uncategorized']),
            'Name': name,
            'Summary': app.get('description', 'No description'),
            'Description': app.get('description', 'No description'),
            'SourceCode': repo_url,
            'IssueTracker': f"{repo_url}/issues",
            'WebSite': repo_url,
            'License': 'Unknown',
            'AutoUpdateMode': 'None'
        }
        
        with open(meta_path, 'w') as f:
            yaml.dump(metadata, f, default_flow_style=False)

def task_index():
    print("\n--- 🏗️ Starting Index Phase ---")
    
    print("Populating F-Droid Repo Directory...")
    if os.path.exists(REPO_DIR):
        shutil.rmtree(REPO_DIR)
    os.makedirs(REPO_DIR)
    
    count = 0
    for root, dirs, files in os.walk(APKS_DIR):
        for file in files:
            if file.endswith('.apk'):
                src = os.path.join(root, file)
                dst = os.path.join(REPO_DIR, file)
                shutil.copy2(src, dst)
                count += 1
    print(f"Copied {count} APKs to {REPO_DIR}")

    print("Running F-Droid Update...")
    try:
        subprocess.run(['fdroid', 'update', '--create-metadata', '--pretty', '--verbose'], cwd='fdroid', check=True)
    except subprocess.CalledProcessError as e:
        print(f"Error running fdroid update: {e}")
        sys.exit(1)

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--download', action='store_true', help='Run download phase')
    parser.add_argument('--index', action='store_true', help='Run index phase')
    args = parser.parse_args()

    if not args.download and not args.index:
        args.download = True
        args.index = True

    if args.download:
        task_download()
    
    if args.index:
        task_index()

if __name__ == "__main__":
    main()
