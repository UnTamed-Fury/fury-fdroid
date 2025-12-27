import os
import glob
import json
import yaml
import shutil
import requests
import subprocess
import sys
import traceback

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
        # Filter assets
        apk_assets = [a for a in rel['assets'] if a['name'].endswith('.apk')]
        if not apk_assets:
            continue
            
        is_pre = rel.get('prerelease', False)
        
        # If we prefer prerelease, take everything. 
        # If we don't, skip prereleases.
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
    # Sort by arch preference
    priority = ['arm64-v8a', 'universal', 'armeabi-v7a', 'x86_64', 'x86']
    
    for arch in priority:
        for asset in assets:
            if arch in asset['name'].lower():
                return asset
    
    return assets[0] # Fallback to first

def clean_versions(app_dir):
    """Enforce retention rule: Keep MAX_VERSIONS latest APKs."""
    apks = sorted(glob.glob(os.path.join(app_dir, "*.apk")), key=os.path.getmtime, reverse=True)
    
    keep = apks[:MAX_VERSIONS]
    remove = apks[MAX_VERSIONS:]
    
    for f in remove:
        try:
            os.remove(f)
            print(f"    🗑 Deleted old version: {os.path.basename(f)}")
        except Exception as e:
            print(f"    ⚠ Failed to delete {f}: {e}")
            
    return [os.path.basename(k) for k in keep]

def main():
    print("--- 🏗️ Starting Build Process ---")
    token = os.environ.get('GH_TOKEN')
    if not token:
        print("Error: GH_TOKEN missing")
        sys.exit(1)

    with open('apps.yaml') as f:
        config = yaml.safe_load(f)

    # 1. Process Apps
    for app in config.get('apps', []):
        app_id = app['id']
        name = app['name']
        repo_url = app.get('url') or app.get('source', {}).get('url')
        print(f"\n📦 Processing {name} ({app_id})...")
        
        # Setup dirs
        app_dir = os.path.join(APKS_DIR, app_id)
        os.makedirs(app_dir, exist_ok=True)
        
        # Fetch Releases
        prefer_pre = app.get('fdroid', {}).get('prefer_prerelease', False)
        releases = get_releases(repo_url, token, prefer_pre)
        
        # We only want top N releases to save space/time
        target_releases = releases[:MAX_VERSIONS]
        
        builds_metadata = []
        
        for rel in target_releases:
            asset = select_best_apk(rel['assets'])
            version = rel['tag']
            
            # Construct filename: package_versionCode.apk logic
            # Simpler logic: package_versionName.apk to avoid parsing code?
            # F-Droid likes package_code.apk.
            # We will use a consistent naming: {app_id}_{sanitized_version}.apk
            sanitized_version = version.replace('/', '_') # Basic sanitization
            filename = f"{app_id}_{sanitized_version}.apk"
            filepath = os.path.join(app_dir, filename)
            
            # Download if missing
            if not os.path.exists(filepath):
                download_file(asset['browser_download_url'], filepath)
            else:
                print(f"    ✓ Exists: {filename}")
                
            builds_metadata.append({
                'versionName': version,
                'versionCode': 1, # Dummy code, fdroidscanner might update this? 
                                  # Actually fdroid server reads the APK to get real versionCode.
                                  # So we can put anything here or let it auto-detect?
                                  # YAML requires 'versionCode', 'versionName'.
                                  # We should probably let 'fdroid update' handle the scanning 
                                  # but we are writing the metadata file manually.
                                  # Wait, if we use 'fdroid update', it scans APKs.
                                  # We just need to provide basic metadata.
                'commit': version,
                'output': filename,
                'disable': False
            })

        # Cleanup old files
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
            'AutoUpdateMode': 'None',
            'Builds': builds_metadata
        }
        
        with open(meta_path, 'w') as f:
            yaml.dump(metadata, f, default_flow_style=False)

    # 2. Populate Repo Directory (Symlink/Copy)
    print("\n--- 🔗 Populating F-Droid Repo Directory ---")
    if os.path.exists(REPO_DIR):
        shutil.rmtree(REPO_DIR)
    os.makedirs(REPO_DIR)
    
    # Copy/Link APKs
    # We use copy because symlinks might be tricky with artifacts/pages sometimes, 
    # but copying doubles usage? No, we just need them there for 'fdroid update'.
    # Afterwards we can delete them from repo/ if we deploy only index?
    # No, we need to deploy APKs too.
    # So we copy them to repo/ and then deploy repo/.
    
    count = 0
    for root, dirs, files in os.walk(APKS_DIR):
        for file in files:
            if file.endswith('.apk'):
                src = os.path.join(root, file)
                dst = os.path.join(REPO_DIR, file)
                shutil.copy2(src, dst)
                count += 1
    print(f"Copied {count} APKs to {REPO_DIR}")

    # 3. F-Droid Update
    print("\n--- 🔄 Running F-Droid Update ---")
    # Config injection handles externally in workflow or here?
    # Let's assume env vars are set.
    
    try:
        subprocess.run(['fdroid', 'update', '--create-metadata', '--pretty', '--verbose'], cwd='fdroid', check=True)
    except subprocess.CalledProcessError as e:
        print(f"Error running fdroid update: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()
