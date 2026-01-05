# Architecture

Fury's F-Droid Repository uses a unique "stateless" approach to F-Droid repositories that automates the process of maintaining an F-Droid repository.

## Workflow Phases

The repository is built using a 4-phase GitHub Actions workflow:

### Phase 1 - Watcher
- A scheduled workflow checks GitHub for new releases of tracked apps
- Runs automatically every 6 hours
- Updates the repository if new app versions are found

### Phase 2 - Setup
- Prepares the directory structure
- Fetches and updates app icons from upstream repositories
- Validates app metadata

### Phase 3 - Download
- Downloads APKs from GitHub Releases
- Passes APKs as artifacts (not committed to git)
- Maintains only the latest 2 versions of each app

### Phase 4 - Index
- Uses `fdroidserver` to generate the repository index (`index-v1.jar`)
- Creates the repository metadata
- Signs the repository with the proper certificate

### Phase 5 - Deploy
- Publishes the static website and repository to GitHub Pages
- Updates the live repository at fury.untamedfury.space

## Key Features

### Stateless Architecture
- APKs are NOT stored in the git history
- Keeps the repository size small and builds fast
- APKs are downloaded during the build process and used only for index generation

### Automated Updates
- Checks for new releases automatically
- Maintains up-to-date repository without manual intervention

### Smart Metadata
- Automatically fetches app descriptions and icons from upstream GitHub repositories
- Optimizes icons for F-Droid compatibility

## Repository Structure

```
fury-fdroid/
├── apps.yaml          # Source of truth for apps
├── apks/              # Downloaded APKs (not in git)
├── fdroid/            # F-Droid configuration
├── scripts/           # Automation scripts
├── website/           # Static website files
└── docs/              # Documentation
```

## Security

- Repository is signed with a 4096-bit RSA key
- SHA-256 fingerprint is provided for verification
- All APKs are verified during the build process