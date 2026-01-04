# Fury's F-Droid Repository - Codebase Documentation

## Project Structure
```
fury-fdroid/
├── apps.yaml                 # App definitions and metadata
├── requirements.txt          # Python dependencies
├── release_status.json       # Release status tracking
├── fdroid/                   # F-Droid configuration and metadata
│   └── config.yml            # F-Droid repository configuration
├── scripts/                  # Automation scripts
│   ├── check_updates.py      # Check for app updates
│   ├── fdroid_emulator.py    # F-Droid client emulator for testing
│   ├── setup_apps.py         # Setup app directories and metadata
│   └── update_fdroid_repo.py # Download APKs and update repo
├── website/                  # Nuxt.js website files
│   ├── nuxt.config.ts        # Nuxt configuration
│   ├── package.json          # Nuxt project dependencies
│   ├── pages/                # Website pages
│   ├── assets/               # CSS, images, etc.
│   └── public/               # Public assets
└── .github/workflows/        # GitHub Actions workflows
    ├── phase1-watcher.yml    # Phase 1: Schedule and trigger
    ├── phase2-setup.yml      # Phase 2: Setup directories
    ├── phase34-download-index.yml # Phases 3&4: Download APKs and index
    └── phase5-deploy.yml     # Phase 5: Deploy website and repo
```

## Core Components

### 1. apps.yaml
- **Purpose**: Defines the apps to be included in the repository
- **Format**: YAML with app metadata including GitHub URLs, package IDs, categories, etc.
- **Structure**:
  - `id`: Package name of the Android app
  - `name`: Display name
  - `author`: Developer name
  - `url`: GitHub repository URL
  - `classification`: Domain, type, content, and status categorization
  - `assets.icon`: Icon source information
  - `fdroid`: F-Droid specific settings (categories, pre-release preference, archiving)

### 2. scripts/update_fdroid_repo.py
- **Purpose**: Downloads APKs from GitHub releases and prepares F-Droid repository
- **Key Functions**:
  - Parses apps.yaml to get app information
  - Queries GitHub API for releases
  - Downloads APK files to local apks/ directory
  - Organizes APKs by package ID
  - Handles both stable and pre-release versions based on app settings

### 3. scripts/setup_apps.py
- **Purpose**: Creates directory structure based on apps.yaml
- **Function**: Creates package-specific directories in apks/ and fdroid/metadata/icons/

### 4. scripts/fdroid_emulator.py
- **Purpose**: Tests the F-Droid repository locally
- **Function**: Verifies that repository files exist locally (for development/testing)

### 5. scripts/check_updates.py
- **Purpose**: Checks for app updates without downloading
- **Function**: Compares current versions with GitHub releases

### 6. F-Droid Configuration (fdroid/config.yml)
- **Purpose**: Repository configuration for F-Droid server
- **Settings**:
  - Repository URL and name
  - Signing key configuration
  - Directory paths for repo, APKs, and metadata

## GitHub Actions Workflows

### Phase 1 - Watcher (.github/workflows/phase1-watcher.yml)
- **Trigger**: Scheduled (every 6 hours) via cron OR manual dispatch
- **Purpose**: Initiates the entire workflow process
- **Actions**:
  - Checks out repository
  - Simple echo command to trigger next phase
- **Output**: No artifacts, just triggers Phase 2

### Phase 2 - Setup (.github/workflows/phase2-setup.yml)
- **Trigger**: When Phase 1 completes successfully (workflow_run trigger)
- **Purpose**: Prepares directory structure and metadata
- **Actions**:
  - Checks out repository
  - Creates apks/ and fdroid/metadata/icons/ directories
  - Runs setup_apps.py to create package-specific directories based on apps.yaml
- **Output**: Sets up directory structure needed for Phase 3&4

### Phase 3 & 4 - Download & Index (.github/workflows/phase34-download-index.yml)
- **Trigger**: When Phase 2 completes successfully (workflow_run trigger)
- **Purpose**: Downloads APKs and creates F-Droid repository index (combined to avoid cross-workflow artifact issues)
- **Actions**:
  - Checks out repository
  - Sets up Python environment
  - Installs dependencies from requirements.txt
  - Runs update_fdroid_repo.py to download APKs from GitHub releases
  - Prepares repo directory with APKs (copies from apks/ to fdroid/repo/)
  - Injects secure config (replaces $KEYPASS placeholder with actual secrets)
  - Runs `fdroid update --create-metadata` to generate repository index
  - Copies icons to repo directory
  - Uploads repository as artifact named "fdroid-repo"
- **Output**: F-Droid repository files as "fdroid-repo" artifact

### Phase 5 - Deploy (.github/workflows/phase5-deploy.yml)
- **Trigger**: When Phase 3&4 completes successfully (workflow_run trigger) OR manual dispatch
- **Purpose**: Deploys website and repository to GitHub Pages
- **Actions**:
  - Checks out repository
  - Downloads "fdroid-repo" artifact from triggering Phase 3&4 run using custom action
  - Sets up Node.js environment
  - Installs Nuxt.js dependencies
  - Generates static Nuxt.js site
  - Creates deployment directory structure (combines website and repo)
  - Deploys to GitHub Pages using actions/deploy-pages
- **Output**: Live F-Droid repository and website at GitHub Pages URL

## Nuxt.js Website (website/)
- **Framework**: Nuxt 3 with static site generation
- **Features**:
  - Repository information and QR code
  - App browsing with search functionality
  - Repository statistics
  - Responsive design with dark theme
- **Pages**:
  - `/` - Main repository information
  - `/apps` - App browser with search
  - `/about` - Repository information

## Dependencies (requirements.txt)
- fdroidserver: Core F-Droid server tools
- requests: HTTP requests
- pyyaml: YAML parsing
- pillow: Image processing
- androguard: APK analysis
- gitpython: Git operations

## Statelessness Principle
The repository follows a "stateless" architecture:
- APKs are not stored in git history
- APKs are downloaded fresh during each build
- Repository index is regenerated from scratch each time
- Keeps repository size small and build times fast

## Current Issues & Planned Improvements

### Issues Identified
1. **Cross-workflow artifact sharing**: Phase 5 needs to download artifacts from Phase 3&4, which requires custom action
2. **Workflow naming**: Inconsistent naming between workflow display name and file name
3. **Deployment reliability**: Custom action for cross-workflow artifact download may be unreliable

### Planned Changes

#### 1. Workflow Architecture Optimization
- **Current**: Separate workflows with cross-workflow artifact sharing
- **Planned**: Maintain current combined Phase 3&4 approach (which solves artifact sharing within same workflow)
- **Benefit**: Eliminates cross-workflow artifact sharing issues between download and index phases

#### 2. Artifact Sharing Enhancement
- **Current**: Phase 5 uses custom action `dawidd6/action-download-artifact` to get artifacts from triggering workflow run
- **Issue**: Custom action may fail due to workflow name mismatch
- **Fix**: Use correct workflow filename in action parameters
- **Alternative**: Consider if we can make artifacts more reliably accessible

#### 3. Naming Consistency
- **Current**: Workflow names don't always match filenames
- **Planned**: Align workflow names with filenames for consistency
- **Example**: "Phase 3 & 4 - Download & Index" workflow should reference "phase34-download-index.yml" file

#### 4. Nuxt.js Website Enhancements
- **Current**: Basic Nuxt.js site with repository information
- **Planned**: Enhanced app browsing with real-time data from apps.yaml
- **Features**: Dynamic app listings, search, categories, and repository statistics

#### 5. Error Handling & Resilience
- **Current**: Basic error handling
- **Planned**: Improved error handling and retry mechanisms
- **Focus**: More resilient artifact downloads and deployment processes

#### 6. Performance Optimization
- **Current**: Downloads all APKs regardless of changes
- **Planned**: Implement change detection to only process updated apps
- **Benefit**: Faster workflow execution and reduced resource usage