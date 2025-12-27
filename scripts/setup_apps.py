import os
import yaml
import requests
import sys
from io import BytesIO
from PIL import Image

def download_and_convert_icon(url, target_path):
    print(f"Downloading icon {url}...")
    try:
        response = requests.get(url, timeout=30)
        response.raise_for_status()
        img = Image.open(BytesIO(response.content))
        if img.mode in ('P', 'CMYK'):
            img = img.convert('RGBA')
        img.save(target_path, "PNG")
        print(f"  ✓ Saved to {target_path}")
    except Exception as e:
        print(f"  ✗ Failed: {e}")

def setup_apps():
    print("--- 🛠️ Setup Apps ---")
    
    if not os.path.exists('apps.yaml'):
        print("apps.yaml missing")
        return

    with open('apps.yaml', 'r') as f:
        data = yaml.safe_load(f)

    os.makedirs('apks', exist_ok=True)
    os.makedirs('fdroid/metadata/icons', exist_ok=True)

    for app in data.get('apps', []):
        app_id = app['id']
        
        # 1. Create APK directory
        apk_dir = os.path.join('apks', app_id)
        if not os.path.exists(apk_dir):
            os.makedirs(apk_dir)
            print(f"  + Created directory: {apk_dir}")

        # 2. Check/Download Icon
        icon_path = os.path.join('fdroid/metadata/icons', f"{app_id}.png")
        if not os.path.exists(icon_path):
            icon_config = app.get('assets', {}).get('icon', {})
            # Try config URL or GitHub avatar
            icon_url = None
            if icon_config.get('type') == 'github-repo':
                icon_url = icon_config.get('url')
            
            if not icon_url:
                # Try to guess from repo owner avatar
                repo_url = app.get('url')
                if repo_url and 'github.com' in repo_url:
                    owner = repo_url.replace('https://github.com/', '').split('/')[0]
                    icon_url = f"https://github.com/{owner}.png"

            if icon_url:
                download_and_convert_icon(icon_url, icon_path)
            else:
                print(f"  ⚠ No icon source found for {app_id}")

if __name__ == "__main__":
    setup_apps()
