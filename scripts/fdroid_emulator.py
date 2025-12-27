#!/usr/bin/env python3
"""
F-Droid Emulator & Repository Validator
Unified tool for testing Fury's F-Droid Repository.

Modes:
1. --local: Checks local directory structure (metadata, config, keystore).
2. --live: Checks the deployed F-Droid repository (URL access, indexes, APKs).
3. --script: Validates the python update script logic/imports.
"""

import os
import sys
import json
import yaml
import requests
import argparse
import traceback
import importlib.util
import random
from pathlib import Path

# Configuration
REPO_URL = "https://fury.untamedfury.space/repo"

def check_local_structure():
    """Validates the local file system layout."""
    print("=== 🏠 Local Structure Check ===")
    
    # 1. Directories
    required_dirs = ['fdroid', 'fdroid/metadata', 'fdroid/repo', 'apks', 'scripts', 'website']
    for d in required_dirs:
        if os.path.isdir(d):
            print(f"  ✓ Directory found: {d}")
        else:
            print(f"  ✗ Directory MISSING: {d}")

    # 2. Config Files
    if os.path.exists("apps.yaml"):
        print("  ✓ apps.yaml found")
        try:
            with open("apps.yaml", 'r') as f:
                data = yaml.safe_load(f)
                count = len(data.get('apps', []))
                print(f"    -> Parsed {count} apps")
        except Exception as e:
            print(f"    ✗ Error parsing apps.yaml: {e}")
    else:
        print("  ✗ apps.yaml MISSING")

    if os.path.exists("fdroid/config.yml"):
        print("  ✓ fdroid/config.yml found")
    else:
        print("  ✗ fdroid/config.yml MISSING")

    # 3. Keystore
    if os.path.exists("fdroid/keystore.p12"):
        size = os.path.getsize("fdroid/keystore.p12")
        print(f"  ✓ Keystore found ({size} bytes)")
    else:
        print("  ✗ Keystore MISSING")

    print("")

def check_live_repo():
    """Checks the publicly accessible F-Droid repository with detailed analysis."""
    print(f"=== 🌐 Live Repository Check ({REPO_URL}) ===")
    
    session = requests.Session()
    session.headers.update({'User-Agent': 'Fury-Emulator/3.0'})

    # 1. Index Access & Validation
    index_url = f"{REPO_URL}/index-v1.json"
    index_data = None
    
    try:
        print(f"  ⬇ Fetching {index_url}...")
        r = session.get(index_url, timeout=30)
        if r.status_code == 200:
            print(f"  ✓ Index accessible ({len(r.content)} bytes)")
            try:
                index_data = r.json()
                repo_name = index_data.get('repo', {}).get('name', 'Unknown')
                apps_count = len(index_data.get('apps', []))
                print(f"  ✓ Valid JSON: Repository '{repo_name}'")
                print(f"  ✓ Found {apps_count} apps in index")
            except json.JSONDecodeError:
                print("  ✗ Index contains invalid JSON")
        else:
            print(f"  ✗ Index inaccessible (Status: {r.status_code})")
    except Exception as e:
        print(f"  ✗ Connection failed: {e}")

    # 2. APK Availability Test
    if index_data and index_data.get('apps'):
        print("\n  🔍 Testing Random APK Availability:")
        apps = index_data['apps']
        sample_apps = random.sample(apps, min(3, len(apps)))
        
        for app in sample_apps:
            app_id = app.get('packageName', 'unknown')
            print(f"    - Checking {app_id}...")
            
            # Check packages inside the app
            packages = app.get('packages', [])
            if packages:
                latest_pkg = packages[0] # Usually sorted?
                apk_name = latest_pkg.get('apkName')
                if apk_name:
                    apk_url = f"{REPO_URL}/{apk_name}"
                    try:
                        head = session.head(apk_url, timeout=15)
                        if head.status_code == 200:
                            size = head.headers.get('Content-Length', 'unknown')
                            print(f"      ✓ APK accessible: {apk_name} ({size} bytes)")
                        else:
                            print(f"      ✗ APK missing: {apk_url} ({head.status_code})")
                    except Exception as e:
                        print(f"      ⚠ Error checking APK: {e}")
            else:
                print("      ⚠ No packages listed for app")

    # 3. Signature & Legacy
    print("\n  🔒 Checking Signatures:")
    for f in ['index.jar', 'index-v1.jar']:
        url = f"{REPO_URL}/{f}"
        try:
            r = session.head(url, timeout=10)
            if r.status_code == 200:
                print(f"  ✓ {f} found")
            else:
                print(f"  ✗ {f} missing ({r.status_code})")
        except:
            print(f"  ⚠ Error checking {f}")

    print("")

def validate_script():
    """Imports the main update script to check for syntax errors."""
    print("=== 🐍 Script Validation ===")
    script_path = "scripts/update_fdroid_repo.py"
    
    if not os.path.exists(script_path):
        print(f"  ✗ Script not found: {script_path}")
        return

    try:
        spec = importlib.util.spec_from_file_location("update_fdroid_repo", script_path)
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)
        print(f"  ✓ Syntax is valid for {script_path}")
        
        if hasattr(module, 'main'):
            print("  ✓ Found 'main' function")
        else:
            print("  ✗ Function 'main' missing")
            
    except Exception as e:
        print(f"  ✗ Script Import Failed: {e}")
        traceback.print_exc()
    print("")

def main():
    parser = argparse.ArgumentParser(description="Fury's F-Droid Emulator")
    parser.add_argument('--all', action='store_true', help='Run all checks')
    parser.add_argument('--local', action='store_true', help='Check local structure')
    parser.add_argument('--live', action='store_true', help='Check live repository')
    parser.add_argument('--script', action='store_true', help='Validate python script')
    
    args = parser.parse_args()

    if not any(vars(args).values()):
        parser.print_help()
        return

    if args.local or args.all:
        check_local_structure()
    if args.script or args.all:
        validate_script()
    if args.live or args.all:
        check_live_repo()

if __name__ == "__main__":
    main()