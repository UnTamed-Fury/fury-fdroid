# F-Droid Repository Analysis & Troubleshooting

## Repository Overview
This repository is an automated F-Droid repository that fetches APKs from GitHub Releases and creates a F-Droid compatible repository.

## Current Workflow Status
- **Build CI**: Running but failing to populate apps in index
- **Index files**: Generated but showing 0 apps
- **APK files**: Being downloaded but not properly indexed

## GitHub Actions Workflow Breakdown

### Step 1: Checkout Repository
```bash
- Uses actions/checkout@v4 to get repository code
- Fetches depth of 0 to get full history
```

### Step 2: Setup Python Environment
```bash
- Sets up Python 3.12
- Uses pip caching to speed up dependency installation
- Installs dependencies from pip cache repository
```

### Step 3: Create Secure Config File
```python
# Creates temporary config with actual passwords from GitHub Secrets
cat > fdroid/config_secure.yml << EOF
repo_url: "https://fury.untamedfury.space/repo"
repo_name: "Fury's F-Droid Repo"
# ... other config with actual passwords
keystorepass: $KEYSTORE_PASS
keypass: $KEY_PASS
EOF

# Runs the update script with environment variables
export FDROID_KEY_STORE_PASS="$KEYSTORE_PASS"
export FDROID_KEY_PASS="$KEY_PASS"
python3 scripts/update_fdroid_repo.py
```

### Step 4: Python Script Execution (Where the issue occurs)
```python
# The script processes apps from apps.yaml and does the following:
1. Reads apps.yaml to get list of apps to process
2. For each app:
   - Fetches GitHub repository details
   - Downloads app icon to fdroid/metadata/icons/
   - Gets latest release info from GitHub Releases
   - Selects best APK (arm64-v8a, universal, etc.)
   - Downloads APK to fdroid/repo/ directory
   - Creates metadata file in fdroid/metadata/{app_id}.yml
3. Runs 'fdroid update' command to generate repository index
```

## Common Issues & Solutions

### Issue 1: Variable Name Mismatch
**Problem**: 
```python
# In the script, trying to use undefined variables
version_code = latest_version_code  # ❌ Variable not defined
```

**Solution**:
```python
# Calculate version code from the version string
version_code = 1
if '.' in latest_version:
    try:
        parts = latest_version.replace('-alpha', '.').replace('-beta', '.').replace('-rc', '.').replace('+', '.').split('.')
        for part in reversed(parts):
            if part.isdigit():
                version_code = int(part)
                break
    except:
        version_code = abs(hash(latest_version)) % 10000  # Fallback to hash-based version code
```

### Issue 2: GitHub API Authentication
**Problem**: 
- GitHub API calls failing with 401 Unauthorized errors
- Missing proper Authorization headers

**Solution**:
```python
def get_github_headers(github_token):
    headers = {
        'Accept': 'application/vnd.github.v3+json',
        'User-Agent': 'Fury-FDroid-Bot/1.0'  # GitHub API requires User-Agent
    }
    if github_token:
        headers['Authorization'] = f'token {github_token}'
    else:
        # Fallback to environment variables
        env_token = os.environ.get('GH_TOKEN') or os.environ.get('GITHUB_TOKEN')
        if env_token:
            headers['Authorization'] = f'token {env_token}'
    return headers
```

### Issue 3: F-Droid Server Configuration
**Problem**: 
- F-Droid server not properly recognizing apps
- Index files generated but with 0 apps

**Root Cause Analysis**:
The F-Droid server expects:
1. Metadata files in fdroid/metadata/ directory with correct format
2. APK files in fdroid/repo/ directory
3. Proper config.yml with keystore information
4. Correct directory structure and permissions

**Current Metadata Format**:
```yaml
Categories: [Other]
AuthorName: Unknown
Name: App Name
Summary: App summary
Description: App summary
SourceCode: https://github.com/user/repo
WebSite: https://github.com/user/repo
IssueTracker: https://github.com/user/repo/issues
Changelog: https://github.com/user/repo/releases
License: Unknown
AutoUpdateMode: Version %v
UpdateCheckMode: Tags
Builds:
  - versionName: v1.2.3
    versionCode: 3
    commit: v1.2.3
    output: app.id_3.apk
```

## F-Droid Index Generation Process

### What happens during 'fdroid update':
1. F-Droid server scans fdroid/metadata/ directory for .yml files
2. For each metadata file, it looks for corresponding APK in fdroid/repo/
3. It verifies APK signatures and extracts app information
4. It creates index-v1.json and index-v2.json with app data
5. It signs the repository with the keystore

### Expected Repository Structure:
```
fdroid/
├── config.yml
├── keystore.p12
├── metadata/
│   ├── app.id1.yml
│   ├── app.id2.yml
│   └── icons/
│       ├── app.id1.png
│       └── app.id2.png
└── repo/
    ├── app.id1_v1.apk
    ├── app.id2_v2.apk
    ├── index-v1.json
    ├── index-v2.json
    ├── index-v1.jar
    └── index-v2.jar
```

## The Core Problem Identified

Based on the test output:
```
✓ https://fury.untamedfury.space/repo/index-v1.json is accessible (Status: 200)
✓ https://fury.untamedfury.space/repo/index-v1.json contains valid JSON
✓ Repository info found: Fury's F-Droid Repo
✓ Found 0 apps in repository
```

The issue is that the index files are being generated but they contain 0 apps. This means:
1. ✅ The F-Droid server is running without errors
2. ✅ Index files are being created
3. ❌ Apps are not being recognized by the F-Droid server

## Potential Causes

### 1. Metadata Format Issues
The metadata files might not have the correct format that F-Droid server expects.

### 2. APK-Metadata Linking Problems
The APK files might not be properly linked to the metadata in the F-Droid server processing.

### 3. Version Code Calculation
Incorrect version code calculation might be causing F-Droid to not recognize the apps properly.

## Solution Strategy

### Immediate Fix:
1. Ensure metadata files have correct F-Droid format
2. Verify APK files are in correct location when 'fdroid update' runs
3. Make sure version codes are properly calculated and unique

### Long-term Solution:
1. Implement proper error checking in the script
2. Add validation for metadata format
3. Ensure compatibility with F-Droid server requirements

## F-Droid Client Compatibility Requirements

For F-Droid clients to work:
1. Repository must have valid index files (index-v1.json or index-v2.json)
2. Index files must contain app entries with proper metadata
3. APK files must be accessible at the URLs specified in the index
4. Repository must be properly signed with keystore
5. Fingerprint must match the keystore signature

## Current State Summary
- GitHub Actions workflow runs to completion (no more crashes)
- Repository index files are generated
- Index files show 0 apps instead of the expected ~40 apps
- This indicates a metadata processing issue with the F-Droid server tools
- The repository is not functional for F-Droid clients until this is fixed

## Next Steps for Resolution
1. Examine the actual generated index files to see what's missing
2. Verify the metadata format matches F-Droid server expectations
3. Ensure APK files are properly named and located for F-Droid processing
4. Check version code generation logic
5. Test with a minimal set of apps to isolate the issue