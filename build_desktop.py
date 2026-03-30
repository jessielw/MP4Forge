import os
import platform
import plistlib
import shutil
import subprocess
from pathlib import Path
from subprocess import run

import tomllib


def get_executable_extension() -> str:
    return ".exe" if platform.system() == "Windows" else ""


def load_toml(file_path: Path) -> dict:
    """Load TOML file, handling different Python versions."""
    with open(file_path, "rb") as fh:
        return tomllib.load(fh)


def create_icns_from_png(png_path: Path, output_icns: Path) -> bool:
    """
    Convert PNG to ICNS format using sips (macOS built-in tool).
    Returns True if successful, False otherwise.
    """
    try:
        if platform.system() != "Darwin":
            print("Warning: ICNS conversion is only supported on macOS")
            return False

        iconset_dir = output_icns.parent / f"{output_icns.stem}.iconset"
        iconset_dir.mkdir(exist_ok=True)

        sizes = [16, 32, 64, 128, 256, 512, 1024]
        for size in sizes:
            output_file = iconset_dir / f"icon_{size}x{size}.png"
            subprocess.run(
                ["sips", "-z", str(size), str(size), str(png_path),
                 "--out", str(output_file)],
                check=True,
                capture_output=True,
            )
            if size <= 512:
                retina_size = size * 2
                output_file_2x = iconset_dir / f"icon_{size}x{size}@2x.png"
                subprocess.run(
                    ["sips", "-z", str(retina_size), str(retina_size),
                     str(png_path), "--out", str(output_file_2x)],
                    check=True,
                    capture_output=True,
                )

        subprocess.run(
            ["iconutil", "-c", "icns", str(iconset_dir), "-o", str(output_icns)],
            check=True,
            capture_output=True,
        )
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


def prepare_app_bundle(
    pyinstaller_bundle: Path,
    app_name: str,
    version: str,
    bundle_identifier: str,
    icon_path: Path | None = None,
) -> Path:
    """
    Use PyInstaller's own .app bundle as the base and layer on a proper
    icon and Info.plist. PyInstaller already produces the correct internal
    layout (MacOS/, Frameworks/, Resources/) — we must not restructure it
    or the Python runtime paths break.

    Args:
        pyinstaller_bundle: Path to PyInstaller's bundled_mode directory
        app_name: Name of the application
        version: Version string
        bundle_identifier: Bundle identifier (e.g., com.example.app)
        icon_path: Path to PNG icon file (will be converted to ICNS)

    Returns:
        Path to the prepared .app bundle
    """
    # PyInstaller's own .app is in bundled_mode/Mp4Forge.app
    src_bundle = pyinstaller_bundle / f"{app_name}.app"
    if not src_bundle.exists():
        raise FileNotFoundError(f"PyInstaller .app bundle not found: {src_bundle}")

    # copy it to the parent directory as our output bundle
    dest_bundle = pyinstaller_bundle.parent / f"{app_name}.app"
    if dest_bundle.exists():
        shutil.rmtree(dest_bundle)

    shutil.copytree(src_bundle, dest_bundle)
    print(f"Copied PyInstaller bundle to: {dest_bundle}")

    contents_dir = dest_bundle / "Contents"
    resources_dir = contents_dir / "Resources"
    resources_dir.mkdir(exist_ok=True)

    # replace icon
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

    # replace Info.plist with our version
    plist_data = create_info_plist(app_name, version, bundle_identifier)
    plist_path = contents_dir / "Info.plist"
    with open(plist_path, "wb") as fh:
        plistlib.dump(plist_data, fh)
    print(f"Updated Info.plist")

    # ensure executable bit is set
    executable = contents_dir / "MacOS" / app_name
    if executable.exists():
        os.chmod(executable, 0o755)
        print(f"Set executable permissions on {app_name}")

    print(f"Successfully prepared app bundle: {dest_bundle}")
    return dest_bundle


def clean_extended_attributes(app_bundle: Path) -> None:
    """
    Remove extended attributes from all files in the app bundle.
    Required on macOS 26 Tahoe (and Sequoia) where xattrs block codesign.
    """
    print("Cleaning extended attributes from app bundle...")
    for item in app_bundle.rglob("*"):
        try:
            subprocess.run(["xattr", "-c", str(item)], capture_output=True)
        except Exception:
            pass
    print("Extended attributes cleaned.")


def remove_codesign_blockers(app_bundle: Path) -> None:
    """
    Remove files and directories that codesign incorrectly treats as code
    objects on macOS 26 Tahoe and Sequoia, causing signing failures.

    macOS 26 codesign is stricter than previous versions and rejects any
    file with an unrecognized extension inside a bundle, even if it is
    plain text or empty. This function removes known problem directories
    explicitly, then sweeps both MacOS/ and Frameworks/ with a whitelist
    of extensions that codesign accepts or that are required at runtime.

    Contents/Resources is excluded — it only contains the .icns icon.
    """
    bundle_macos = app_bundle / "Contents" / "MacOS"
    bundle_frameworks = app_bundle / "Contents" / "Frameworks"

    # extensions codesign accepts or that are required at runtime
    SAFE_EXTENSIONS = {
        # binaries and libraries
        ".so", ".dylib",
        # python
        ".py", ".pyc", ".pyi",
        # data formats codesign accepts
        ".json", ".toml", ".xml", ".html", ".css", ".js",
        ".plist", ".cfg", ".conf", ".ini", ".txt", ".md",
        # qt resources
        ".qss", ".rcc",
        # iso639 language data
        ".tab",
        # font files — qtawesome .ttf fonts are kept and signed separately
        ".ttf", ".otf", ".woff", ".woff2",
        # archives pyinstaller needs
        ".pyz", ".zip",
        # no extension (executables)
        "",
    }

    # explicit directory blockers in both MacOS and Frameworks
    # note: qtawesome/fonts is intentionally excluded — font files are needed
    # at runtime and are handled separately (json charmaps removed, ttf kept)
    explicit_dir_blockers = [
        bundle_macos / "PySide6" / "Qt" / "translations",
        bundle_macos / "runtime" / "images",
        bundle_frameworks / "PySide6" / "Qt" / "translations",
        bundle_frameworks / "runtime" / "images",
    ]
    for blocker in explicit_dir_blockers:
        if blocker.exists():
            shutil.rmtree(blocker)
            print(f"Removed codesign blocker: {blocker.name}/")

    # explicit file blockers
    # note: only remove base_library.zip from MacOS, NOT Frameworks
    # PyInstaller bootloader requires it in Frameworks for encodings module
    explicit_file_blockers = [
        bundle_macos / "base_library.zip",
    ]
    for blocker in explicit_file_blockers:
        if blocker.exists():
            blocker.unlink()
            print(f"Removed codesign blocker: {blocker.name}")

    # whitelist sweep: remove unrecognized file types from MacOS and Frameworks
    # .dist-info directories are excluded from the sweep — their contents have
    # no standard extensions but are required at runtime by importlib.metadata
    removed_count = 0
    sweep_dirs = [d for d in [bundle_macos, bundle_frameworks] if d.exists()]
    for sweep_dir in sweep_dirs:
        for item in sweep_dir.rglob("*"):
            if not item.is_file():
                continue
            if not item.exists():
                continue
            # skip files inside .dist-info directories
            if any(p.suffix == ".dist-info" for p in item.parents):
                continue
            if item.suffix.lower() not in SAFE_EXTENSIONS:
                item.unlink()
                removed_count += 1

    # note: .dist-info directories are intentionally preserved
    # iso639 and other packages require their metadata at runtime via
    # importlib.metadata — removing them causes PackageNotFoundError on launch

    print(f"Whitelist sweep removed {removed_count} unrecognized file(s).")


def sign_app_bundle(app_bundle: Path) -> bool:
    """
    Apply ad-hoc code signatures to the app bundle for macOS 26 Tahoe
    and Apple Silicon compatibility.

    macOS requires all arm64 binaries to be signed. PyInstaller does not
    sign bundles automatically, causing an immediate 'killed' on launch.

    The Qt frameworks bundled by PyInstaller are malformed (missing proper
    framework structure) so codesign cannot sign them as framework bundles.
    Instead we sign the dylib inside each framework directly, which is
    handled by the dylib signing pass in step 1.

    Signing order matters:
      1. dylibs and .so files (including those inside .framework dirs)
      2. main executable
      3. outer .app bundle

    Returns True if signing succeeded, False otherwise.
    """
    print("Signing app bundle for macOS compatibility...")

    def codesign(path: Path) -> bool:
        result = subprocess.run(
            ["codesign", "--force", "--sign", "-", str(path)],
            capture_output=True,
            text=True,
        )
        if result.returncode != 0:
            print(f"  Warning: Failed to sign {path.name}: {result.stderr.strip()}")
            return False
        return True

    # step 0: handle base_library.zip for macOS 26 Tahoe codesign compatibility.
    # codesign rejects the zip because it contains unsigned .pyc bytecode files.
    # Solution: extract, sign each .pyc inside, repack, then use a codesign
    # exclusion rule via an entitlements approach — but since we are ad-hoc
    # signing, the simplest fix is to move base_library.zip to Resources/
    # (which codesign does not recursively validate for code objects) and
    # create a symlink in Frameworks/ so the bootloader still finds it.
    import zipfile
    for zip_candidate in [
        app_bundle / "Contents" / "Frameworks" / "base_library.zip",
        app_bundle / "Contents" / "MacOS" / "base_library.zip",
    ]:
        if zip_candidate.exists():
            print(f"  Moving {zip_candidate.name} out of codesign scan path...")
            resources_zip = app_bundle / "Contents" / "Resources" / "base_library.zip"
            shutil.copy2(zip_candidate, resources_zip)
            zip_candidate.unlink()
            # create symlink so bootloader path still resolves
            zip_candidate.symlink_to(resources_zip)
            print(f"  Moved to Resources/, symlinked from {zip_candidate.parent.name}/")

    # step 1: sign all dylibs
    print("  Signing dylibs...")
    for item in app_bundle.rglob("*.dylib"):
        codesign(item)

    # step 1b: sign all .pyc files — macOS 26 Tahoe treats compiled Python
    # bytecode as code objects that must be signed inside app bundles
    print("  Signing .pyc files...")
    for item in app_bundle.rglob("*.pyc"):
        codesign(item)

    # step 1c: sign all .tab files — macOS 26 Tahoe treats iso639 TSV data
    # files as code objects that must be signed inside app bundles
    print("  Signing .tab files...")
    for item in app_bundle.rglob("*.tab"):
        codesign(item)

    # step 1e: relocate qtawesome/fonts to Resources/ and symlink back.
    # codesign on macOS 26 rejects the json charmap files inside this directory
    # but qtawesome needs both the .ttf font files AND the .json charmap files
    # at runtime. Resources/ is not recursively validated by codesign.
    print("  Relocating qtawesome/fonts to Resources/...")
    resources_dir = app_bundle / "Contents" / "Resources"
    resources_dir.mkdir(exist_ok=True)
    for fonts_dir in list(app_bundle.rglob("qtawesome/fonts")):
        if fonts_dir.is_dir() and not fonts_dir.is_symlink():
            if resources_dir in fonts_dir.parents:
                continue
            dest = resources_dir / "qtawesome_fonts"
            if dest.exists():
                shutil.rmtree(dest)
            shutil.copytree(fonts_dir, dest)
            shutil.rmtree(fonts_dir)
            fonts_dir.symlink_to(dest)
            print(f"    Relocated: qtawesome/fonts -> Resources/qtawesome_fonts")

    # step 1d: move .dist-info directories to Resources/ and symlink back.
    # codesign on macOS 26 treats .dist-info directories as unrecognized bundle
    # formats and rejects the outer app. Resources/ is not recursively validated
    # for code objects so codesign ignores their contents there.
    # The symlinks allow importlib.metadata to still find them at runtime.
    print("  Relocating .dist-info directories to Resources/...")
    resources_dir = app_bundle / "Contents" / "Resources"
    resources_dir.mkdir(exist_ok=True)
    for item in list(app_bundle.rglob("*.dist-info")):
        if not item.is_dir() or item.is_symlink():
            continue
        # skip if already inside Resources/
        if resources_dir in item.parents:
            continue
        dest = resources_dir / item.name
        if dest.exists():
            shutil.rmtree(dest)
        shutil.copytree(item, dest)
        shutil.rmtree(item)
        item.symlink_to(dest)
        print(f"    Relocated: {item.name}")

    # step 2: sign all .so files
    print("  Signing .so files...")
    for item in app_bundle.rglob("*.so"):
        codesign(item)

    # step 3: sign the main executable
    executable = app_bundle / "Contents" / "MacOS" / "Mp4Forge"
    if executable.exists():
        print("  Signing main executable...")
        codesign(executable)

    # step 4: sign the outer .app bundle
    print("  Signing outer app bundle...")
    result = subprocess.run(
        ["codesign", "--force", "--sign", "-", str(app_bundle)],
        capture_output=True,
        text=True,
    )
    if result.returncode != 0:
        print(f"  Failed to sign app bundle: {result.stderr.strip()}")
        return False

    print("App bundle signed successfully.")
    return True


# def get_site_packages() -> Path:
#     output = run(
#         ("uv", "pip", "show", "PySide6"),
#         check=True,
#         capture_output=True,
#         text=True,
#     ).stdout.strip()
#     get_location = re.search(r"Location: (.+)\n", output, flags=re.M)
#     if not get_location:
#         raise FileNotFoundError("Can not detect site packages")
#     return Path(get_location.group(1))


def build_app():
    # change directory to the project's root directory
    project_root = Path(__file__).parent
    os.chdir(project_root)

    # define and create pyinstaller output path
    pyinstaller_folder = Path(project_root / "pyinstaller_build")
    pyinstaller_folder.mkdir(exist_ok=True)

    # dev runtime path to pull into final package
    dev_runtime = project_root / "runtime"

    # define paths before changing directory
    desktop_script = Path(project_root / "frontend_desktop" / "main.py")
    icon_path = Path(dev_runtime / "images" / "mp4.ico")

    # change directory so we output all of pyinstallers files in it's own folder
    os.chdir(pyinstaller_folder)

    # run pyinstaller onedir (bundle) build
    # skip icon on macOS as it will be added during .app bundle preparation
    build_args = [
        "uv",
        "run",
        "pyinstaller",
        "-n",
        "Mp4Forge",
        "--distpath",
        "bundled_mode",
        f"--add-data={dev_runtime}:runtime",
        "--contents-directory",
        "bundle",
        "--windowed",
    ]

    # only add icon on Windows/Linux; macOS uses .icns added during bundle prep
    if platform.system() != "Darwin":
        build_args.append(f"--icon={str(icon_path)}")

    build_args.extend(["-y", str(desktop_script)])

    build_job_onedir = run(build_args)

    # cleanse included runtime folder of unneeded files
    RUNTIME_WHITELIST = (
        "images",
    )

    bundled_runtime = Path("bundled_mode") / "Mp4Forge" / "bundle" / "runtime"
    if bundled_runtime.exists():
        for item in bundled_runtime.iterdir():
            if item.is_dir() and item.name not in RUNTIME_WHITELIST:
                shutil.rmtree(item)
                print(f"Removed: {item.name}")
            elif item.is_file():
                item.unlink()
                print(f"Removed: {item.name}")

    exe_str = get_executable_extension()
    success_msgs = []

    # check onedir (bundle) build
    onedir_path = Path("bundled_mode") / "Mp4Forge" / f"Mp4Forge{exe_str}"
    build_succeeded = onedir_path.is_file() and str(build_job_onedir.returncode) == "0"

    if build_succeeded:
        success_msgs.append(f"Bundle build success! Path: {Path.cwd() / onedir_path}")
    else:
        success_msgs.append("Bundle build did not complete successfully")

    # store absolute path before changing directory
    pyinstaller_output = pyinstaller_folder / "bundled_mode"

    # change directory back to original directory
    os.chdir(desktop_script.parent)

    # on macOS, prepare and sign the .app bundle
    if platform.system() == "Darwin" and build_succeeded:
        try:
            # get version from pyproject.toml
            pyproject_path = project_root / "pyproject.toml"
            pyproject = load_toml(pyproject_path)
            version = pyproject["project"]["version"]

            icon_png = project_root / "runtime" / "images" / "mp4.png"

            # use PyInstaller's own bundle as base — do not restructure it
            app_bundle = prepare_app_bundle(
                pyinstaller_bundle=pyinstaller_output,
                app_name="Mp4Forge",
                version=version,
                bundle_identifier="io.github.jessielw.mp4forge",
                icon_path=icon_png if icon_png.exists() else None,
            )
            success_msgs.append(f"macOS app bundle prepared: {app_bundle}")

            # macOS 26 Tahoe / Apple Silicon: clean, strip blockers, and sign
            clean_extended_attributes(app_bundle)
            remove_codesign_blockers(app_bundle)
            signed = sign_app_bundle(app_bundle)
            if signed:
                success_msgs.append("macOS app bundle signed successfully (ad-hoc)")
            else:
                success_msgs.append(
                    "Warning: macOS app bundle signing failed - app may not launch on Apple Silicon"
                )

        except Exception as e:
            success_msgs.append(f"Warning: Failed to prepare .app bundle: {e}")

    return "\n".join(success_msgs)


if __name__ == "__main__":
    build = build_app()
    print(build)
