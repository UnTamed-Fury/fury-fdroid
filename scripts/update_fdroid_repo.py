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
            # Calculate version code from the latest_version string
            version_code = 1
            if '.' in latest_version:
                # Try to extract version code from version string
                try:
                    # Get the last numeric part of the version
                    parts = latest_version.replace('-alpha', '.').replace('-beta', '.').replace('-rc', '.').replace('+', '.').split('.')
                    for part in reversed(parts):
                        if part.isdigit():
                            version_code = int(part)
                            break
                except:
                    version_code = abs(hash(latest_version)) % 10000  # Fallback to hash-based version code

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

            # Create app-specific directory structure: /apks/{PKG_ID}/ for organized storage
            app_apk_dir = os.path.join(repo_dir, "apks", app_id)
            os.makedirs(app_apk_dir, exist_ok=True)

            # Generate proper F-Droid APK filename: {app_id}_{version_code}.apk
            # This ensures F-Droid clients can properly recognize and download the APKs
            latest_fdroid_apk_filename = f"{app_id}_{version_code}.apk"

            # Download APK to the app-specific directory for organized storage
            app_specific_apk_path = os.path.join(app_apk_dir, latest_fdroid_apk_filename)
            if apk_needs_processing:
                if not os.path.exists(app_specific_apk_path):
                    download_file(download_url, app_specific_apk_path)
                    print(f"  -> Downloaded APK to app-specific directory: {app_specific_apk_path}")
                else:
                    print(f"  -> APK already exists in app-specific directory: {app_specific_apk_path}")
            else:
                print(f"  -> Skipping download for latest version, already indexed for {app_id}")

            # For F-Droid server compatibility, also place APK in the main repo directory
            # F-Droid server tools expect APKs to be in the repo/ directory directly
            main_repo_apk_path = os.path.join(repo_dir, latest_fdroid_apk_filename)
            if apk_needs_processing or not os.path.exists(main_repo_apk_path):
                # Create a copy in the main repo directory for F-Droid server tools
                import shutil
                shutil.copy2(app_specific_apk_path, main_repo_apk_path)
                print(f"  -> Created copy for F-Droid server: {main_repo_apk_path}")
            else:
                print(f"  -> F-Droid server APK already exists: {main_repo_apk_path}")

            # Add the current latest version to builds
            all_builds.append({
                'versionName': latest_version,
                'versionCode': version_code,  # Use the calculated version code
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

                        # Create app-specific directory structure for this additional version
                        app_apk_dir = os.path.join(repo_dir, "apks", app_id)
                        os.makedirs(app_apk_dir, exist_ok=True)

                        # Generate proper F-Droid APK filename for this version
                        additional_fdroid_apk_filename = f"{app_id}_{additional_version_code}.apk"

                        # Download APK to the app-specific directory for organized storage
                        additional_app_specific_apk_path = os.path.join(app_apk_dir, additional_fdroid_apk_filename)
                        if not os.path.exists(additional_app_specific_apk_path):
                            download_file(additional_download_url, additional_app_specific_apk_path)
                            print(f"  -> Downloaded additional APK to app-specific directory: {additional_app_specific_apk_path}")
                        else:
                            print(f"  -> Additional APK already exists in app-specific directory: {additional_app_specific_apk_path}")

                        # For F-Droid server compatibility, also place APK in the main repo directory
                        additional_main_repo_apk_path = os.path.join(repo_dir, additional_fdroid_apk_filename)
                        if not os.path.exists(additional_main_repo_apk_path):
                            # Create a copy in the main repo directory for F-Droid server tools
                            import shutil
                            shutil.copy2(additional_app_specific_apk_path, additional_main_repo_apk_path)
                            print(f"  -> Created copy for F-Droid server: {additional_main_repo_apk_path}")
                        else:
                            print(f"  -> F-Droid server APK already exists: {additional_main_repo_apk_path}")

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

            # For standard F-Droid repositories, don't use Binaries field
            # The APK files are hosted locally in the repo directory
            # F-Droid server will automatically create the proper index referencing local APKs

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
    2. Old APKs that are no longer the latest versions (within retention limits)
    """
    import os
    import glob

    # Get all app directories in the apks directory
    apk_app_dirs = []
    apks_dir = os.path.join(repo_dir, "apks")
    if os.path.exists(apks_dir):
        apk_app_dirs = [d for d in os.listdir(apks_dir) if os.path.isdir(os.path.join(apks_dir, d))]

    for app_dir_name in apk_app_dirs:
        app_dir_path = os.path.join(apks_dir, app_dir_name)

        # Check if this app is still in the apps.yaml
        if app_dir_name not in current_app_ids:
            # This app has been removed from apps.yaml, remove all its APKs
            import shutil
            shutil.rmtree(app_dir_path)
            print(f"  -> Removed APK directory for app no longer in apps.yaml: {app_dir_name}")

            # Also remove the corresponding metadata file
            metadata_file = os.path.join(metadata_dir, f"{app_dir_name}.yml")
            if os.path.exists(metadata_file):
                os.remove(metadata_file)
                print(f"  -> Removed metadata file for app no longer in apps.yaml: {app_dir_name}")
        else:
            # App is still in apps.yaml, but check for version retention
            # Keep only the most recent APKs per retention rules
            apk_files = glob.glob(os.path.join(app_dir_path, "*.apk"))

            # Sort APK files by modification time (newest first)
            apk_files.sort(key=lambda x: os.path.getmtime(x), reverse=True)

            # Keep only the most recent APKs based on retention rules
            max_apks_to_keep = 4  # Maximum APKs per app

            # Remove excess APKs from both app-specific and main repo directories
            for i, apk_path in enumerate(apk_files):
                if i >= max_apks_to_keep:
                    try:
                        # Remove from app-specific directory
                        os.remove(apk_path)
                        print(f"  -> Removed excess APK from app directory: {os.path.basename(apk_path)}")

                        # Also remove from main repo directory if it exists there
                        main_apk_path = os.path.join(repo_dir, os.path.basename(apk_path))
                        if os.path.exists(main_apk_path):
                            os.remove(main_apk_path)
                            print(f"  -> Removed excess APK from main repo: {os.path.basename(apk_path)}")
                    except OSError as e:
                        print(f"  -> Could not remove excess APK {os.path.basename(apk_path)}: {e}")

    # Clean up APKs in the main repo directory that are not referenced in metadata
    # This ensures we only keep APKs that are actively referenced in the repository
    all_main_repo_apks = glob.glob(os.path.join(repo_dir, "*.apk"))
    for apk_path in all_main_repo_apks:
        apk_filename = os.path.basename(apk_path)

        # Skip repository index files and other repository files
        if any(skip_pattern in apk_filename for skip_pattern in ['index-', '.jar', '.json']):
            continue

        # Check if this APK is referenced in any metadata file
        apk_referenced = False
        for app_id in current_app_ids:
            metadata_path = os.path.join(metadata_dir, f"{app_id}.yml")
            if os.path.exists(metadata_path):
                try:
                    with open(metadata_path, 'r') as f:
                        import yaml
                        metadata = yaml.safe_load(f)

                    builds = metadata.get('Builds', [])
                    for build in builds:
                        apk_output = build.get('output', '')
                        if apk_output == apk_filename:
                            apk_referenced = True
                            break
                except Exception:
                    # If there's any error parsing the metadata file, continue
                    continue

        # If this APK is not referenced in any active metadata file, remove it
        if not apk_referenced:
            try:
                os.remove(apk_path)
                print(f"  -> Removed unreferenced APK from main repo: {apk_filename}")
            except OSError as e:
                print(f"  -> Could not remove unreferenced APK {apk_filename}: {e}")
        else:
            print(f"  -> Keeping APK: {apk_filename} (referenced in active metadata)")

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

        # First, read the metadata to ensure F-Droid server recognizes all apps
        print("Reading metadata with fdroid readmeta...")
        readmeta_result = subprocess.run(['fdroid', 'readmeta', '--verbose'], cwd=FDROID_DIR, env=env, capture_output=True, text=True)

        if readmeta_result.returncode != 0:
            print(f"Error reading metadata: Command failed with return code {readmeta_result.returncode}")
            print(f"STDOUT: {readmeta_result.stdout}")
            print(f"STDERR: {readmeta_result.stderr}")
            # Continue anyway as update might still work
        else:
            print("Metadata read successfully by F-Droid server.")

        # Now run fdroid update to generate the repository index
        print("Updating F-Droid repository index...")
        result = subprocess.run(['fdroid', 'update', '--verbose', '--create-metadata', '--delete-unknown', '--pretty'], cwd=FDROID_DIR, env=env, capture_output=True, text=True, timeout=120)  # 2-minute timeout with additional flags from template

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