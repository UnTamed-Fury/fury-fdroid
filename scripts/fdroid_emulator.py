#!/usr/bin/env python3
import subprocess, logging
from pathlib import Path

logging.basicConfig(level=logging.INFO, format="[%(levelname)s] %(message)s")

ROOT = Path(__file__).resolve().parents[1]
REPO = ROOT / "repo" / "index-v1.json"

if not REPO.exists():
    logging.error("index-v1.json missing. Run Phase 4 again.")
    raise SystemExit(1)

try:
    subprocess.run(["fdroid", "lint"], check=True)
    logging.info("Repo lint OK.")
except:
    logging.error("FDroid Lint failed.")
    raise SystemExit(1)