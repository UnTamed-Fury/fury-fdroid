# Fury's F-Droid Repository

![F Droid](https://img.shields.io/badge/F_Droid-1976D2?style=for-the-badge&logo=f-droid&logoColor=white)
![GitHub License](https://img.shields.io/github/license/UnTamed-Fury/fury-fdroid)

---

A high-performance, automated F-Droid repository hosting a curated collection of open-source Android apps. This repository is **stateless** and **fully automated**, fetching updates, metadata, and icons directly from GitHub Releases.

**🌐 Website:** [https://fury.untamedfury.space/](https://fury.untamedfury.space/)

---

## 📲 Installation

You can add this repository to any F-Droid compatible client (F-Droid, Neo Store, Droid-ify, etc.).

### Option 1: QR Code
Scan the QR code below with your F-Droid client:

<img src="website/qr.png" width="200" alt="Repository QR Code" />

### Option 2: Manual Configuration
*   **Repository URL:**
    ```text
    https://fury.untamedfury.space/repo
    ```
*   **Fingerprint (SHA-256):**
    ```text
    BD:3D:60:C7:D6:AA:34:20:42:78:62:9B:0F:BC:EC:E7:B6:80:2E:6B:C6:7C:5F:11:12:D2:60:D4:21:86:EE:E6
    ```

---

## ✨ Features

*   **Automated Updates:** Checks for new releases every 6 hours.
*   **Stateless Architecture:** APKs are not stored in the git history, keeping the repo lightweight.
*   **Smart Metadata:** Automatically fetches app descriptions and icons from the upstream GitHub repositories.
*   **Optimized Icons:** Automatically converts and optimizes app icons for F-Droid compatibility.

---

## 📦 App Collection

This repository hosts a variety of apps, including:

| Category | Apps |
| :--- | :--- |
| **System** | PojavLauncher, Obtainium, Neo Store, Widgets Pro |
| **Entertainment** | AnymeX, Mihon, CloudStream, Spotube, SimpMusic, Echo |
| **Development** | Termux (Monet, API, Float, Style, X11), NeoTerm, Visual Code Space |
| **Communication** | Signal, Mastodon, Element X |
| **Security** | Stratum (Authenticator) |

*(See `apps.yaml` for the full live list)*

---

## 🤝 Contributing

Want to add an app or improve the scripts? We welcome contributions!
Please read our [Contributing Guide](CONTRIBUTING.md) for details on how to add new apps to `apps.yaml`.

---

## 📄 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

---

## ⚠️ Security Notice

This repository uses a secure keystore for signing the F-Droid repository. The repository fingerprint has been updated to reflect the new security key with enhanced 4096-bit RSA encryption.

## 🚀 Repository Status

[![Build Status](https://github.com/UnTamed-Fury/fury-fdroid/actions/workflows/update-repo.yml/badge.svg)](https://github.com/UnTamed-Fury/fury-fdroid/actions/workflows/update-repo.yml)