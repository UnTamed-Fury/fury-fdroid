# Repository Setup Guide

This guide explains how to set up the F-Droid repository with all necessary configurations.

## GitHub Secrets Configuration

For the workflows to run properly, you need to set the following secrets in your GitHub repository:

1. `KEYSTORE_PASS`: `fdroid123`
2. `KEY_PASS`: `fdroid123`

To add these:
1. Go to your repository Settings
2. Click on Secrets and variables > Actions
3. Click "New repository secret"
4. Add each secret with the exact names and values above

## F-Droid Repository Configuration

The repository is configured to automatically fetch APKs from GitHub Releases and generate the F-Droid repository index.

### Smart APK Management System

The system now includes intelligent APK management:
- Only downloads APKs that aren't already indexed with the same version
- Automatically cleans up APKs for apps removed from apps.yaml
- Checks for version changes and re-downloads when needed
- Manages repository size by removing obsolete files