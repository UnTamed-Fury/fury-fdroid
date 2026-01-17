#!/usr/bin/env python3
import os, sys, json, yaml, logging, subprocess, shutil
from pathlib import Path

from fdroidserver import common

logging.basicConfig(level=logging.INFO, format="[%(levelname)s] %(message)s")

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
    # Skip individual APK signing - F-Droid will handle signing during the update process
    # Individual signing here can cause issues with F-Droid's repository signing
    logging.info(f"Skipping individual signing for {apk_path.name} - will be handled by F-Droid")
    return

def get_version(apk: Path):
    try:
        appid, versionCode, versionName = common.get_apk_id(str(apk))
        return int(versionCode)
    except Exception as e:
        logging.warning(f"Failed to parse {apk.name}: {e}")
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
    try:
        releases = json.loads(result)
        # Ensure releases is a list
        if not isinstance(releases, list):
            logging.warning(f"Expected a list of releases, but got {type(releases)}: {releases}")
            continue
    except json.JSONDecodeError:
        logging.error(f"Failed to decode JSON response for {repo}: {result}")
        continue

    # sort newest first by GitHub release ordering
    # For each release, select the BEST single APK based on architecture priority
    for r in releases:
        # Ensure r is a dictionary
        if not isinstance(r, dict):
            continue
        if r.get("prerelease") and not prerelease:
            continue
        if not r.get("prerelease") and prerelease:
            continue
        
        release_assets = []
        for a in r.get("assets", []):
            if isinstance(a, dict) and a.get("name", "").endswith(".apk"):
                release_assets.append(a)
        
        if not release_assets:
            continue

        # Logic: arm64 > universal > generic > skip x86/other
        best_asset = None
        best_score = -1

        for asset in release_assets:
            name = asset["name"].lower()
            
            # Exclude unwanted architectures
            if any(x in name for x in ["x86", "x64", "amd64", "desktop", "windows", "linux", "macos"]):
                continue
            
            score = 0
            if "arm64" in name or "aarch64" in name:
                score = 3
            elif "universal" in name or "all" in name:
                score = 2
            elif not any(x in name for x in ["arm", "7a", "eabi"]): # Generic/Clean name often means universal
                score = 1
            
            if score > best_score:
                best_score = score
                best_asset = asset
        
        if best_asset:
            url = best_asset["browser_download_url"]
            name = best_asset["name"]
            target = pkg_dir / name
            if not target.exists():
                logging.info(f"Downloading ({best_score}): {name}")
                subprocess.run(["curl", "-L", "-o", str(target), url], check=True)
                sign_apk(target)

    # Cleanup unwanted architectures from disk
    for f in pkg_dir.glob("*.apk"):
        name = f.name.lower()
        if any(x in name for x in ["x86", "x64", "amd64"]):
            logging.info(f"Removing unwanted arch: {f.name}")
            f.unlink()

    prune(package)

logging.info("Download + sign complete.")
