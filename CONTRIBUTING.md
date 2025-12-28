# Contributing to Fury's F-Droid Repo

Thank you for your interest in contributing! This repository is fully automated, and most contributions will involve adding or updating apps in `apps.yaml`.

## ➕ Adding a New App

To add a new app, you need to edit the `apps.yaml` file.

### 1. Prerequisites
*   The app **must** be hosted on GitHub.
*   The app **must** use GitHub Releases to publish APKs.
*   The repository **must** be public.

### 2. YAML Structure
Add a new entry to the `apps` list in `apps.yaml`. Use the following template:

```yaml
- id: com.example.app.package.name  # MUST match the APK's package name exactly
  name: App Name
  author: Developer Name
  url: https://github.com/username/repo
  classification:
    domain: System          # Broad category (System, Entertainment, Development, etc.)
    type: Utility           # Specific type (Launcher, Player, Reader, etc.)
    content: Music          # Optional: Content type (Manga, Anime, Minecraft, etc.)
    status: Stable          # Stable, Alpha, Beta, Discontinued
  assets:
    icon:
      type: github-repo
      # URL to the raw icon file. Usually found in app/src/main/res/mipmap-xxxhdpi/ic_launcher.png
      url: https://raw.githubusercontent.com/username/repo/main/app/src/main/res/mipmap-xxxhdpi/ic_launcher.png
  fdroid:
    categories:             # Categories to show in F-Droid client
    - System
    - Utility
    prefer_prerelease: false # Set to true if you want to track Alpha/Beta releases
    archive: false          # Set to true if the app is discontinued/archived
```

### 3. Finding the Icon URL
1.  Navigate to the app's GitHub repository.
2.  Go to `app/src/main/res/`.
3.  Look for `mipmap-xxxhdpi` (preferred) or `mipmap-xxhdpi`.
4.  Find `ic_launcher.png`.
5.  Click on the file, then click the **Raw** button (or "Download raw file").
6.  Copy that URL.

### 4. Verification
Before submitting a Pull Request:
1.  Ensure the `id` matches the package name found in the APK (you can check this with tools like `aapt` or usually in the `AndroidManifest.xml` or `build.gradle` of the source).
2.  Ensure the `url` is correct.
3.  Check that the icon URL is accessible.

## 🛠️ Development & Maintenance

### Architecture
This repository uses a **stateless** architecture.
*   **APKs are NOT stored in git.** They are downloaded fresh during the CI build.
*   **Metadata** is generated from `apps.yaml` and injected into the F-Droid structure.
*   **Icons** are fetched and optimized during the Setup phase.

### Workflows
The automation is split into phases:
1.  **Watcher:** Checks for new GitHub releases periodically.
2.  **Setup & Icons:** Updates `apps.yaml` structure and fetches/caches icons.
3.  **Build:**
    *   **Download:** Fetches the latest APKs (up to 2 versions) from GitHub Releases.
    *   **Index:** Generates the F-Droid repository index (`index-v1.jar`).
    *   **Deploy:** Pushes the static site to GitHub Pages.

### Running Locally
To run the scripts locally, you need Python 3.12+ and the dependencies listed in `requirements.txt`.

```bash
pip install -r requirements.txt
```

#### Updating the Repo
```bash
# 1. Setup directories and icons
python3 scripts/setup_apps.py

# 2. Download APKs (Requires GH_TOKEN env var)
export GH_TOKEN="your_github_token"
python3 scripts/update_fdroid_repo.py --download

# 3. Index Repo (Requires 'fdroidserver' installed and on PATH)
# Note: You need a keystore to sign the repo.
python3 scripts/update_fdroid_repo.py --index
```
