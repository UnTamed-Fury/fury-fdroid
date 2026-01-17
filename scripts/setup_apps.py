#!/usr/bin/env python3
import yaml, sys, logging
from pathlib import Path

logging.basicConfig(level=logging.INFO, format="[%(levelname)s] %(message)s")

ROOT = Path(__file__).resolve().parents[1]
APPS = ROOT / "apps.yaml"
APKS = ROOT / "apks"
META = ROOT / "fdroid" / "metadata" / "icons"

if not APPS.exists():
    logging.error("apps.yaml missing. Phase 2 cannot continue.")
    sys.exit(1)

APKS.mkdir(parents=True, exist_ok=True)
META.mkdir(parents=True, exist_ok=True)
METADATA_DIR = ROOT / "fdroid" / "metadata"
METADATA_DIR.mkdir(parents=True, exist_ok=True)

with open(APPS, "r") as f:
    data = yaml.safe_load(f)

if not isinstance(data, dict) or 'apps' not in data:
    logging.error("apps.yaml format invalid. Expected a dict with 'apps' key.")
    sys.exit(1)

for app in data['apps']:
    if "id" not in app:
        logging.error(f"Invalid entry: {app}")
        continue

    pkg = app["id"]
    (APKS / pkg).mkdir(exist_ok=True)

    # Sync metadata
    name = app.get('name')
    if name:
        metadata_file = METADATA_DIR / f"{pkg}.yml"
        metadata = {}
        if metadata_file.exists():
            with open(metadata_file, 'r') as f:
                metadata = yaml.safe_load(f) or {}

        metadata['Name'] = name
        metadata['AuthorName'] = app.get('author', '')
        metadata['WebSite'] = app.get('url', '')
        metadata['SourceCode'] = app.get('url', '')

        categories = app.get('fdroid', {}).get('categories', [])
        if categories:
            metadata['Categories'] = categories

        with open(metadata_file, 'w') as f:
            yaml.dump(metadata, f, sort_keys=False, allow_unicode=True)

logging.info("Setup complete (Apps + Metadata synced).")