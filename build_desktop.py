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
    with open(file_path, "rb") as f:
        return tomllib.load(f)


def create_icns_from_png(png_path: Path, output_icns: Path) -> bool:
    """
    Convert PNG to ICNS format using sips (macOS built-in tool).
    Returns True if successful, False otherwise.
    """
    try:
        if platform.system() != "Darwin":
            print("Warning: ICNS conversion is only supported on macOS")
            return False

        # create iconset directory
        iconset_dir = output_icns.parent / f"{output_icns.stem}.iconset"
        iconset_dir.mkdir(exist_ok=True)

        # generate different sizes required for ICNS
        sizes = [16, 32, 64, 128, 256, 512, 1024]
        for size in sizes:
            output_file = iconset_dir / f"icon_{size}x{size}.png"
            subprocess.run(
                [
                    "sips",
                    "-z",
                    str(size),
                    str(size),
                    str(png_path),
                    "--out",
                    str(output_file),
                ],
                check=True,
                capture_output=True,
            )

            # create @2x versions for retina displays (except for largest size)
            if size <= 512:
                retina_size = size * 2
                output_file_2x = iconset_dir / f"icon_{size}x{size}@2x.png"
                subprocess.run(
                    [
                        "sips",
                        "-z",
                        str(retina_size),
                        str(retina_size),
                        str(png_path),
                        "--out",
                        str(output_file_2x),
                    ],
                    check=True,
                    capture_output=True,
                )

        # convert iconset to icns
        subprocess.run(
            ["iconutil", "-c", "icns", str(iconset_dir), "-o", str(output_icns)],
            check=True,
            capture_output=True,
        )

        # clean up iconset directory
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
    # define .app structure paths
    app_bundle = pyinstaller_output_dir.parent / f"{app_name}.app"
    contents_dir = app_bundle / "Contents"
    macos_dir = contents_dir / "MacOS"
    resources_dir = contents_dir / "Resources"

    # clean up if it already exists
    if app_bundle.exists():
        shutil.rmtree(app_bundle)

    # create directory structure
    macos_dir.mkdir(parents=True, exist_ok=True)
    resources_dir.mkdir(parents=True, exist_ok=True)

    print(f"Creating app bundle: {app_bundle}")

    # move PyInstaller contents to MacOS directory
    # PyInstaller creates a folder with the app name containing the executable and resources
    pyinstaller_app_dir = pyinstaller_output_dir / app_name
    if pyinstaller_app_dir.exists():
        # move everything from the PyInstaller output to MacOS
        for item in pyinstaller_app_dir.iterdir():
            dest = macos_dir / item.name
            if item.is_dir():
                shutil.copytree(item, dest)
            else:
                shutil.copy2(item, dest)
        print(f"Copied PyInstaller output to MacOS directory")
    else:
        raise FileNotFoundError(f"PyInstaller output not found: {pyinstaller_app_dir}")

    # handle icon
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

    # create Info.plist
    plist_data = create_info_plist(app_name, version, bundle_identifier)
    plist_path = contents_dir / "Info.plist"
    with open(plist_path, "wb") as f:
        plistlib.dump(plist_data, f)
    print(f"Created Info.plist")

    # make the executable actually executable
    executable = macos_dir / app_name
    if executable.exists():
        os.chmod(executable, 0o755)
        print(f"Set executable permissions on {app_name}")

    print(f"Successfully created app bundle: {app_bundle}")
    return app_bundle


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

    # get extra deps
    # site_packages = get_site_packages()

    # change directory so we output all of pyinstallers files in it's own folder
    os.chdir(pyinstaller_folder)

    # run pyinstaller onefile build
    # build_job_onefile = run(
    #     [
    #         "uv",
    #         "run",
    #         "pyinstaller",
    #         "-n",
    #         "Mp4Forge",
    #         "--onefile",
    #         # f"--icon={str(icon_path)}",
    #         "-y",
    #         str(desktop_script),
    #     ]
    # )

    # run pyinstaller onedir (bundle) build
    # Build command args - skip icon on macOS as it will be added during .app bundle creation
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

    # only add icon on Windows/Linux; macOS uses .icns which is added during .app bundle creation
    if platform.system() != "Darwin":
        build_args.append(f"--icon={str(icon_path)}")

    build_args.extend(["-y", str(desktop_script)])

    build_job_onedir = run(build_args)

    # cleanse included runtime folder of unneeded files
    # whitelist of runtime subdirectories to keep in the bundled build
    RUNTIME_WHITELIST = (
        "images",
        # add more subdirectories here if needed
    )

    # bundled_runtime = Path(desktop_script.parent / "bundle" / "runtime")
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

    # # Check onefile build
    # onefile_path = Path("dist") / f"Mp4Forge{exe_str}"
    # if onefile_path.is_file() and str(build_job_onefile.returncode) == "0":
    #     success_msgs.append(f"Onefile build success! Path: {Path.cwd() / onefile_path}")
    # else:
    #     success_msgs.append("Onefile build did not complete successfully")

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

    # on macOS, create a proper .app bundle
    if platform.system() == "Darwin" and build_succeeded:
        try:
            # get version from pyproject.toml
            pyproject_path = project_root / "pyproject.toml"
            pyproject = load_toml(pyproject_path)
            version = pyproject["project"]["version"]

            # create .app bundle (pyinstaller_output already defined above)
            icon_png = project_root / "runtime" / "images" / "mp4.png"

            app_bundle = create_app_bundle(
                pyinstaller_output_dir=pyinstaller_output,
                app_name="Mp4Forge",
                version=version,
                bundle_identifier="io.github.jessielw.mp4forge",
                icon_path=icon_png if icon_png.exists() else None,
            )
            success_msgs.append(f"macOS app bundle created: {app_bundle}")
        except Exception as e:
            success_msgs.append(f"Warning: Failed to create .app bundle: {e}")

    return "\n".join(success_msgs)


if __name__ == "__main__":
    build = build_app()
    print(build)
