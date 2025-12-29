#!/usr/bin/env python3
import requests, yaml, logging
from pathlib import Path

logging.basicConfig(level=logging.INFO, format="[%(levelname)s] %(message)s")

ROOT = Path(__file__).resolve().parents[1]
APPS = ROOT / "apps.yaml"

with open(APPS, "r") as f:
    apps = yaml.safe_load(f)

for app in apps.get('apps', []):
    repo_url = app.get('url')
    app_id = app.get('id')
    if not repo_url or not app_id:
        logging.warning(f"Invalid entry: {app}")
        continue

    # Extract repo from URL
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

    url = f"https://api.github.com/repos/{repo}/releases/latest"
    r = requests.get(url)
    if r.status_code != 200:
        logging.warning(f"{app_id}: no latest release or invalid repo")
        continue

    tag = r.json().get("tag_name")
    logging.info(f"{app_id}: latest = {tag}")
