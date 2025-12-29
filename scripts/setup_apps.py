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

logging.info("Setup complete.")