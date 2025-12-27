# F-Droid Repository Workflow Breakdown

This document explains how the main "Build CI" workflow operates, broken down into its key steps.

## Step 3: Create Secure Config
```bash
# What happens:
- Creates a temporary config file with actual passwords from GitHub Secrets
- Replaces placeholder values like ${{ secrets.KEYSTORE_PASS }} with real passwords
- Sets environment variables for the F-Droid server tools

# Why it's needed:
- The main config.yml has placeholder values for security
- F-Droid server tools need actual passwords to sign the repository
- Temporary config allows secure processing during workflow execution

# Code example:
cat > fdroid/config_secure.yml << EOF
repo_url: "https://fury.untamedfury.space/repo"
repo_name: "Fury's F-Droid Repo"
# ... other config with actual passwords
keystorepass: $KEYSTORE_PASS
keypass: $KEY_PASS
EOF
```

## Step 4: Python Script Execution
```python
# What happens:
1. Script reads apps.yaml to get list of apps to process
2. For each app, it performs these operations:
   - Fetches repository details from GitHub API
   - Downloads app icon to fdroid/metadata/icons/
   - Gets latest release info from GitHub Releases
   - Selects best APK (arm64-v8a, universal, etc.)
   - Downloads APK to local repo directory
   - Creates metadata file in fdroid/metadata/{app_id}.yml

# Log evidence of failure:
FileNotFoundError: [Errno 2] No such file or directory: 
'/home/runner/work/fury-fdroid/fury-fdroid/fdroid/repo/apks/net.kdt.pojavlaunch.debug/net.kdt.pojavlaunch.debug_1.apk'

# The specific failure point:
shutil.copy2(app_specific_apk_path, main_repo_apk_path)  # ← Variable name error
# Error: 'app_specific_apk_path' and 'main_repo_apk_path' not defined in scope

# Why it fails:
- Variable name mismatch in the Python script
- Tries to copy APKs between directories using undefined variables
- Script crashes before completing repository processing
```

## Step 5: F-Droid Update (Never reached due to Step 4 failure)
```bash
# What should happen:
- Run 'fdroid update' command to generate repository index files
- Creates index-v1.json, index-v2.json, index-v1.jar, etc.
- Scans APKs and metadata to create proper F-Droid repository structure

# Command example:
fdroid update --verbose

# Why it's needed:
- Generates the index files that F-Droid clients use to discover apps
- Signs the repository with the keystore
- Creates proper repository structure for F-Droid compatibility
```

## Steps 6-7: Prepare Website & Deploy (Never reached due to Step 4 failure)
```bash
# What should happen:
1. Copy all repository files to public/ directory:
   - Repository index files (index-v1.json, index-v2.json, etc.)
   - APK files from fdroid/repo/
   - Metadata and icons
   - Website files

2. Deploy public/ directory to GitHub Pages:
   - Makes repository accessible at https://fury.untamedfury.space/repo
   - F-Droid clients can add this URL to access the repository

# Code example:
cp -r fdroid/repo/* public/repo/
cp -r website/* public/
# Deploy to GitHub Pages
```

## Current Status
- ✅ Steps 1-2: Working (Checkout and Setup)
- ❌ Step 3: Partially working (config is created but script fails)
- ❌ Step 4: **FAILING** (variable name error in Python script)
- ❌ Step 5: Never reached (due to Step 4 failure)
- ❌ Steps 6-7: Never reached (due to Step 4 failure)

## Root Cause
The Python script has a variable name error where it tries to use `app_specific_apk_path` and `main_repo_apk_path` that are not defined in the current scope, causing the workflow to fail before generating repository index files.