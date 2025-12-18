"""
Script to create a proper macOS .app bundle from PyInstaller output.
This creates the standard macOS application structure with Info.plist.
"""

import os
import plistlib
import shutil
from pathlib import Path


def load_toml(file_path: Path) -> dict:
    """Load TOML file, handling different Python versions."""
    try:
        import tomllib
    except ImportError:
        import tomli as tomllib
    
    with open(file_path, "rb") as f:
        return tomllib.load(f)


def create_icns_from_png(png_path: Path, output_icns: Path) -> bool:
    """
    Convert PNG to ICNS format using sips (macOS built-in tool).
    Returns True if successful, False otherwise.
    """
    try:
        import platform
        import subprocess

        if platform.system() != "Darwin":
            print("Warning: ICNS conversion is only supported on macOS")
            return False

        # Create iconset directory
        iconset_dir = output_icns.parent / f"{output_icns.stem}.iconset"
        iconset_dir.mkdir(exist_ok=True)

        # Generate different sizes required for ICNS
        sizes = [16, 32, 64, 128, 256, 512, 1024]
        for size in sizes:
            output_file = iconset_dir / f"icon_{size}x{size}.png"
            subprocess.run(
                ["sips", "-z", str(size), str(size), str(png_path), "--out", str(output_file)],
                check=True,
                capture_output=True,
            )
            # Create @2x versions for retina displays (except for largest size)
            if size <= 512:
                retina_size = size * 2
                output_file_2x = iconset_dir / f"icon_{size}x{size}@2x.png"
                subprocess.run(
                    ["sips", "-z", str(retina_size), str(retina_size), str(png_path), "--out", str(output_file_2x)],
                    check=True,
                    capture_output=True,
                )

        # Convert iconset to icns
        subprocess.run(
            ["iconutil", "-c", "icns", str(iconset_dir), "-o", str(output_icns)],
            check=True,
            capture_output=True,
        )

        # Clean up iconset directory
        shutil.rmtree(iconset_dir)
        print(f"Created ICNS icon: {output_icns}")
        return True

    except Exception as e:
        print(f"Failed to create ICNS: {e}")
        return False


def create_info_plist(app_name: str, version: str, bundle_identifier: str) -> dict:
    """Create the Info.plist dictionary for the macOS app."""
    return {
        "CFBundleDevelopmentRegion": "en",
        "CFBundleDisplayName": app_name,
        "CFBundleExecutable": app_name,
        "CFBundleIconFile": "AppIcon.icns",
        "CFBundleIdentifier": bundle_identifier,
        "CFBundleInfoDictionaryVersion": "6.0",
        "CFBundleName": app_name,
        "CFBundlePackageType": "APPL",
        "CFBundleShortVersionString": version,
        "CFBundleVersion": version,
        "LSMinimumSystemVersion": "10.13",
        "NSHighResolutionCapable": True,
        "NSPrincipalClass": "NSApplication",
        "NSRequiresAquaSystemAppearance": False,
    }


def create_app_bundle(
    pyinstaller_output_dir: Path,
    app_name: str,
    version: str,
    bundle_identifier: str,
    icon_path: Path | None = None,
) -> Path:
    """
    Create a macOS .app bundle from PyInstaller output.

    Args:
        pyinstaller_output_dir: Path to PyInstaller's dist output directory
        app_name: Name of the application
        version: Version string
        bundle_identifier: Bundle identifier (e.g., com.example.app)
        icon_path: Path to PNG icon file (will be converted to ICNS)

    Returns:
        Path to the created .app bundle
    """
    # Define .app structure paths
    app_bundle = pyinstaller_output_dir.parent / f"{app_name}.app"
    contents_dir = app_bundle / "Contents"
    macos_dir = contents_dir / "MacOS"
    resources_dir = contents_dir / "Resources"

    # Clean up if it already exists
    if app_bundle.exists():
        shutil.rmtree(app_bundle)

    # Create directory structure
    macos_dir.mkdir(parents=True, exist_ok=True)
    resources_dir.mkdir(parents=True, exist_ok=True)

    print(f"Creating app bundle: {app_bundle}")

    # Move PyInstaller contents to MacOS directory
    # PyInstaller creates a folder with the app name containing the executable and resources
    pyinstaller_app_dir = pyinstaller_output_dir / app_name
    if pyinstaller_app_dir.exists():
        # Move everything from the PyInstaller output to MacOS
        for item in pyinstaller_app_dir.iterdir():
            dest = macos_dir / item.name
            if item.is_dir():
                shutil.copytree(item, dest)
            else:
                shutil.copy2(item, dest)
        print(f"Copied PyInstaller output to MacOS directory")
    else:
        raise FileNotFoundError(f"PyInstaller output not found: {pyinstaller_app_dir}")

    # Handle icon
    icns_path = resources_dir / "AppIcon.icns"
    if icon_path and icon_path.exists():
        if icon_path.suffix.lower() == ".png":
            create_icns_from_png(icon_path, icns_path)
        elif icon_path.suffix.lower() == ".icns":
            shutil.copy2(icon_path, icns_path)
        else:
            print(f"Warning: Unsupported icon format: {icon_path.suffix}")
    else:
        print("Warning: No icon provided")

    # Create Info.plist
    plist_data = create_info_plist(app_name, version, bundle_identifier)
    plist_path = contents_dir / "Info.plist"
    with open(plist_path, "wb") as f:
        plistlib.dump(plist_data, f)
    print(f"Created Info.plist")

    # Make the executable actually executable
    executable = macos_dir / app_name
    if executable.exists():
        os.chmod(executable, 0o755)
        print(f"Set executable permissions on {app_name}")

    print(f"Successfully created app bundle: {app_bundle}")
    return app_bundle


if __name__ == "__main__":
    import sys

    # For testing
    if len(sys.argv) > 1:
        pyinstaller_dir = Path(sys.argv[1])
    else:
        pyinstaller_dir = Path("pyinstaller_build/bundled_mode")

    if not pyinstaller_dir.exists():
        print(f"Error: PyInstaller output directory not found: {pyinstaller_dir}")
        sys.exit(1)

    # Get icon path
    project_root = Path(__file__).parent
    icon_path = project_root / "runtime" / "images" / "mp4.png"

    # Get version from pyproject.toml
    pyproject = load_toml(project_root / "pyproject.toml")
    version = pyproject["project"]["version"]

    app_bundle = create_app_bundle(
        pyinstaller_output_dir=pyinstaller_dir,
        app_name="Mp4Forge",
        version=version,
        bundle_identifier="io.github.jessielw.mp4forge",
        icon_path=icon_path if icon_path.exists() else None,
    )

    print(f"\n✅ App bundle created successfully at: {app_bundle}")
