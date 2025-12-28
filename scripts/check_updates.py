import os
import json
import yaml
import requests
import sys

"""
F-Droid Update Watcher
======================

This script checks for new releases of apps defined in 'apps.yaml'.
It is designed to run frequently (e.g., via cron or scheduled CI job).

Features:
- Compares the latest GitHub Release tag against a local state file ('release_status.json').
- Outputs 'updates_found=true' to GitHub Actions outputs if changes are detected.
- Supports both stable and pre-release checks based on configuration.

Usage:
    python3 check_updates.py
"""

def get_github_headers(github_token):
    headers = {
        'Accept': 'application/vnd.github.v3+json',
        'User-Agent': 'Fury-FDroid-Bot/Watcher'
    }
    if github_token:
        headers['Authorization'] = f'token {github_token}'
    return headers

def check_updates():
    print("--- 🔍 Checking for Updates ---")
    
    github_token = os.environ.get('GH_TOKEN')
    if not github_token:
        print("Error: GH_TOKEN not set")
        sys.exit(1)

    # Load Apps
    try:
        with open('apps.yaml', 'r') as f:
            app_data = yaml.safe_load(f)
    except FileNotFoundError:
        print("apps.yaml not found")
        sys.exit(1)

    # Load Status
    status_file = 'release_status.json'
    if os.path.exists(status_file):
        with open(status_file, 'r') as f:
            try:
                status = json.load(f)
            except json.JSONDecodeError:
                status = {}
    else:
        status = {}

    updates_found = False
    
    for app in app_data.get('apps', []):
        app_id = app['id']
        repo_url = app.get('url') or app.get('source', {}).get('url')
        
        if not repo_url or 'github.com' not in repo_url:
            continue

        owner, repo = repo_url.replace('https://github.com/', '').split('/')[:2]
        api_url = f"https://api.github.com/repos/{owner}/{repo}/releases/latest"
        
        try:
            # Check latest release (ignoring pre-release preference for the watcher to keep it fast)
            # Or should we respect pre-release?
            # Ideally we check /releases and filter based on preference.
            # For simplicity/speed, checking 'latest' endpoint is usually good for stable.
            # But if prefer_prerelease is true, we need to check /releases.
            
            fdroid_config = app.get('fdroid', {})
            prefer_prerelease = fdroid_config.get('prefer_prerelease', False)
            
            if prefer_prerelease:
                api_url = f"https://api.github.com/repos/{owner}/{repo}/releases"
                resp = requests.get(api_url, headers=get_github_headers(github_token), timeout=10)
                resp.raise_for_status()
                releases = resp.json()
                if not releases: continue
                # Get first release (newest)
                latest_tag = releases[0]['tag_name']
            else:
                resp = requests.get(api_url, headers=get_github_headers(github_token), timeout=10)
                if resp.status_code == 404: continue # No release
                resp.raise_for_status()
                data = resp.json()
                latest_tag = data['tag_name']

            # Compare
            stored_tag = status.get(app_id)
            if latest_tag != stored_tag:
                print(f"  ★ New version for {app_id}: {stored_tag} -> {latest_tag}")
                status[app_id] = latest_tag
                updates_found = True
            else:
                # print(f"  . {app_id} is up to date ({latest_tag})")
                pass

        except Exception as e:
            print(f"  ⚠ Error checking {app_id}: {e}")

    if updates_found:
        print("updates_found=true")
        with open(status_file, 'w') as f:
            json.dump(status, f, indent=2)
        
        # Write to GITHUB_OUTPUT if running in Actions
        if 'GITHUB_OUTPUT' in os.environ:
            with open(os.environ['GITHUB_OUTPUT'], 'a') as f:
                f.write("updates_found=true\n")
    else:
        print("No updates found.")
        if 'GITHUB_OUTPUT' in os.environ:
            with open(os.environ['GITHUB_OUTPUT'], 'a') as f:
                f.write("updates_found=false\n")

if __name__ == "__main__":
    check_updates()
