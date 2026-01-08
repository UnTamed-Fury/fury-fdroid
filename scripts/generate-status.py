#!/usr/bin/env python3
"""
App Status Generator for Fury's F-Droid Repository

This script generates a markdown table showing the status of all apps in the repository.
"""

import yaml
from pathlib import Path
import requests
from datetime import datetime


def get_latest_release_info(repo_url):
    """Get the latest release info from GitHub"""
    try:
        # Convert GitHub URL to API URL
        if repo_url.endswith('.git'):
            repo_url = repo_url[:-4]
        
        # Extract owner and repo name from URL
        parts = repo_url.rstrip('/').split('/')
        if len(parts) >= 5 and 'github.com' in parts:
            owner_idx = parts.index('github.com') + 1
            if owner_idx + 1 < len(parts):
                owner = parts[owner_idx]
                repo = parts[owner_idx + 1]
                
                # Get latest release
                api_url = f"https://api.github.com/repos/{owner}/{repo}/releases/latest"
                response = requests.get(api_url)
                
                if response.status_code == 200:
                    release_data = response.json()
                    return {
                        'version': release_data.get('tag_name', 'N/A'),
                        'prerelease': release_data.get('prerelease', False),
                        'published_at': release_data.get('published_at', 'N/A')
                    }
                
                # If latest release fails, try getting all releases
                api_url = f"https://api.github.com/repos/{owner}/{repo}/releases"
                response = requests.get(api_url)
                
                if response.status_code == 200:
                    releases = response.json()
                    if releases:
                        latest = releases[0]  # First one is usually latest
                        return {
                            'version': latest.get('tag_name', 'N/A'),
                            'prerelease': latest.get('prerelease', False),
                            'published_at': latest.get('published_at', 'N/A')
                        }
    except Exception as e:
        print(f"Error fetching release info for {repo_url}: {e}")
    
    return {'version': 'N/A', 'prerelease': False, 'published_at': 'N/A'}


def generate_app_status_table(apps_yaml_path):
    """Generate markdown table of app statuses"""
    with open(apps_yaml_path, 'r', encoding='utf-8') as f:
        data = yaml.safe_load(f)
    
    apps = data.get('apps', [])
    
    # Header
    table = "| App Name | Latest Version | Source | Pre-release | Status |\n"
    table += "|----------|----------------|--------|-------------|--------|\n"
    
    for app in apps:
        name = app.get('name', 'N/A')
        pkg_id = app.get('id', 'N/A')
        source = app.get('url', 'N/A')
        
        # Get release info
        release_info = get_latest_release_info(source)
        version = release_info['version']
        prerelease = "Yes" if release_info['prerelease'] else "No"
        
        # Check if this is Revenge Manager to mark as having prerelease enabled
        if pkg_id == "app.revenge.manager":
            prerelease_setting = app.get('fdroid', {}).get('prefer_prerelease', False)
            prerelease_display = "Yes (configured)" if prerelease_setting else f"{prerelease} (auto)"
        else:
            prerelease_setting = app.get('fdroid', {}).get('prefer_prerelease', False)
            prerelease_display = "Yes" if prerelease_setting else prerelease
        
        # Status based on availability
        status = "Active" if version != "N/A" else "Inactive"
        
        table += f"| {name} | {version} | [{pkg_id}]({source}) | {prerelease_display} | {status} |\n"
    
    return table


def main():
    apps_yaml_path = Path("apps.yaml")

    if not apps_yaml_path.exists():
        print("apps.yaml not found in current directory")
        return

    table = generate_app_status_table(apps_yaml_path)

    # Write to markdown file in docs directory
    with open("docs/app-status.md", "w", encoding="utf-8") as f:
        f.write("# App Status Table\n\n")
        f.write("This table shows the current status of all apps in the repository.\n\n")
        f.write(f"Last updated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n\n")
        f.write(table)

    print("App status table generated in docs/app-status.md")


if __name__ == "__main__":
    main()