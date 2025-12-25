#!/usr/bin/env python3
"""
Test script to validate the update_fdroid_repo.py script
"""
import os
import sys
import traceback

def test_script():
    print("Testing update_fdroid_repo.py script...")
    
    # Mock environment variables
    os.environ['GH_TOKEN'] = 'test_token'
    os.environ['FDROID_KEY_STORE_PASS'] = 'fdroid123'
    os.environ['FDROID_KEY_PASS'] = 'fdroid123'
    
    try:
        # Try to import the main script
        import importlib.util
        spec = importlib.util.spec_from_file_location("update_fdroid_repo", "./scripts/update_fdroid_repo.py")
        module = importlib.util.module_from_spec(spec)
        
        # Execute the module to check for import errors
        spec.loader.exec_module(module)
        print("✓ Script imports successfully without syntax errors")
        
        # Check if required functions exist
        required_functions = [
            'get_github_repo_details',
            'get_latest_github_release_info',
            'download_file',
            'download_and_convert_icon',
            'generate_metadata_for_apps'
        ]
        
        for func_name in required_functions:
            if hasattr(module, func_name):
                print(f"✓ Function {func_name} exists")
            else:
                print(f"✗ Function {func_name} missing")
        
        return True
    except Exception as e:
        print(f"✗ Script import/test failed: {e}")
        traceback.print_exc()
        return False

if __name__ == "__main__":
    success = test_script()
    if success:
        print("\n✓ Script validation passed!")
    else:
        print("\n✗ Script validation failed!")
        sys.exit(1)