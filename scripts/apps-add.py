#!/usr/bin/env python3
"""
App Adder for Fury's F-Droid Repository

This script helps users add new apps to the fury-fdroid repository by
interactively collecting information and generating the appropriate entry
for apps.yaml.
"""

import sys
import os
import yaml
import requests
from pathlib import Path


def get_app_info():
    """Interactively collect app information from the user"""
    print("App Adder for Fury's F-Droid Repository")
    print("========================================")
    
    # Get basic app information
    app_name = input("App name: ").strip()
    if not app_name:
        print("Error: App name is required!")
        sys.exit(1)
    
    pkg_id = input("Package ID: ").strip()
    if not pkg_id:
        print("Error: Package ID is required!")
        sys.exit(1)
    
    github_url = input("GitHub URL: ").strip()
    if not github_url:
        print("Error: GitHub URL is required!")
        sys.exit(1)
    
    icon_url = input("Icon URL (project-root/icon-path or GitHub raw URL): ").strip()
    if not icon_url:
        print("Error: Icon URL is required!")
        sys.exit(1)
    
    # Determine app category
    print("\nSelect app category:")
    categories = [
        "System", "Entertainment", "Development", 
        "Communication", "Security", "Gaming", "Misc"
    ]
    for i, cat in enumerate(categories, 1):
        print(f"{i}. {cat}")
    
    while True:
        try:
            cat_choice = int(input(f"Enter category number (1-{len(categories)}): "))
            if 1 <= cat_choice <= len(categories):
                selected_category = categories[cat_choice - 1]
                break
            else:
                print(f"Please enter a number between 1 and {len(categories)}")
        except ValueError:
            print("Please enter a valid number")
    
    # Determine status
    print("\nSelect app status:")
    statuses = ["Stable", "Alpha", "Beta", "Nightly", "Discontinued", "Maintained Fork", "Active"]
    for i, status in enumerate(statuses, 1):
        print(f"{i}. {status}")
    
    while True:
        try:
            status_choice = int(input(f"Enter status number (1-{len(statuses)}): "))
            if 1 <= status_choice <= len(statuses):
                selected_status = statuses[status_choice - 1]
                break
            else:
                print(f"Please enter a number between 1 and {len(statuses)}")
        except ValueError:
            print("Please enter a valid number")
    
    # Determine content type (optional)
    content_type = input("Content type (e.g., Manga, Anime, Music, Video, etc. - press Enter to skip): ").strip()
    
    # Determine if prefer_prerelease
    while True:
        prerelease = input("Prefer prerelease versions? (y/n): ").strip().lower()
        if prerelease in ['y', 'yes']:
            prefer_prerelease = True
            break
        elif prerelease in ['n', 'no']:
            prefer_prerelease = False
            break
        else:
            print("Please enter 'y' or 'n'")
    
    # Determine if archive old versions
    while True:
        archive = input("Archive old versions? (y/n): ").strip().lower()
        if archive in ['y', 'yes']:
            archive_old = True
            break
        elif archive in ['n', 'no']:
            archive_old = False
            break
        else:
            print("Please enter 'y' or 'n'")
    
    return {
        'name': app_name,
        'id': pkg_id,
        'url': github_url,
        'icon_url': icon_url,
        'category': selected_category,
        'status': selected_status,
        'content_type': content_type,
        'prefer_prerelease': prefer_prerelease,
        'archive': archive_old
    }


def validate_github_url(url):
    """Basic validation of GitHub URL"""
    if 'github.com' not in url:
        print(f"Warning: URL doesn't appear to be a GitHub URL: {url}")
        confirm = input("Continue anyway? (y/n): ").strip().lower()
        if confirm not in ['y', 'yes']:
            sys.exit(0)


def create_app_entry(app_info):
    """Create the app entry in the apps.yaml format"""
    entry = {
        'id': app_info['id'],
        'name': app_info['name'],
        'author': extract_author_from_url(app_info['url']),
        'url': app_info['url'],
        'classification': {
            'domain': app_info['category'],
            'type': app_info['category'],  # This can be refined later
        },
        'assets': {
            'icon': {
                'type': 'github-repo',
                'url': app_info['icon_url']
            }
        },
        'fdroid': {
            'categories': [app_info['category']]
        }
    }
    
    # Add content type if provided
    if app_info['content_type']:
        entry['classification']['content'] = app_info['content_type']
        entry['fdroid']['categories'].append(app_info['content_type'])
    
    # Add status
    entry['classification']['status'] = app_info['status']
    
    # Add prefer_prerelease if True
    if app_info['prefer_prerelease']:
        entry['fdroid']['prefer_prerelease'] = True
    
    # Add archive if True
    if app_info['archive']:
        entry['fdroid']['archive'] = True
    
    return entry


def extract_author_from_url(url):
    """Extract author name from GitHub URL"""
    # Example: https://github.com/author/repo -> author
    parts = url.rstrip('/').split('/')
    if len(parts) >= 4 and 'github.com' in parts:
        # Find the index of github.com and take the next part
        for i, part in enumerate(parts):
            if part == 'github.com' and i + 1 < len(parts):
                return parts[i + 1]
    return "unknown"


def load_apps_yaml(yaml_path):
    """Load existing apps.yaml file"""
    if os.path.exists(yaml_path):
        with open(yaml_path, 'r', encoding='utf-8') as f:
            return yaml.safe_load(f)
    else:
        # Create a default structure
        return {
            'schemaVersion': 2,
            'meta': {
                'name': 'Fury\'s F-Droid Repo',
                'description': 'Curated Android apps with clean, normalized metadata',
                'source': 'https://github.com/UnTamed-Fury/FDroid--repo'
            },
            'apps': []
        }


def save_apps_yaml(yaml_path, data):
    """Save apps.yaml file"""
    with open(yaml_path, 'w', encoding='utf-8') as f:
        yaml.dump(data, f, default_flow_style=False, allow_unicode=True, indent=2)


def main():
    if len(sys.argv) != 2:
        print("Usage: python3 apps-add.py <directory-name>")
        sys.exit(1)
    
    directory_name = sys.argv[1]
    
    print(f"Checking data in directory: {directory_name}")
    
    # Validate directory exists
    if not os.path.isdir(directory_name):
        print(f"Error: Directory '{directory_name}' does not exist!")
        sys.exit(1)
    
    # Collect app information
    app_info = get_app_info()
    
    # Validate GitHub URL
    validate_github_url(app_info['url'])
    
    # Create app entry
    app_entry = create_app_entry(app_info)
    
    # Load existing apps.yaml
    apps_yaml_path = Path("apps.yaml")
    apps_data = load_apps_yaml(apps_yaml_path)
    
    # Check if app ID already exists
    existing_ids = [app.get('id', '') for app in apps_data.get('apps', [])]
    if app_info['id'] in existing_ids:
        print(f"Warning: App with ID '{app_info['id']}' already exists!")
        confirm = input("Continue anyway? (y/n): ").strip().lower()
        if confirm not in ['y', 'yes']:
            sys.exit(0)
    
    # Add new app to the list
    apps_data['apps'].append(app_entry)
    
    # Save updated apps.yaml
    save_apps_yaml(apps_yaml_path, apps_data)
    
    print("\nApp entry created successfully!")
    print(f"Added to apps.yaml: {app_info['name']} ({app_info['id']})")
    
    # Show the generated entry
    print("\nGenerated entry:")
    print(yaml.dump([app_entry], default_flow_style=False, allow_unicode=True, indent=2))


if __name__ == "__main__":
    main()