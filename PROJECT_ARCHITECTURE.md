# Fury's F-Droid Repository - Architecture Documentation

## Overview
This is a stateless, automated F-Droid repository that fetches updates, metadata, and icons directly from GitHub Releases. The repository is designed to be lightweight and efficient, with APKs not stored in git history.

## Architecture Flow

### Phase 1: Watcher
- **File**: `.github/workflows/phase1-watcher.yml`
- **Trigger**: Scheduled every 6 hours or manual dispatch
- **Purpose**: Acts as a trigger for the entire pipeline
- **Steps**: Simply triggers the next phase

### Phase 2: Setup
- **File**: `.github/workflows/phase2-setup.yml`
- **Trigger**: Runs after Phase 1 completes successfully
- **Purpose**: Sets up directory structure and prepares for APK downloads
- **Steps**:
  - Creates `apks/` directory structure for each app package
  - Creates `fdroid/metadata/icons` directory
  - Runs `scripts/setup_apps.py` to create package directories

### Phase 3: Download & Sign
- **File**: `.github/workflows/phase3-download.yml`
- **Trigger**: Runs after Phase 2 completes successfully
- **Purpose**: Downloads APKs from GitHub Releases and signs them
- **Steps**:
  - Installs Python dependencies
  - Runs `scripts/update_fdroid_repo.py` to download APKs from GitHub Releases
  - Commits and pushes new APKs to the repository
- **Issues**: Git push fails due to timeout/connection issues

### Phase 4: Index
- **File**: `.github/workflows/phase4-index.yml`
- **Trigger**: Runs after Phase 3 completes successfully
- **Purpose**: Generates F-Droid repository index files
- **Steps**:
  - Replaces `$KEYPASS` placeholder in `fdroid/config.yml` with actual key password
  - Runs `fdroid update --create-metadata` to generate repository files
  - Uploads repository artifacts
- **Issues**: The sed command doesn't properly replace variables, causing F-Droid to fail

### Phase 5: Deploy
- **File**: `.github/workflows/phase5-deploy.yml`
- **Trigger**: Runs after Phase 4 completes successfully
- **Purpose**: Deploys the repository to GitHub Pages
- **Steps**:
  - Downloads repository artifacts
  - Combines website and repository files
  - Deploys to GitHub Pages

## Scripts

### `scripts/setup_apps.py`
- Creates directory structure in `apks/` for each app package
- Creates directories based on app IDs from `apps.yaml`

### `scripts/update_fdroid_repo.py`
- Downloads APKs from GitHub Releases based on `apps.yaml`
- Handles both stable and pre-release versions
- Signs APKs using the keystore
- Prunes old APKs (keeps 2 latest versions of each type)
- Uses GitHub API with optional token for authentication

## Key Files

### `apps.yaml`
- Contains the list of apps to track
- Defines app metadata including GitHub URL, package ID, categories, etc.
- Used as the source of truth for which apps to include

### `fdroid/config.yml`
- F-Droid repository configuration
- Contains placeholders for passwords that should be replaced during CI

### `.gitignore`
- Currently ignores too many files needed for the F-Droid repo
- May be causing issues with APK files not being properly committed

## Issues Summary

### Phase 3 Issues:
1. Git push fails due to timeout/connection issues when committing many APK files
2. The repository becomes too large to handle efficiently with git

### Phase 4 Issues:
1. The sed command in the workflow doesn't properly replace the password placeholders
2. F-Droid server can't read the config due to missing key values

## Security Considerations
- Uses keystore.p12 for signing repository
- GitHub token required for API access to avoid rate limiting
- Passwords stored as GitHub secrets