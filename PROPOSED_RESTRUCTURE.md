# Proposed Repository Restructuring Plan (Final Consolidated Version)

This document merges the original restructuring plan with all improved suggestions:
- `apks/` is the final destination for binaries
- `fdroid/repo` pulls from `apks/`
- Artifacts are minimal and temporary
- Only latest 2 releases are kept
- Workflow phases remain modular and automated

---

## 1. Target Repository Structure

.
├── apks/                                   # FINAL storage for signed binaries
│   └── [package.id]/
│       └── *.apk                           # Only latest 2 kept (auto-clean)
├── fdroid/                                 # F-Droid server environment
│   ├── archive/
│   ├── metadata/
│   │   ├── icons/
│   │   └── [package.id].yml
│   ├── repo/                               # Index reads from apks/ via symlink or copy
│   ├── config.yml
│   ├── icon.png
│   └── keystore.p12
├── scripts/
│   ├── update_fdroid_repo.py               # Core automation engine
│   └── fdroid_emulator.py                  # Unified testing/emulator tool
├── website/
│   ├── index.html
│   └── qr.png
├── apps.yaml                               # SOURCE OF TRUTH: app registry
├── release_status.json                     # Tracks last processed version per app
├── WORKFLOW_BREAKDOWN.md
├── README.md
└── LICENSE

---

## 2. Repository Intent and Separation of Concerns

| Area | Purpose |
|------|----------|
| `apks/` | Permanent signed binary store (single truth for APKs) |
| `fdroid/` | Index builder + config + signing environment |
| `scripts/` | Automation logic executed by workflows |
| `website/` | Deployment output / GitHub Pages frontend |
| `apps.yaml` | App definitions + preferences (`prefer_prerelease`, etc.) |
| `release_status.json` | Prevents duplicate downloads; version tracking |

---

## 3. Workflow Architecture (Phases)

### Phase 1: Watcher (Scheduled Checks)
- Runs every 6 hours
- Reads `apps.yaml` to locate upstream repos
- Compares latest tags to `release_status.json`
- Updates JSON and triggers fetch when a new release exists

### Phase 2: Setup (When apps.yaml changes)
- Creates initial folders for missing apps in `apks/`
- Fetches and converts icons into metadata/icons/
- Creates/updates metadata `.yml` files if missing

### Phase 3: Downloader (Fetch + Temporary Storage)
- Downloads latest APK to cache or artifact only when required
- Pre-release/stable decision based on `apps.yaml` keys:
  - `prefer_prerelease: true` → accept prerelease first
  - else stable priority

### Phase 4: Signer (Final Delivery to `apks/`)
- Signs APK → places inside `apks/<package.id>/`
- Enforces retention rule:
  - Keep latest 2 versions
  - Remove all older automatically

### Phase 5: Builder (Indexing & Symlink)
- F-Droid index fetches directly from `apks/`
- Recommended:
  ln -s apks fdroid/repo
- Fallback if symlink fails:
  cp apks/*/*.apk fdroid/repo/

### Phase 6: Publisher (Deployment)
- Builds new index.jar + index-v1.json
- Deploys repo + website to GitHub Pages

---

## 4. APK Retention and Cleanup Rules

- `apks/` is the master storage location
- Artifacts used only when caching is unavoidable
- Automatic cleanup every workflow run:
  - Keep 2 latest APKs maximum
  - All older APKs removed

Command principle applied:
  ls -t *.apk | sed -e '1,2d' | xargs -r rm

---

## 5. Benefits of the New System

- Eliminates APK duplication across artifacts
- Ensures deterministic update behavior
- Repo index always reads from the same source (`apks/`)
- Lower storage usage and maintenance
- Future expansion ready (delta updates, mirrors, CDN)

---