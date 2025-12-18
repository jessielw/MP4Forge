# macOS .app Bundle Support

## Overview

MP4Forge now supports proper macOS .app bundles for both Apple Silicon (ARM64) and Intel (x86_64) processors.

## What Changed

### 1. Build Script Enhancement
- Added `build_macos_app.py` - A dedicated script to convert PyInstaller output into proper macOS .app bundles
- Modified `build_desktop.py` to automatically create .app bundles on macOS after PyInstaller build

### 2. .app Bundle Structure
The created .app bundle follows the standard macOS application structure:
```
Mp4Forge.app/
├── Contents/
    ├── Info.plist          # Application metadata
    ├── MacOS/              # Executable and dependencies
    │   ├── Mp4Forge        # Main executable
    │   └── bundle/         # PyInstaller bundled resources
    └── Resources/
        └── AppIcon.icns    # Application icon
```

### 3. Icon Conversion
- Automatically converts PNG icons to ICNS format using macOS built-in tools (`sips` and `iconutil`)
- Generates all required icon sizes for normal and Retina displays

### 4. Dual Architecture Support
The GitHub Actions workflow now builds for both architectures:
- **ARM64** (Apple Silicon): Built on `macos-latest` (currently macOS 15)
- **Intel** (x86_64): Built on `macos-13`

## Installation for Users

### macOS ARM64 (Apple Silicon - M1, M2, M3, etc.)
1. Download `Mp4Forge-macOS-ARM64.zip` from releases
2. Extract the .zip file
3. Drag `Mp4Forge.app` to your Applications folder
4. Launch from Launchpad or Finder

### macOS Intel (x86_64)
1. Download `Mp4Forge-macOS-Intel.zip` from releases
2. Extract the .zip file
3. Drag `Mp4Forge.app` to your Applications folder
4. Launch from Launchpad or Finder

### First Launch Notes
On first launch, you may see a security warning because the app is not signed with an Apple Developer certificate. To bypass this:
1. Right-click (or Control-click) on `Mp4Forge.app`
2. Select "Open" from the context menu
3. Click "Open" in the security dialog
4. The app will launch and you won't see this warning again

## Building Locally

### Requirements
- macOS system
- Python 3.11 or 3.12
- uv package manager

### Build Commands
```bash
# Clone the repository
git clone https://github.com/jessielw/MP4Forge.git
cd MP4Forge

# Install dependencies
uv sync --all-extras

# Build the application (creates .app bundle automatically on macOS)
uv run python build_desktop.py

# The .app bundle will be at: pyinstaller_build/bundled_mode/Mp4Forge.app
```

## Technical Details

### Info.plist Configuration
- Bundle Identifier: `io.github.jessielw.mp4forge`
- Minimum macOS Version: 10.13 (High Sierra)
- High Resolution Capable: Yes
- Respects system appearance (Dark/Light mode)

### Why .app Bundles?
.app bundles provide several advantages:
1. **Standard macOS Experience**: Users can drag to Applications folder
2. **Better Integration**: Appears properly in Launchpad, Spotlight, and Dock
3. **Icon Support**: Proper icon display at all resolutions
4. **Metadata**: Contains version and app information accessible to the system
5. **Organization**: Keeps all app files contained in a single bundle

## GitHub Actions Workflow

The build workflow automatically:
1. Builds for both ARM64 and Intel architectures
2. Creates proper .app bundles with icons
3. Packages each as a .zip archive
4. Uploads artifacts for download
5. Creates release assets on tagged releases

## Future Enhancements

Potential improvements for the future:
- Code signing with Apple Developer certificate
- Notarization for Gatekeeper approval
- DMG disk image creation instead of zip archives
- Universal binary (fat binary) combining both architectures
