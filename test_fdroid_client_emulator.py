#!/usr/bin/env python3
"""
F-Droid Client Emulator - Tests repository functionality
Simulates what an actual F-Droid client does when connecting to the repository
"""

import os
import json
import yaml
import requests
import tempfile
import subprocess
from pathlib import Path


class FDroidClientEmulator:
    def __init__(self, repo_url):
        self.repo_url = repo_url
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'F-Droid-Emulator/1.0',
            'Accept': 'application/json'
        })
        
    def test_repository_access(self):
        """Test if the repository URL is accessible"""
        print("=== Testing Repository Access ===")
        
        # Test the main index files
        index_urls = [
            f"{self.repo_url}/index-v1.json",
            f"{self.repo_url}/index-v2.json"
        ]
        
        for url in index_urls:
            try:
                print(f"Testing {url}...")
                response = self.session.get(url, timeout=30)
                if response.status_code == 200:
                    print(f"  ✓ {url} is accessible (Status: {response.status_code})")
                    
                    # Validate JSON format
                    try:
                        data = response.json()
                        print(f"  ✓ {url} contains valid JSON")
                        
                        # Check for required fields in F-Droid index
                        if 'repo' in data:
                            print(f"  ✓ Repository info found: {data['repo'].get('name', 'Unknown')}")
                        else:
                            print(f"  ⚠ {url} missing 'repo' field")
                            
                        if 'apps' in data:
                            print(f"  ✓ Found {len(data['apps'])} apps in repository")
                        else:
                            print(f"  ⚠ {url} missing 'apps' field")
                            
                    except json.JSONDecodeError:
                        print(f"  ✗ {url} contains invalid JSON")
                        
                else:
                    print(f"  ✗ {url} is not accessible (Status: {response.status_code})")
            except Exception as e:
                print(f"  ✗ Error accessing {url}: {e}")
                
    def test_apk_availability(self):
        """Test if APKs referenced in the index are accessible"""
        print("\n=== Testing APK Availability ===")
        
        # Get the index to find APKs to test
        index_url = f"{self.repo_url}/index-v2.json"
        try:
            response = self.session.get(index_url, timeout=30)
            if response.status_code == 200:
                index_data = response.json()
                apps = index_data.get('apps', {})
                
                tested_apks = 0
                successful_apks = 0
                
                for app_id, app_info in list(apps.items())[:5]:  # Test first 5 apps
                    print(f"Testing APKs for {app_id}...")
                    
                    packages = app_info.get('packages', {})
                    if packages:
                        # Test the latest package
                        latest_package = next(iter(packages.values()))  # Get first (latest) package
                        apk_name = latest_package.get('apkName', '')
                        
                        if apk_name:
                            apk_url = f"{self.repo_url}/{apk_name}"
                            print(f"  Testing APK: {apk_name}")
                            
                            try:
                                apk_response = self.session.head(apk_url, timeout=30)  # Use HEAD to check availability without downloading
                                if apk_response.status_code == 200:
                                    content_length = apk_response.headers.get('Content-Length', 'Unknown')
                                    print(f"    ✓ {apk_name} is accessible (Size: {content_length} bytes)")
                                    successful_apks += 1
                                else:
                                    print(f"    ✗ {apk_name} not accessible (Status: {apk_response.status_code})")
                            except Exception as e:
                                print(f"    ✗ Error accessing {apk_name}: {e}")
                                
                            tested_apks += 1
                            
                            if tested_apks >= 3:  # Only test first 3 APKs to avoid too many requests
                                break
                    else:
                        print(f"  ⚠ No packages found for {app_id}")
                        
                print(f"\nAPK availability: {successful_apks}/{tested_apks} tested APKs accessible")
            else:
                print(f"✗ Could not access index file: {response.status_code}")
        except Exception as e:
            print(f"✗ Error testing APK availability: {e}")
            
    def test_repository_signature(self):
        """Test if repository signature files exist and are accessible"""
        print("\n=== Testing Repository Signatures ===")
        
        signature_files = [
            f"{self.repo_url}/index-v1.jar",
            f"{self.repo_url}/index-v2.jar"
        ]
        
        for sig_url in signature_files:
            try:
                response = self.session.head(sig_url, timeout=30)
                if response.status_code == 200:
                    print(f"  ✓ Signature file accessible: {os.path.basename(sig_url)}")
                else:
                    print(f"  ✗ Signature file not accessible: {os.path.basename(sig_url)} (Status: {response.status_code})")
            except Exception as e:
                print(f"  ✗ Error accessing signature file {os.path.basename(sig_url)}: {e}")
                
    def test_icon_availability(self):
        """Test if app icons are accessible"""
        print("\n=== Testing Icon Availability ===")
        
        # Icons would be in the metadata directory
        # For this test, we'll check if the repository has the expected structure
        try:
            # Test if we can access the metadata directory structure
            metadata_url = f"{self.repo_url}/../metadata/"  # This might not work with GitHub Pages
            print(f"  Note: Direct metadata directory access might not be enabled on GitHub Pages")
        except:
            pass  # This is expected for GitHub Pages
            
        # Test a few specific icon URLs if we can find them in the index
        index_url = f"{self.repo_url}/index-v2.json"
        try:
            response = self.session.get(index_url, timeout=30)
            if response.status_code == 200:
                index_data = response.json()
                apps = index_data.get('apps', {})
                
                tested_icons = 0
                successful_icons = 0
                
                for app_id in list(apps.keys())[:3]:  # Test first 3 apps
                    icon_url = f"{self.repo_url}/../icons/{app_id}.png"  # This might not work with GitHub Pages
                    # Alternative: icons might be in the metadata directory
                    alt_icon_url = f"{self.repo_url}/../metadata/{app_id}.png"  # This might not work with GitHub Pages
                    
                    # For GitHub Pages, icons are typically at /repo/../metadata/icons/
                    alt_icon_url2 = f"{self.repo_url}/../metadata/icons/{app_id}.png"
                    
                    # Try the most common pattern for F-Droid repositories
                    icon_urls_to_try = [
                        f"{self.repo_url}/icons/{app_id}.png",  # In repo directory
                        f"{self.repo_url}/../metadata/icons/{app_id}.png",  # In metadata/icons directory
                    ]
                    
                    for icon_url in icon_urls_to_try:
                        try:
                            icon_response = self.session.head(icon_url, timeout=15)
                            if icon_response.status_code == 200:
                                print(f"  ✓ Icon accessible for {app_id}: {icon_response.status_code}")
                                successful_icons += 1
                                break
                        except:
                            continue
                    else:
                        print(f"  ⚠ Icon not accessible for {app_id}")
                        
                    tested_icons += 1
                    if tested_icons >= 3:
                        break
                        
                print(f"Icon availability: {successful_icons}/{tested_icons} tested icons accessible")
        except Exception as e:
            print(f"  ⚠ Error testing icon availability: {e}")
            
    def run_comprehensive_test(self):
        """Run all tests to validate repository functionality"""
        print(f"F-Droid Client Emulator Testing Repository: {self.repo_url}\n")

        self.test_repository_access()
        self.test_apk_availability()
        self.test_repository_signature()
        self.test_icon_availability()

        print("\n=== Test Summary ===")
        print("This emulator tests the repository from an F-Droid client perspective.")
        print("If all tests pass, the repository should be accessible to F-Droid clients.")
        print("\nNote: Some tests may fail due to GitHub Pages configuration restrictions.")
        print("For full F-Droid compatibility, ensure:")
        print("1. Index files (index-v1.json, index-v2.json) are accessible")
        print("2. APK files referenced in the index are downloadable")
        print("3. Signature files (index-v1.jar, index-v2.jar) are accessible")
        print("4. Repository is properly signed with the correct keystore")


def main():
    # Use the repository URL from the config
    repo_url = "https://fury.untamedfury.space/repo"
    
    emulator = FDroidClientEmulator(repo_url)
    emulator.run_comprehensive_test()


if __name__ == "__main__":
    main()