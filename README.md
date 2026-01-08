# Fury's F-Droid Repository

A F-Droid repository for open source Android apps I use and recommend.

[![F-Droid](https://img.shields.io/badge/F_Droid-1976D2?style=for-the-badge&logo=f-droid&logoColor=white)](https://f-droid.org/)
[![GitHub License](https://img.shields.io/github/license/UnTamed-Fury/fury-fdroid)](LICENSE)
[![Build Status](https://github.com/UnTamed-Fury/fury-fdroid/actions/workflows/build.yml/badge.svg)](https://github.com/UnTamed-Fury/fury-fdroid/actions/workflows/build.yml)

A high-performance, automated F-Droid repository hosting a curated collection of open-source Android apps. This repository is **stateless** and **fully automated**, fetching updates, metadata, and icons directly from GitHub Releases.

Website: [https://fury.untamedfury.space/](https://fury.untamedfury.space/)

## Installation

You can add this repository to any F-Droid compatible client (F-Droid, Neo Store, Droid-ify, etc.).

### QR Code
Scan the QR code below with your F-Droid client:

![QR Code](website/qr.png)

### Manual Configuration
- Repository URL: `https://fury.untamedfury.space/repo`
- Fingerprint (SHA-256): `D5:ED:79:60:17:1D:58:32:4A:D3:64:A0:90:0E:28:7A:51:F1:95:92:6C:B4:FB:AF:5E:BB:E7:E9:5A:81:DC:EF`

## Features

- Automated Updates: Checks for new releases every 6 hours via GitHub Actions
- Stateless Architecture: APKs are not stored in the git history, keeping the repository size small and builds fast
- Smart Metadata: Automatically fetches app descriptions and icons from upstream GitHub repositories
- Optimized Icons: Automatically converts and optimizes app icons for F-Droid compatibility
- Version Control: Maintains the latest 2 versions of each app to save bandwidth and storage

## Architecture

This project uses a unique "stateless" approach to F-Droid repositories:

1. Source of Truth: `apps.yaml` defines the list of apps and their metadata
2. Phase 1: Watcher: A scheduled workflow checks GitHub for new releases of tracked apps
3. Phase 2: Setup: Prepares the directory structure and fetches/updates icons
4. Phase 3: Download: Downloads APKs from GitHub Releases and passes them as artifacts (not committed to git)
5. Phase 4: Index: Uses `fdroidserver` to generate the repository index with APKs from artifacts
6. Phase 5: Deploy: Publishes the static website and repository to GitHub Pages

Key Point: APKs are NOT stored in the git repository. They are downloaded during the build process and used only for index generation, keeping the repository lightweight.

For detailed technical information about the architecture, see the [Architecture Documentation](docs/architecture.md).

## App Collection

This repository hosts a curated collection of open-source Android apps across multiple categories including System utilities, Entertainment, Development tools, Communication apps, and Security tools.

For a complete list of apps and their categories, see the [App Collection Documentation](docs/apps.md) and [App Status Table](docs/app-status.md).

## Documentation

For detailed information about the repository, please see our [Documentation](docs/index.md):

- App Collection: Complete list of apps and categories
- Architecture: Technical details about how the repository works
- App Status: Current status of all apps in the repository

## Contributing

We welcome contributions! whether it's adding a new app or improving the build scripts.

- Add a New App: Use our [App Adder Script](docs/apps-add.md) to easily add new apps to the repository
- Report Issues: Open an issue if an app is outdated or broken

## License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## Security Notice

This repository uses a secure keystore for signing the F-Droid repository. The repository fingerprint uses 4096-bit RSA encryption for enhanced security.
