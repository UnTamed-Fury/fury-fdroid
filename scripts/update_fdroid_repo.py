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
        'Accept': 'application/vnd.github.v3+json',
        'User-Agent': 'Fury-FDroid-Bot/1.0'
    }
    if github_token:
        headers['Authorization'] = f'token {github_token}'
    else:
        # If no token provided directly, try to get from environment
        env_token = os.environ.get('GH_TOKEN') or os.environ.get('GITHUB_TOKEN')
        if env_token:
            headers['Authorization'] = f'token {env_token}'
    return headers

def get_github_repo_details(repo_url, github_token):
    """Fetches repo description and owner avatar."""
    try:
        owner, repo = repo_url.replace('https://github.com/', '').split('/')[:2]
        api_url = f"https://api.github.com/repos/{owner}/{repo}"

        # Add timeout to prevent hanging requests
        response = requests.get(api_url, headers=get_github_headers(github_token), timeout=30)
        response.raise_for_status()
        data = response.json()

        return {
            'description': data.get('description'),
            'avatar_url': data.get('owner', {}).get('avatar_url')
        }
    except requests.exceptions.Timeout:
        print(f"  -> Warning: Timed out fetching repo details for {repo_url}")
        return None
    except Exception as e:
        print(f"  -> Warning: Could not fetch repo details for {repo_url}: {e}")
        return None

def get_all_github_releases_info(repo_url, github_token, prefer_prerelease=False):
    """
    Fetches ALL GitHub releases (not just latest) to enable downgrade capability.

    Returns a list of release_info dictionaries for all releases with APKs.
    """
    owner, repo = repo_url.replace('https://github.com/', '').split('/')[:2]
    # Get all releases (including pre-releases) from the repository
    api_url = f"https://api.github.com/repos/{owner}/{repo}/releases"

    # Add timeout to prevent hanging requests
    response = requests.get(api_url, headers=get_github_headers(github_token), timeout=30)
    response.raise_for_status()
    releases_data = response.json()

    all_releases_with_apks = []

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

            # Depending on the prefer_prerelease setting, add to appropriate list
            if prefer_prerelease and release_info['is_prerelease']:
                # If prefer_prerelease is True, only add pre-releases
                all_releases_with_apks.append(release_info)
            elif not prefer_prerelease and not release_info['is_prerelease']:
                # If prefer_prerelease is False, only add regular releases
                all_releases_with_apks.append(release_info)

    if all_releases_with_apks:
        # Return all releases with APKs, sorted by published date (newest first)
        # Sort by published_at timestamp if available, otherwise by tag name
        try:
            # Filter out empty published_at values before sorting
            valid_releases = [r for r in all_releases_with_apks if r['published_at']]
            other_releases = [r for r in all_releases_with_apks if not r['published_at']]
            valid_releases.sort(key=lambda x: x['published_at'], reverse=True)
            other_releases.sort(key=lambda x: x['version'], reverse=True)
            all_releases_with_apks = valid_releases + other_releases
        except Exception:
            # If published_at sorting fails, sort by version string
            all_releases_with_apks.sort(key=lambda x: x['version'], reverse=True)

        return all_releases_with_apks
    else:
        raise Exception("No releases with APK assets found")


def get_latest_github_release_info(repo_url, github_token, prefer_prerelease=False):
    owner, repo = repo_url.replace('https://github.com/', '').split('/')[:2]
    # Get all releases (including pre-releases) instead of just the latest
    api_url = f"https://api.github.com/repos/{owner}/{repo}/releases"

    # Add timeout to prevent hanging requests
    response = requests.get(api_url, headers=get_github_headers(github_token), timeout=30)
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
        # Add timeout to prevent hanging downloads
        with requests.get(url, stream=True, timeout=60) as r:
            r.raise_for_status()
            with open(target_path, 'wb') as f:
                for chunk in r.iter_content(chunk_size=8192):
                    f.write(chunk)
        print("Download complete.")
    except requests.exceptions.Timeout:
        print(f"  -> Error downloading {url}: Request timed out after 60 seconds")
        raise
    except Exception as e:
        print(f"  -> Error downloading {url}: {e}")
        raise

def download_and_convert_icon(url, target_path):
    """Downloads an image and converts it to PNG using Pillow."""
    print(f"Downloading icon {url}...")
    try:
        # Add timeout to prevent hanging icon downloads
        response = requests.get(url, timeout=30)
        response.raise_for_status()

        img = Image.open(BytesIO(response.content))

        # Convert to RGBA if necessary (to preserve transparency)
        if img.mode in ('P', 'CMYK'):
            img = img.convert('RGBA')

        img.save(target_path, "PNG")
        print(f"Icon saved and converted to PNG at {target_path}")
        return True
    except requests.exceptions.Timeout:
        print(f"  -> Error downloading icon {url}: Request timed out after 30 seconds")
        return False
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

    # Keep track of apps currently in apps.yaml to identify removals later
    current_app_ids = set()
    for app in apps_to_process:
        current_app_ids.add(app['id'])

    # Process each app
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

            # 3. Fetch latest release info with timeout protection
            try:
                latest_version, apk_assets = get_latest_github_release_info(app_url, github_token, prefer_prerelease)
            except Exception as e:
                print(f"  -> Skipping: {e}")
                continue

            if not apk_assets:
                print(f"  -> Skipping: No APK assets found for latest release.")
                continue

            # Add a small delay between processing apps to avoid rate limiting
            import time
            time.sleep(1)

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

            selected_apk_result = select_best_apk(apk_assets)
            if selected_apk_result is None:
                print(f"  -> Skipping: No suitable APK found in release assets")
                continue

            apk_filename, download_url = selected_apk_result

            print(f"  -> Latest version: {latest_version}")
            print(f"  -> Selected APK: {apk_filename}")

            # 5. Check if APK is already indexed with the same version
            metadata_path = os.path.join(metadata_dir, f"{app_id}.yml")
            apk_needs_processing = True

            if os.path.exists(metadata_path):
                # Check if this is the same APK version as previously indexed
                with open(metadata_path, 'r') as f:
                    try:
                        existing_metadata = yaml.safe_load(f)
                        existing_builds = existing_metadata.get('Builds', [])
                        if existing_builds:
                            existing_version = existing_builds[0].get('versionName', '') if existing_builds else ''
                            if existing_version == latest_version:
                                print(f"  -> APK for {app_id} version {latest_version} already indexed, skipping download")
                                apk_needs_processing = False
                            else:
                                print(f"  -> APK version changed from {existing_version} to {latest_version}, will re-download")
                    except yaml.YAMLError:
                        print(f"  -> Error parsing existing metadata for {app_id}, will re-download")

            # Generate proper F-Droid APK filename: package_versionCode.apk
            # This ensures F-Droid clients can properly recognize and download the APKs
            version_code = latest_version_code
            fdroid_apk_filename = f"{app_id}_{version_code}.apk"
            target_apk_path = os.path.join(repo_dir, fdroid_apk_filename)

            # Download APK with proper F-Droid naming if it's not already indexed with the same version
            if apk_needs_processing:
                if not os.path.exists(target_apk_path):
                    download_file(download_url, target_apk_path)
                    print(f"  -> Downloaded APK for F-Droid processing: {target_apk_path}")
                else:
                    print(f"  -> APK already exists for processing: {target_apk_path}")
            else:
                print(f"  -> Skipping download, APK already indexed for {app_id}")

            # Update the output filename in the metadata to use the F-Droid naming convention
            apk_filename = fdroid_apk_filename

            # 6. Generate Metadata File with downgrade capability
            print(f"  -> Creating metadata file at {metadata_path}")

            category = categories[0] if categories else 'Other'

            # Fetch additional versions for downgrade capability (up to 3 total versions)
            all_builds = []

            # Generate proper F-Droid APK filename for the latest version: {app_id}_{version_code}.apk
            # This ensures consistency with F-Droid server expectations
            latest_fdroid_apk_filename = f"{app_id}_{latest_version_code}.apk"

            # Download APK with proper F-Droid naming for the latest version
            latest_target_apk_path = os.path.join(repo_dir, latest_fdroid_apk_filename)
            if apk_needs_processing:
                if not os.path.exists(latest_target_apk_path):
                    download_file(download_url, latest_target_apk_path)
                    print(f"  -> Downloaded latest APK for F-Droid processing: {latest_target_apk_path}")
                else:
                    print(f"  -> Latest APK already exists for processing: {latest_target_apk_path}")
            else:
                print(f"  -> Skipping download for latest version, already indexed for {app_id}")

            # Add the current latest version to builds
            all_builds.append({
                'versionName': latest_version,
                'versionCode': latest_version_code,
                'commit': latest_version,
                'output': latest_fdroid_apk_filename,  # Use the F-Droid compatible filename
            })

            # Try to fetch additional recent versions for downgrade capability
            try:
                all_releases = get_all_github_releases_info(app_url, github_token, prefer_prerelease)

                # Add up to 2 more recent versions (in addition to the latest) for downgrade capability
                additional_versions_added = 0
                for release_info in all_releases[1:3]:  # Skip the first (latest) and take up to 2 more
                    if additional_versions_added >= 2:  # Only add up to 2 additional versions
                        break

                    # Select best APK for this additional version
                    additional_apk_result = select_best_apk(release_info['apk_assets'])
                    if additional_apk_result:
                        original_apk_filename, additional_download_url = additional_apk_result

                        # Calculate version code for this additional version
                        additional_version_code = 1
                        if '.' in release_info['version']:
                            try:
                                parts = release_info['version'].replace('-alpha', '.').replace('-beta', '.').replace('-rc', '.').replace('+', '.').split('.')
                                for part in reversed(parts):
                                    if part.isdigit():
                                        additional_version_code = int(part)
                                        break
                            except:
                                additional_version_code = abs(hash(release_info['version'])) % 10000  # Fallback to hash-based version code

                        # Generate proper F-Droid APK filename for this version
                        additional_fdroid_apk_filename = f"{app_id}_{additional_version_code}.apk"
                        additional_target_apk_path = os.path.join(repo_dir, additional_fdroid_apk_filename)

                        # Download APK with proper F-Droid naming for this additional version
                        # Only download if this version isn't already processed
                        # We'll use a simplified check here - if the target file doesn't exist, download it
                        if not os.path.exists(additional_target_apk_path):
                            download_file(additional_download_url, additional_target_apk_path)
                            print(f"  -> Downloaded additional APK for F-Droid processing: {additional_target_apk_path}")
                        else:
                            print(f"  -> Additional APK already exists for processing: {additional_target_apk_path}")

                        all_builds.append({
                            'versionName': release_info['version'],
                            'versionCode': additional_version_code,
                            'commit': release_info['version'],
                            'output': additional_fdroid_apk_filename,  # Use the F-Droid naming convention
                        })
                        additional_versions_added += 1

                        print(f"  -> Added version {release_info['version']} for downgrade capability")
            except Exception as e:
                print(f"  -> Warning: Could not fetch additional versions for downgrade capability: {e}")
                # Continue with just the latest version if additional versions can't be fetched

            print(f"  -> Including {len(all_builds)} versions in metadata for downgrade capability")

            # Construct proper F-Droid metadata format with multiple versions for downgrade capability
            # This format is compatible with F-Droid server and clients
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

                # Auto-update settings
                'AutoUpdateMode': 'Version %v',
                'UpdateCheckMode': 'Tags',

                # Builds section - include multiple versions for downgrade capability
                'Builds': all_builds,
            }

            # Add Binaries field pointing to the latest APK in the repo directory
            # This is required for F-Droid clients to know where to download the APK from
            if all_builds:
                latest_build = all_builds[0]  # First build is the latest
                latest_apk_filename = latest_build.get('output', '')
                if latest_apk_filename:
                    # The Binaries field should point to the APK file relative to the repo directory
                    metadata['Binaries'] = latest_apk_filename

            # Use yaml.dump to safely write the file
            with open(metadata_path, 'w') as f_meta:
                yaml.dump(metadata, f_meta, default_flow_style=False, allow_unicode=True)

        except Exception as e:
            print(f"  -> ERROR processing {app.get('name', 'Unknown app')}: {e}")
            traceback.print_exc()
            continue

    # After processing all apps, clean up APKs that are no longer needed
    print("\n--- Cleaning up APK files after processing ---")
    cleanup_old_apks(repo_dir, current_app_ids, metadata_dir)


def cleanup_old_apks(repo_dir, current_app_ids, metadata_dir):
    """
    Clean up APK files that are no longer needed:
    1. APKs for apps that have been removed from apps.yaml
    2. Old APKs that are no longer the latest version
    """
    import os
    import glob

    # Get all APK files in repo directory
    apk_files = glob.glob(os.path.join(repo_dir, "*.apk"))

    for apk_path in apk_files:
        apk_filename = os.path.basename(apk_path)

        # Check if this APK is for an app that's still in apps.yaml
        apk_belongs_to_active_app = False
        app_id_for_apk = None

        # Look for the app_id by checking which metadata file contains this APK
        for app_id in current_app_ids:
            metadata_path = os.path.join(metadata_dir, f"{app_id}.yml")
            if os.path.exists(metadata_path):
                try:
                    with open(metadata_path, 'r') as f:
                        metadata = yaml.safe_load(f)

                    builds = metadata.get('Builds', [])
                    if builds and len(builds) > 0:
                        apk_output = builds[0].get('output', '')
                        if apk_output == apk_filename:
                            # This APK matches the current metadata for this app
                            apk_belongs_to_active_app = True
                            app_id_for_apk = app_id
                            break
                except Exception:
                    # If there's any error parsing the metadata file, continue
                    continue

        # If this APK doesn't belong to any active app, it should be deleted
        if not apk_belongs_to_active_app:
            try:
                os.remove(apk_path)
                print(f"  -> Removed APK for inactive app: {apk_filename}")
            except OSError as e:
                print(f"  -> Could not remove {apk_filename}: {e}")
        else:
            # Use conditional to avoid potential error if app_id_for_apk is still None
            app_identifier = app_id_for_apk if app_id_for_apk else "unknown"
            print(f"  -> Keeping APK: {apk_filename} (belongs to active app {app_identifier})")

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

    # Define paths relative to the script location to ensure they work in all environments
    SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
    ROOT_DIR = os.path.dirname(SCRIPT_DIR)
    APPS_LIST_FILE = os.path.join(ROOT_DIR, 'apps.yaml')
    FDROID_DIR = os.path.join(ROOT_DIR, 'fdroid')
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

    # Check if config file exists before reading
    if not os.path.exists(config_path):
        print(f"Error: Config file does not exist at {config_path}")
        exit(1)

    print(f"Reading config file from: {config_path}")

    # Read the current config file
    with open(config_path, 'r') as f:
        config_content = f.read()

    print(f"Config file read successfully, length: {len(config_content)} characters")

    # Store backup
    backup_config = config_content

    # Replace placeholder values with actual secrets from environment
    # Try multiple possible environment variable names for compatibility
    import os
    keystore_pass = os.environ.get('FDROID_KEY_STORE_PASS') or os.environ.get('KEYSTORE_PASS', '')
    key_pass = os.environ.get('FDROID_KEY_PASS') or os.environ.get('KEY_PASS', '')

    print(f"Keystore password found: {'YES' if keystore_pass else 'NO'}")
    print(f"Key password found: {'YES' if key_pass else 'NO'}")

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
        print("Secure config file written with actual passwords")
    else:
        print("Warning: Keystore passwords not found in environment. Using placeholder values.")
        print(f"Available environment variables: {[k for k in os.environ.keys() if 'PASS' in k.upper() or 'KEY' in k.upper()]}")
        # Print all environment variables for debugging
        print(f"All environment variables: {list(os.environ.keys())}")

    try:
        # Set environment variables for fdroid command
        # F-Droid server expects specific environment variable names
        env = os.environ.copy()
        env['FDROID_KEY_STORE_PASS'] = keystore_pass
        env['FDROID_KEY_PASS'] = key_pass

        # Additionally, make sure GitHub token is available to subprocess
        if 'GH_TOKEN' in os.environ:
            env['GH_TOKEN'] = os.environ['GH_TOKEN']

        # Run fdroid update from inside the fdroid directory
        # Use the secure config file that has the actual passwords
        result = subprocess.run(['fdroid', 'update', '--verbose'], cwd=FDROID_DIR, env=env, capture_output=True, text=True, timeout=120)  # 2-minute timeout

        if result.returncode != 0:
            print(f"Error updating F-Droid repository index: Command failed with return code {result.returncode}")
            print(f"STDOUT: {result.stdout}")
            print(f"STDERR: {result.stderr}")
            # Restore original config before exiting
            if backup_config:
                with open(config_path, 'w') as f:
                    f.write(backup_config)
            exit(result.returncode)
        else:
            print("F-Droid repository index updated successfully.")
            if result.stdout:
                print(f"Command output: {result.stdout}")
    except subprocess.TimeoutExpired:
        print("Timeout occurred while running fdroid update command.")
        print("This might indicate an issue with the keystore or repository configuration.")
        # Restore original config before exiting
        if backup_config:
            with open(config_path, 'w') as f:
                f.write(backup_config)
        exit(1)
    except Exception as e:
        print(f"Error updating F-Droid repository index: {e}")
        import traceback
        traceback.print_exc()
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