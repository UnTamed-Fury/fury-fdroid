#!/usr/bin/env python3
"""
App Adder for Fury's F-Droid Repository (Simplified Version)

This script helps users add new apps to the fury-fdroid repository by
analyzing a cloned app repository and generating the appropriate entry
for apps.yaml.
"""

import sys
import os
import yaml
import json
import re
from pathlib import Path


def extract_info_from_repo(repo_path):
    """Extract app information from a cloned repository"""
    repo_path = Path(repo_path)
    
    # Look for app information in common places
    app_info = {
        'name': 'Unknown',
        'id': 'unknown.package.id',
        'author': 'unknown',
        'url': 'https://github.com/unknown/unknown',
        'icon_url': '',
        'category': 'Misc',
        'status': 'Stable',
        'content_type': '',
        'prefer_prerelease': False,
        'archive': False
    }
    
    # Extract repo name and author from path
    # Assuming the path is like: /some/path/author/repo_name
    path_parts = str(repo_path).rstrip('/').split('/')
    if len(path_parts) >= 2:
        repo_name = path_parts[-1]
        # Look for the author as the directory before the repo directory
        # This assumes the format is like: .../author/repo_name
        if len(path_parts) >= 2:
            author = path_parts[-2]
        else:
            author = "unknown"
        app_info['author'] = author
        app_info['url'] = f"https://github.com/{author}/{repo_name}"
    else:
        # If we can't determine from path, use defaults
        app_info['author'] = "unknown"
        app_info['url'] = "https://github.com/unknown/unknown"
    
    # Try to get app name from repo name (convert from kebab-case or snake_case to title case)
    app_name = repo_name.replace('-', ' ').replace('_', ' ').title()
    app_info['name'] = app_name
    
    # Look for package ID in common Android files
    possible_locations = [
        'app/build.gradle',
        'app/build.gradle.kts',
        'app/src/main/AndroidManifest.xml',
        'build.gradle',
        'build.gradle.kts'
    ]
    
    for location in possible_locations:
        full_path = repo_path / location
        if full_path.exists():
            content = full_path.read_text(encoding='utf-8', errors='ignore')
            
            # Look for applicationId in build.gradle files
            if 'build.gradle' in location:
                # Look for applicationId pattern
                app_id_match = re.search(r'applicationId\s+["\']([^"\']+)["\']', content)
                if app_id_match:
                    app_info['id'] = app_id_match.group(1)
                    break
            
            # Look for package in AndroidManifest.xml
            elif 'AndroidManifest.xml' in location:
                package_match = re.search(r'package\s*=\s*["\']([^"\']+)["\']', content)
                if package_match:
                    app_info['id'] = package_match.group(1)
                    break
    
    # Look for icon in common locations
    icon_locations = [
        'app/src/main/res/mipmap-xxxhdpi/ic_launcher.png',
        'app/src/main/res/mipmap-xxhdpi/ic_launcher.png',
        'app/src/main/res/mipmap-xhdpi/ic_launcher.png',
        'app/src/main/res/drawable/ic_launcher.png',
        'fastlane/metadata/android/en-US/images/icon.png',
        'metadata/en-US/icon.png'
    ]
    
    for icon_loc in icon_locations:
        full_path = repo_path / icon_loc
        if full_path.exists():
            app_info['icon_url'] = f"https://raw.githubusercontent.com/{app_info['author']}/{repo_name}/main/{icon_loc}"
            break
    
    # If no icon found, use a default GitHub repo icon reference
    if not app_info['icon_url']:
        app_info['icon_url'] = f"https://github.com/{app_info['author']}/{repo_name}"
    
    return app_info


def create_app_entry(app_info):
    """Create the app entry in the apps.yaml format"""
    entry = {
        'id': app_info['id'],
        'name': app_info['name'],
        'author': app_info['author'],
        'url': app_info['url'],
        'classification': {
            'domain': app_info['category'],
            'type': app_info['category'],
            'status': app_info['status']
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
    
    # Add prefer_prerelease if True
    if app_info['prefer_prerelease']:
        entry['fdroid']['prefer_prerelease'] = True
    
    # Add archive if True
    if app_info['archive']:
        entry['fdroid']['archive'] = True
    
    return entry


def main():
    if len(sys.argv) != 3 or sys.argv[2] != '-gen':
        print("Usage: python3 app-add.py <app-repo> -gen")
        print("Note: This tool only supports GitHub repositories")
        sys.exit(1)
    
    repo_path = sys.argv[1]
    
    print(f"Analyzing repository: {repo_path}")
    
    # Validate directory exists
    if not os.path.isdir(repo_path):
        print(f"Error: Directory '{repo_path}' does not exist!")
        sys.exit(1)
    
    # Extract app information from the repository
    app_info = extract_info_from_repo(repo_path)
    
    print(f"App name: {app_info['name']}")
    print(f"Package ID: {app_info['id']}")
    print(f"GitHub URL: {app_info['url']}")
    print(f"Icon URL: {app_info['icon_url']}")
    
    # Ask for category
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
                app_info['category'] = categories[cat_choice - 1]
                break
            else:
                print(f"Please enter a number between 1 and {len(categories)}")
        except ValueError:
            print("Please enter a valid number")
    
    # Ask for status
    print("\nSelect app status:")
    statuses = ["Stable", "Alpha", "Beta", "Nightly", "Discontinued", "Maintained Fork", "Active"]
    for i, status in enumerate(statuses, 1):
        print(f"{i}. {status}")
    
    while True:
        try:
            status_choice = int(input(f"Enter status number (1-{len(statuses)}): "))
            if 1 <= status_choice <= len(statuses):
                app_info['status'] = statuses[status_choice - 1]
                break
            else:
                print(f"Please enter a number between 1 and {len(statuses)}")
        except ValueError:
            print("Please enter a valid number")
    
    # Ask for content type (optional)
    content_type = input("Content type (e.g., Manga, Anime, Music, Video, etc. - press Enter to skip): ").strip()
    app_info['content_type'] = content_type if content_type else ''
    
    # Ask for prefer_prerelease
    while True:
        prerelease = input("Prefer prerelease versions? (y/n): ").strip().lower()
        if prerelease in ['y', 'yes']:
            app_info['prefer_prerelease'] = True
            break
        elif prerelease in ['n', 'no']:
            app_info['prefer_prerelease'] = False
            break
        else:
            print("Please enter 'y' or 'n'")
    
    # Create app entry
    app_entry = create_app_entry(app_info)
    
    # Generate just the app entry
    yaml_content = yaml.dump([app_entry], default_flow_style=False, allow_unicode=True, indent=2)

    # Print the app entry to stdout so user can copy it
    print(f"\nApp entry generated for: {app_info['name']} ({app_info['id']})")
    print("Copy and paste this entry into your apps.yaml file under the 'apps:' section:\n")
    print("-" * 50)
    print(yaml_content)
    print("-" * 50)
    print("\nNote: This tool only supports GitHub repositories")


if __name__ == "__main__":
    main()