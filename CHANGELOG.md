# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

## [1.2.0] - 2025-12-25

### Added
- Smart APK management system with intelligent download logic
- Only download APKs that aren't already indexed with same version
- Automatic cleanup of APKs for apps removed from apps.yaml
- Version change detection to re-download only when needed
- Enhanced error handling throughout the script
- Size management to prevent exceeding GitHub Pages limits

### Changed
- Updated all repository URLs to use fury.untamedfury.space
- Refined metadata format for better F-Droid compatibility
- Improved workflow configuration for GitHub Actions
- Updated website content with correct URLs

### Fixed
- Fixed variable name inconsistencies in the main processing loop
- Resolved workflow artifact size issues with proper APK management
- Corrected F-Droid config parameters to match standard format
- Fixed potential None value issues in cleanup functions

## [1.1.0] - 2025-12-24

### Added
- Remote APK reference system implementation
- Automated app icon update workflow
- Proper F-Droid repository structure with metadata directory
- GitHub Actions workflows for automated updates

### Changed
- Migrated to new repository structure with apps in apps.yaml
- Updated all documentation files (README, CONTRIBUTING)
- Configured proper F-Droid server settings with 4096-bit RSA key

### Fixed
- Resolved Git conflict issues in workflow files
- Fixed YAML parsing errors in metadata generation
- Corrected icon download and conversion process

## [1.0.0] - 2025-12-24

### Added
- Initial repository setup with F-Droid configuration
- Basic app metadata generation system
- GitHub Pages integration
- Initial set of tracked applications