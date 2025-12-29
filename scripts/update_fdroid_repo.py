#!/usr/bin/env python3
import os, sys, json, yaml, logging, subprocess, shutil
from pathlib import Path

# Try different import methods for androguard
try:
    from androguard.core.bytecodes.apk import APK
except ImportError:
    try:
        from androguard.core.apk import APK
    except ImportError:
        from androguard.apk import APK

logging.basicConfig(level=logging.INFO, format="[%(levelname)s] %(message)s")
logging.getLogger("androguard").setLevel(logging.ERROR)

ROOT = Path(__file__).resolve().parents[1]
APKS_DIR = ROOT / "apks"
APPS_FILE = ROOT / "apps.yaml"

# -----------------------------------------
# Load app list
# -----------------------------------------
if not APPS_FILE.exists():
    logging.error("apps.yaml missing. Cannot continue.")
    sys.exit(1)

with open(APPS_FILE, "r") as f:
    apps = yaml.safe_load(f)

if not isinstance(apps, dict) or 'apps' not in apps:
    logging.error("apps.yaml format invalid. Expected a dict with 'apps' key.")
    sys.exit(1)

# -----------------------------------------
# Helpers
# -----------------------------------------
def is_prerelease(tag: str) -> bool:
    tag = tag.lower()
    return any(x in tag for x in ["alpha", "beta", "rc", "pre", "preview", "nightly"])

def sign_apk(apk_path: Path):
    keystore = ROOT / "fdroid" / "keystore.p12"
    if not keystore.exists():
        logging.error("Signing failed: keystore.p12 not found.")
        sys.exit(1)

    cmd = [
        "fdroid", "sign",
        "--keystore", str(keystore),
        "--verbose", str(apk_path)
    ]
    subprocess.run(cmd, check=True)
    logging.info(f"Signed: {apk_path}")

def get_version(apk: Path):
    try:
        a = APK(str(apk))
        return int(a.get_androidversion_code())
    except:
        return -1  # invalid apk gets purged later

def prune(package: str):
    pkg_dir = APKS_DIR / package
    if not pkg_dir.exists():
        return

    apks = list(pkg_dir.glob("*.apk"))
    if not apks:
        return

    data = []
    for apk in apks:
        v = get_version(apk)
        label = "prerelease" if is_prerelease(apk.name) else "stable"
        data.append((apk, v, label))

    stable = sorted([x for x in data if x[2] == "stable"], key=lambda x: x[1], reverse=True)
    pre = sorted([x for x in data if x[2] == "prerelease"], key=lambda x: x[1], reverse=True)

    purge = stable[2:] + pre[2:]  # keep 2 of each
    for apk, v, label in purge:
        logging.info(f"Removing old {label}: {apk.name}")
        apk.unlink()

# -----------------------------------------
# Main — Download loop
# -----------------------------------------
for entry in apps['apps']:
    if "url" not in entry or "id" not in entry:
        logging.error(f"Invalid entry: {entry}")
        continue

    # Extract repo from URL
    repo_url = entry.get('url')
    if 'github.com/' in repo_url:
        parts = repo_url.split('github.com/')[1].split('/')
        if len(parts) >= 2:
            repo = f"{parts[0]}/{parts[1]}"
        else:
            logging.warning(f"Invalid repo URL: {repo_url}")
            continue
    else:
        logging.warning(f"Not a GitHub URL: {repo_url}")
        continue

    package = entry["id"]
    prerelease = entry.get("fdroid", {}).get("prefer_prerelease", False)

    pkg_dir = APKS_DIR / package
    pkg_dir.mkdir(parents=True, exist_ok=True)

    # fetch from releases
    api = f"https://api.github.com/repos/{repo}/releases"
    token = os.environ.get("GH_TOKEN", "")
    curl = ["curl", "-s"]
    if token: curl += ["-H", f"Authorization: token {token}"]
    curl.append(api)

    result = subprocess.check_output(curl).decode("utf-8")
    releases = json.loads(result)

    assets = []
    for r in releases:
        if r.get("prerelease") and not prerelease:
            continue
        if not r.get("prerelease") and prerelease:
            continue
        for a in r.get("assets", []):
            if a["name"].endswith(".apk"):
                assets.append(a)

    if not assets:
        logging.warning(f"No matching APKs found for {package}")
        continue

    # sort newest first by GitHub release ordering
    for asset in assets[:4]:  # safety bound
        url = asset["browser_download_url"]
        name = asset["name"]
        target = pkg_dir / name
        if target.exists():
            continue
        logging.info(f"Downloading: {name}")
        subprocess.run(["curl", "-L", "-o", str(target), url], check=True)
        sign_apk(target)

    prune(package)

logging.info("Download + sign + prune complete.")
