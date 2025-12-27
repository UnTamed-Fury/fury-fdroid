import os
import yaml
import requests
import sys
import hashlib
from io import BytesIO
from PIL import Image

def get_icon_hash(path):
    if not os.path.exists(path): return None
    with open(path, 'rb') as f:
        return hashlib.md5(f.read()).hexdigest()

def find_best_icon_url(base_url):
    # Try the configured URL first
    urls = [base_url]
    
    # Try alternatives based on Android project structure
    if 'mipmap-' in base_url or 'drawable-' in base_url:
        densities = ['xxxhdpi', 'xxhdpi', 'xhdpi', 'hdpi']
        base_dir = os.path.dirname(base_url) # .../res/mipmap-xxxhdpi
        filename = os.path.basename(base_url) # ic_launcher.png
        res_dir = os.path.dirname(base_dir)   # .../res
        
        # Try mipmap
        for d in densities:
            urls.append(f"{res_dir}/mipmap-{d}/{filename}")
        # Try drawable
        for d in densities:
            urls.append(f"{res_dir}/drawable-{d}/{filename}")
        urls.append(f"{res_dir}/drawable/{filename}")

    return urls

def setup_apps():
    print("--- 🛠️ Setup Apps & Icons ---")
    
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
            os.makedirs(apk_dir, exist_ok=True)
            print(f"  + Created directory: {apk_dir}")

        # 2. Check/Update Icon
        icon_path = os.path.join('fdroid/metadata/icons', f"{app_id}.png")
        
        icon_config = app.get('assets', {}).get('icon', {})
        base_url = icon_config.get('url') if icon_config.get('type') == 'github-repo' else None
        
        if not base_url:
             # Try guess
            repo_url = app.get('url')
            if repo_url and 'github.com' in repo_url:
                # This is a weak guess, usually better to specify in apps.yaml
                pass
        
        if base_url:
            urls_to_try = find_best_icon_url(base_url)
            success = False
            
            for url in urls_to_try:
                try:
                    resp = requests.get(url, timeout=10)
                    if resp.status_code == 200:
                        new_content = resp.content
                        new_hash = hashlib.md5(new_content).hexdigest()
                        old_hash = get_icon_hash(icon_path)
                        
                        if new_hash != old_hash:
                            img = Image.open(BytesIO(new_content))
                            if img.mode in ('P', 'CMYK'):
                                img = img.convert('RGBA')
                            img.save(icon_path, "PNG")
                            print(f"  ✓ Updated icon for {app_id}")
                        else:
                            # print(f"  . Icon unchanged for {app_id}")
                            pass
                        success = True
                        break
                except:
                    continue
            
            if not success:
                print(f"  ⚠ Failed to fetch icon for {app_id}")

if __name__ == "__main__":
    setup_apps()