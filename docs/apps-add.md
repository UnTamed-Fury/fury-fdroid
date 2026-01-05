# Adding Apps to Fury's F-Droid Repository

This guide explains how to add new apps to the Fury's F-Droid repository using the `apps-add.py` script.

## Prerequisites

- Python 3 installed on your system
- `pyyaml` package installed (`pip install pyyaml`)
- `requests` package installed (`pip install requests`)

## Using the apps-add.py Script

### 1. Clone the Repository

```bash
git clone https://github.com/UnTamed-Fury/fury-fdroid.git
cd fury-fdroid
```

### 2. Install Dependencies

```bash
pip install pyyaml requests
```

### 3. Run the Script

```bash
python3 scripts/apps-add.py .
```

The script will interactively ask you for the following information:

- **App name**: The display name of the app
- **Package ID**: The Android package identifier (e.g., `com.example.app`)
- **GitHub URL**: The URL to the app's GitHub repository
- **Icon URL**: The URL to the app's icon (can be a GitHub raw URL or project root path)
- **Category**: Select from predefined categories (System, Entertainment, Development, etc.)
- **Status**: Select the app's development status (Stable, Alpha, Beta, etc.)
- **Content type**: Optional - specify content type (e.g., Manga, Anime, Music)
- **Prefer prerelease**: Whether to prefer prerelease versions
- **Archive old versions**: Whether to archive old versions of the app

### 4. Example Usage

```
$ python3 scripts/apps-add.py .
App Adder for Fury's F-Droid Repository
========================================
App name: Example App
Package ID: com.example.app
GitHub URL: https://github.com/example/example-app
Icon URL (project-root/icon-path or GitHub raw URL): https://raw.githubusercontent.com/example/example-app/main/app/src/main/res/mipmap-xxxhdpi/ic_launcher.png

Select app category:
1. System
2. Entertainment
3. Development
4. Communication
5. Security
6. Gaming
7. Misc
Enter category number (1-7): 3

Select app status:
1. Stable
2. Alpha
3. Beta
4. Nightly
5. Discontinued
6. Maintained Fork
7. Active
Enter status number (1-7): 1
Content type (e.g., Manga, Anime, Music, Video, etc. - press Enter to skip): 
Prefer prerelease versions? (y/n): n
Archive old versions? (y/n): n

Checking data in directory: .
App entry created successfully!
Added to apps.yaml: Example App (com.example.app)
```

## Making a Pull Request

After adding your app to the `apps.yaml` file, you can submit it via a pull request:

### Option 1: Using GitHub Website

1. **Commit your changes**:
   ```bash
   git add apps.yaml
   git commit -m "Add Example App to repository"
   ```

2. **Push your changes**:
   ```bash
   git push origin main
   ```
   (Note: If this is your first time, you might need to fork the repository first)

3. **Go to the repository on GitHub**: https://github.com/UnTamed-Fury/fury-fdroid

4. **Create a pull request**:
   - If you pushed to a branch, GitHub will show a "Compare & pull request" button
   - If not, click "Pull requests" → "New pull request"
   - Select your branch and create the pull request

### Option 2: Using Git Command Line

1. **Fork the repository** on GitHub (click the "Fork" button)

2. **Add your fork as a remote**:
   ```bash
   git remote add fork https://github.com/YOUR-USERNAME/fury-fdroid.git
   ```

3. **Create a new branch**:
   ```bash
   git checkout -b add-example-app
   ```

4. **Commit and push your changes**:
   ```bash
   git add apps.yaml
   git commit -m "Add Example App to repository"
   git push fork add-example-app
   ```

5. **Go to GitHub and create a pull request** from your branch

## Requirements for Apps

- The app must be open source
- The app must be available on GitHub
- The app should not contain proprietary components that violate F-Droid inclusion policy
- The app should have a proper license
- The icon URL should point to a valid image file

## Manual Editing (Alternative)

If you prefer to manually edit `apps.yaml`, here's the format:

```yaml
- id: com.example.app
  name: Example App
  author: example
  url: https://github.com/example/example-app
  classification:
    domain: Development
    type: Development
    status: Stable
  assets:
    icon:
      type: github-repo
      url: https://raw.githubusercontent.com/example/example-app/main/app/src/main/res/mipmap-xxxhdpi/ic_launcher.png
  fdroid:
    categories:
    - Development
```

## Need Help?

If you encounter any issues with the script or have questions about adding apps, please open an issue in the repository or check the [Contributing Guide](../CONTRIBUTING.md).