# Contributing to Fury's F-Droid Repo

Thank you for your interest in contributing! This repository is fully automated, so "contributing" usually means adding a new app to the tracking list or improving the update scripts.

## ➕ How to Add a New App

To add a new application to this repository, you simply need to edit the `apps.yaml` file.

1.  **Fork** this repository.
2.  Open `apps.yaml`.
3.  Add a new entry to the `apps` list using the following format:

```yaml
  - id: com.example.package.id
    name: App Name
    author: AuthorName
    url: https://github.com/Username/RepoName
    categories: ["Category1", "Category2"]
```

### Requirements:
*   **ID:** Must be the exact Android Package ID (e.g., `com.whatsapp`, `org.telegram.messenger`). You can usually find this in the `AndroidManifest.xml` or `build.gradle` of the source repo.
*   **URL:** Must be a valid **GitHub** repository URL. The automation script currently only supports GitHub Releases.
*   **Repo:** The GitHub repository **must** have "Releases" with APK assets attached.

4.  **Submit a Pull Request**.
5.  Once merged, the GitHub Actions workflow will automatically run, fetch the metadata/icon, download the APK, and publish it.

## 🛠️ Improving the Scripts

The core logic resides in `scripts/update_fdroid_repo.py`.

*   **Language:** Python 3.12+
*   **Dependencies:** Listed in `requirements.txt`.
*   **Key Functions:**
    *   `generate_metadata_for_apps`: Orchestrates the fetching and generation.
    *   `download_and_convert_icon`: Handles image processing (Pillow).
    *   `fdroid update`: The official tool used to build the index.

If you modify the script, please ensure you test it locally or verify the Action logs after pushing.

## 🐞 Reporting Issues

If an app is failing to update or has a broken icon:
1.  Check the "Actions" tab to see if the latest run failed.
2.  Open an Issue with the name of the app and the error behavior.

Thank you for helping keep this repository awesome!

## 📋 Repository Structure

*   `apps.yaml` - List of apps to track and include in the repository
*   `fdroid/` - F-Droid repository configuration and generated files
*   `scripts/` - Update scripts for automating repository maintenance
*   `website/` - Static website files for repository information
*   `.github/workflows/` - GitHub Actions for automated updates