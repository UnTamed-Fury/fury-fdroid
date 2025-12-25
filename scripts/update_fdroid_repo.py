import os
import json
import requests
import yaml
import subprocess
import traceback
import sys
from PIL import Image
from io import BytesIO

# --- GitHub API Helpers ---
def get_github_headers(github_token):
    headers = {
        'Accept': 'application/vnd.github.v3+json'
    }
    if github_token:
        headers['Authorization'] = f'token {github_token}'
    return headers

def get_github_repo_details(repo_url, github_token):
    """Fetches repo description and owner avatar."""
    try:
        owner, repo = repo_url.replace('https://github.com/', '').split('/')[:2]
        api_url = f"https://api.github.com/repos/{owner}/{repo}"
        
        response = requests.get(api_url, headers=get_github_headers(github_token))
        response.raise_for_status()
        data = response.json()
        
        return {
            'description': data.get('description'),
            'avatar_url': data.get('owner', {}).get('avatar_url')
        }
    except Exception as e:
        print(f"  -> Warning: Could not fetch repo details for {repo_url}: {e}")
        return None

def get_latest_github_release_info(repo_url, github_token, prefer_prerelease=False):
    owner, repo = repo_url.replace('https://github.com/', '').split('/')[:2]
    # Get all releases (including pre-releases) instead of just the latest
    api_url = f"https://api.github.com/repos/{owner}/{repo}/releases"

    response = requests.get(api_url, headers=get_github_headers(github_token))
    response.raise_for_status()
    releases_data = response.json()

    # Separate pre-releases and regular releases
    pre_releases = []
    regular_releases = []

    for release in releases_data:
        apk_assets = []
        for asset in release['assets']:
            if asset['name'].endswith('.apk'):
                apk_assets.append((asset['name'], asset['browser_download_url']))

        # Only consider releases that have APK assets
        if apk_assets:
            release_info = {
                'version': release['tag_name'],
                'is_prerelease': release.get('prerelease', False),
                'published_at': release.get('published_at', ''),
                'apk_assets': apk_assets
            }

            if release_info['is_prerelease']:
                pre_releases.append(release_info)
            else:
                regular_releases.append(release_info)

    if prefer_prerelease:
        # If prefer_prerelease is True, ONLY return pre-releases (no fallback to regular releases)
        if pre_releases:
            # Return the most recent pre-release (first in the list since GitHub API returns newest first)
            selected_release = pre_releases[0]
            return selected_release['version'], selected_release['apk_assets']
        else:
            # No pre-releases available, raise an exception instead of falling back
            raise Exception("No pre-releases with APK assets found")
    else:
        # If prefer_prerelease is False, ONLY return regular releases (no pre-releases)
        if regular_releases:
            # Return the most recent regular release
            selected_release = regular_releases[0]
            return selected_release['version'], selected_release['apk_assets']
        else:
            # No regular releases available, raise an exception
            raise Exception("No regular releases with APK assets found")

    # If no releases with APKs found, raise an exception
    raise Exception("No releases with APK assets found")

def download_file(url, target_path):
    print(f"Downloading {url} to {target_path}...")
    try:
        with requests.get(url, stream=True) as r:
            r.raise_for_status()
            with open(target_path, 'wb') as f:
                for chunk in r.iter_content(chunk_size=8192):
                    f.write(chunk)
        print("Download complete.")
    except Exception as e:
        print(f"  -> Error downloading {url}: {e}")

def download_and_convert_icon(url, target_path):
    """Downloads an image and converts it to PNG using Pillow."""
    print(f"Downloading icon {url}...")
    try:
        response = requests.get(url)
        response.raise_for_status()
        
        img = Image.open(BytesIO(response.content))
        
        # Convert to RGBA if necessary (to preserve transparency)
        if img.mode in ('P', 'CMYK'):
            img = img.convert('RGBA')
            
        img.save(target_path, "PNG")
        print(f"Icon saved and converted to PNG at {target_path}")
        return True
    except Exception as e:
        print(f"  -> Error processing icon {url}: {e}")
        traceback.print_exc() 
        return False

# --- App Processing and Metadata Generation ---
def generate_metadata_for_apps(app_list_file, metadata_dir, repo_dir, github_token):
    with open(app_list_file, 'r') as f:
        app_data = yaml.safe_load(f)

    apps_to_process = app_data.get('apps', [])

    if not os.path.exists(metadata_dir):
        os.makedirs(metadata_dir)
    if not os.path.exists(repo_dir):
        os.makedirs(repo_dir)

    # Create the repo directory structure even if we're not downloading APKs
    # This is required for the fdroid server to work properly
    os.makedirs(os.path.join(repo_dir, "archive"), exist_ok=True)

    for app in apps_to_process:
        try:
            app_id = app['id']
            app_name = app['name']
            print(f"Processing {app_name} ({app_id})...")

            # Extract fields based on the new structure
            # Support both old and new structures for backward compatibility
            app_url = app.get('url') or app.get('source', {}).get('url')

            # Handle new structure with nested fields
            if 'fdroid' in app:
                # New structure
                fdroid_config = app.get('fdroid', {})
                prefer_prerelease = fdroid_config.get('prefer_prerelease', False)
                categories = fdroid_config.get('categories', [])

                # Get author from either old location or new classification
                author = app.get('author', app.get('classification', {}).get('author', 'Unknown'))

                # Try to get a custom icon URL from assets section
                icon_config = app.get('assets', {}).get('icon', {})
                custom_icon_url = None
                if icon_config.get('type') == 'github-repo' and icon_config.get('url'):
                    custom_icon_url = icon_config['url']
            else:
                # Old structure compatibility
                prefer_prerelease = app.get('prefer_prerelease', False)
                categories = app.get('categories', [])
                author = app.get('author', 'Unknown')
                custom_icon_url = None

            # 1. Fetch Repository Details (Description & Icon)
            repo_details = get_github_repo_details(app_url, github_token)
            summary = app_name # Default summary
            icon_url = None

            if repo_details:
                if repo_details.get('description'):
                    summary = repo_details['description']
                    if summary:
                         summary = summary.replace('\n', ' ').strip()
                # Use custom icon if specified, otherwise use GitHub avatar
                icon_url = custom_icon_url or repo_details.get('avatar_url')

            # 2. Download and Convert Icon
            if icon_url:
                icon_filename = f"{app_id}.png"
                icon_path = os.path.join(metadata_dir, "icons", icon_filename)
                os.makedirs(os.path.join(metadata_dir, "icons"), exist_ok=True)
                download_and_convert_icon(icon_url, icon_path)

            # 3. Fetch latest release info
            try:
                latest_version, apk_assets = get_latest_github_release_info(app_url, github_token, prefer_prerelease)
            except Exception as e:
                print(f"  -> Skipping: {e}")
                continue

            if not apk_assets:
                print(f"  -> Skipping: No APK assets found for latest release.")
                continue

            # 4. Select Best APK
            def select_best_apk(apk_options):
                preferred_order = ['arm64-v8a', 'universal', 'armeabi-v7a']
                best_apk = None
                best_rank = len(preferred_order)

                for apk_name, download_url_asset in apk_options:
                    apk_name_lower = apk_name.lower()
                    rank = len(preferred_order)

                    if 'arm64-v8a' in apk_name_lower:
                        rank = 0
                    elif 'universal' in apk_name_lower or ('arm' not in apk_name_lower and 'x86' not in apk_name_lower):
                        rank = 1
                    elif 'armeabi-v7a' in apk_name_lower:
                        rank = 2

                    if rank < best_rank:
                        best_rank = rank
                        best_apk = (apk_name, download_url_asset)

                if not best_apk and apk_options:
                    return apk_options[0]

                return best_apk

            apk_filename, download_url = select_best_apk(apk_assets)

            print(f"  -> Latest version: {latest_version}")
            print(f"  -> Selected APK: {apk_filename}")

            # 5. Download APK temporarily for F-Droid server processing
            # We need to download APKs for F-Droid server to process them, but they won't be hosted in repo
            target_apk_path = os.path.join(repo_dir, apk_filename)
            if not os.path.exists(target_apk_path):
                download_file(download_url, target_apk_path)
                print(f"  -> Downloaded APK for F-Droid processing: {target_apk_path}")
            else:
                print(f"  -> APK already exists for processing: {target_apk_path}")

            # 6. Generate Metadata File
            metadata_path = os.path.join(metadata_dir, f"{app_id}.yml")
            print(f"  -> Creating metadata file at {metadata_path}")

            category = categories[0] if categories else 'Other'

            # Construct proper F-Droid metadata format for remote APK references
            metadata = {
                'Categories': [category],
                'AuthorName': author,
                'Name': app['name'],
                'Summary': summary,
                'Description': summary,
                'SourceCode': app_url,
                'WebSite': app_url,
                'IssueTracker': f"{app_url}/issues" if app_url else '',
                'Changelog': f"{app_url}/releases",
                'License': 'Unknown',

                # For remote APK references
                'Binaries': download_url,  # Direct URL to the APK

                # Auto-update settings
                'AutoUpdateMode': 'Version %v',
                'UpdateCheckMode': 'Tags',

                # Builds section - minimal for remote APKs
                'Builds': [{
                    'versionName': latest_version,
                    'versionCode': 1,
                    'commit': latest_version,
                    'output': apk_filename,
                }]
            }

            # Use yaml.dump to safely write the file
            with open(metadata_path, 'w') as f_meta:
                yaml.dump(metadata, f_meta, default_flow_style=False, allow_unicode=True)

        except Exception as e:
            print(f"  -> ERROR processing {app.get('name', 'Unknown app')}: {e}")
            traceback.print_exc()
            continue

# --- Git Operations ---
def git_commit_and_push(commit_message, files_to_add):
    print(f"Attempting to commit and push changes: {commit_message}")
    subprocess.run(['git', 'config', '--local', 'user.email', 'action@github.com'], check=True)
    subprocess.run(['git', 'config', '--local', 'user.name', 'GitHub Action'], check=True)
    
    add_command = ['git', 'add'] + files_to_add
    subprocess.run(add_command, check=True)
    
    # Check if there are any changes to commit
    result = subprocess.run(['git', 'diff', '--cached', '--exit-code'], capture_output=True)
    if result.returncode == 0:
        print("No changes to commit.")
    else:
        subprocess.run(['git', 'commit', '-m', commit_message], check=True)
        subprocess.run(['git', 'push'], check=True)
        print("Changes committed and pushed successfully.")

# --- Main Execution ---
if __name__ == '__main__':
    # Debug: Check environment
    print("Python version:", sys.version)
    print("Installed packages:")
    subprocess.run(['pip', 'list'])

    APPS_LIST_FILE = 'apps.yaml'
    FDROID_DIR = 'fdroid'
    METADATA_DIR = os.path.join(FDROID_DIR, 'metadata')
    REPO_DIR = os.path.join(FDROID_DIR, 'repo')
    GITHUB_TOKEN = os.getenv('GH_TOKEN')

    if not GITHUB_TOKEN:
        print("Error: GH_TOKEN environment variable not set. Cannot proceed with GitHub API calls.")
        exit(1)

    # 1. Generate/Update App Metadata & Download APKs
    print("\n--- Generating Metadata and Downloading APKs ---")
    generate_metadata_for_apps(APPS_LIST_FILE, METADATA_DIR, REPO_DIR, GITHUB_TOKEN)
    print("Metadata generation and APK download complete.")

    # 2. Update F-Droid Repository Index
    print("\n--- Updating F-Droid Repository Index ---")

    # Temporarily update the config file with secrets from environment variables
    config_path = os.path.join(FDROID_DIR, 'config.yml')
    backup_config = None

    # Read the current config file
    with open(config_path, 'r') as f:
        config_content = f.read()

    # Store backup
    backup_config = config_content

    # Replace placeholder values with actual secrets from environment
    import os
    keystore_pass = os.environ.get('KEYSTORE_PASS', '')
    key_pass = os.environ.get('KEY_PASS', '')

    if keystore_pass and key_pass:
        # Replace the placeholder values with actual secrets
        secure_config_content = config_content.replace(
            'keystorepass: ${{ secrets.KEYSTORE_PASS }}',
            f'keystorepass: {keystore_pass}'
        ).replace(
            'keypass: ${{ secrets.KEY_PASS }}',
            f'keypass: {key_pass}'
        )

        # Write the secure config temporarily
        with open(config_path, 'w') as f:
            f.write(secure_config_content)

    try:
        # Set environment variables for fdroid command
        env = os.environ.copy()
        env['FDROID_KEY_STORE_PASS'] = keystore_pass
        env['FDROID_KEY_PASS'] = key_pass

        # Run fdroid update from inside the fdroid directory
        # We use --verbose to see what happens.
        subprocess.run(['fdroid', 'update', '--verbose'], cwd=FDROID_DIR, check=True, env=env)
        print("F-Droid repository index updated successfully.")
    except subprocess.CalledProcessError as e:
        print(f"Error updating F-Droid repository index: {e}")
        # Restore original config before exiting
        if backup_config:
            with open(config_path, 'w') as f:
                f.write(backup_config)
        exit(1)
    finally:
        # Always restore the original config file with placeholders
        if backup_config:
            with open(config_path, 'w') as f:
                f.write(backup_config)
            print("Secure config restored to placeholder values.")

    # 3. Commit and Push ONLY Metadata
    print("\n--- Committing Metadata Changes ---")
    files_to_add = [METADATA_DIR]
    git_commit_and_push("Automated: Update app metadata", files_to_add)

    print("\n--- All operations complete ---")