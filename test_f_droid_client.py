#!/usr/bin/env python3
"""
Simple F-Droid client simulator to test the repository
"""

import os
import json
import yaml
import requests
import subprocess
from pathlib import Path

def test_fdroid_repository():
    """
    Test if the F-Droid repository is properly structured and accessible
    """
    print("=== F-Droid Repository Test ===\n")
    
    # Test metadata files (these are stored in git)
    print("1. Testing metadata files...")
    metadata_dir = "fdroid/metadata"
    if os.path.exists(metadata_dir):
        print("   ✓ Metadata directory exists")
        
        # Check for some .yml files
        metadata_files = [f for f in os.listdir(metadata_dir) if f.endswith('.yml')]
        yml_files = [f for f in metadata_files if f != 'index-v1.yml' and f != 'index-v2.yml']  # Exclude index files if they exist
        print(f"   → Found {len(yml_files)} app metadata files")
        
        if yml_files:
            # Test first few metadata files
            for meta_file in yml_files[:3]:  # Test first 3 files
                meta_path = os.path.join(metadata_dir, meta_file)
                try:
                    with open(meta_path, 'r') as f:
                        meta_data = yaml.safe_load(f)
                    
                    print(f"   ✓ Metadata file {meta_file} is valid YAML")
                    
                    # Check if it has required fields for F-Droid
                    required_fields = ['Name', 'Summary', 'SourceCode', 'Builds']
                    missing_fields = [field for field in required_fields if field not in meta_data]
                    
                    if not missing_fields:
                        print(f"     ✓ Has all required fields: {', '.join(required_fields)}")
                    else:
                        print(f"     ⚠ Missing required fields: {missing_fields}")
                    
                    # Check Builds section
                    builds = meta_data.get('Builds', [])
                    if builds:
                        print(f"     ✓ Has {len(builds)} build entries")
                        if builds and 'versionName' in builds[0]:
                            print(f"     → Latest version: {builds[0]['versionName']}")
                    else:
                        print(f"     ⚠ No Builds section in {meta_file}")
                        
                except Exception as e:
                    print(f"   ✗ Error reading metadata file {meta_file}: {e}")
        else:
            print("   ⚠ No app metadata files found in fdroid/metadata/")
    else:
        print("   ✗ Metadata directory missing")
    
    # Test config file
    print("\n2. Testing configuration file...")
    config_path = "fdroid/config.yml"
    if os.path.exists(config_path):
        print("   ✓ Config file exists")
        try:
            with open(config_path, 'r') as f:
                config_data = yaml.safe_load(f)
            
            # Check for required config fields
            required_config_fields = ['repo_url', 'repo_name', 'keystore', 'repo_keyalias']
            missing_config_fields = [field for field in required_config_fields if field not in config_data]
            
            if not missing_config_fields:
                print(f"   ✓ Config has all required fields: {', '.join(required_config_fields)}")
                print(f"   → Repository URL: {config_data.get('repo_url', 'Not found')}")
            else:
                print(f"   ⚠ Config missing required fields: {missing_config_fields}")
                
        except Exception as e:
            print(f"   ✗ Error reading config file: {e}")
    else:
        print("   ✗ Config file missing")
    
    # Test keystore
    print("\n3. Testing keystore...")
    keystore_path = "fdroid/keystore.p12"
    if os.path.exists(keystore_path):
        print("   ✓ Keystore file exists")
        # Check file size to ensure it's not empty
        size = os.path.getsize(keystore_path)
        if size > 0:
            print(f"   ✓ Keystore file has content ({size} bytes)")
        else:
            print(f"   ✗ Keystore file is empty")
    else:
        print("   ✗ Keystore file missing")
    
    # Test if apps.yaml has the proper structure
    print("\n4. Testing apps.yaml structure...")
    apps_yaml_path = "apps.yaml"
    if os.path.exists(apps_yaml_path):
        print("   ✓ apps.yaml file exists")
        try:
            with open(apps_yaml_path, 'r') as f:
                apps_data = yaml.safe_load(f)
            
            apps = apps_data.get('apps', [])
            print(f"   → Found {len(apps)} apps in configuration")
            
            # Test a few apps
            for app in apps[:2]:  # Test first 2 apps
                app_id = app.get('id')
                app_name = app.get('name')
                print(f"     → App: {app_name} ({app_id})")
                
                # Check for required fields
                if 'url' in app or 'source' in app:
                    print(f"       ✓ Has repository URL")
                else:
                    print(f"       ⚠ Missing repository URL")
                    
                if 'fdroid' in app:
                    fdroid_config = app.get('fdroid', {})
                    if 'prefer_prerelease' in fdroid_config or 'categories' in fdroid_config:
                        print(f"       ✓ Has fdroid configuration")
                    else:
                        print(f"       ⚠ Has fdroid section but missing settings")
                else:
                    print(f"       ⚠ Missing fdroid configuration")
                    
        except Exception as e:
            print(f"   ✗ Error reading apps.yaml: {e}")
    else:
        print("   ✗ apps.yaml file missing")
    
    print("\n=== Test Complete ===")
    print("This test verifies the local repository structure.")
    print("The actual repository index files are generated during GitHub Actions workflow.")
    print("If all workflows are passing, the repository should be functional with F-Droid clients.")
    print("\nTo test with an actual F-Droid client:")
    print("1. Repository URL: https://fury.untamedfury.space/repo")
    print("2. Repository fingerprint: BD:3D:60:C7:D6:AA:34:20:42:78:62:9B:0F:BC:EC:E7:B6:80:2E:6B:C6:7C:5F:11:12:D2:60:D4:21:86:EE:E6")
    
    return True

if __name__ == "__main__":
    test_fdroid_repository()