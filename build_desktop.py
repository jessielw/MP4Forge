import platform
import shutil
import subprocess
from pathlib import Path
from subprocess import run


def get_executable_extension() -> str:
    return ".exe" if platform.system() == "Windows" else ""


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
        if iconset_dir.exists():
            shutil.rmtree(iconset_dir)
        if output_icns.exists():
            output_icns.unlink()
        iconset_dir.mkdir()

        # Generate the exact iconset entries accepted by iconutil.
        icon_sizes = (
            ("icon_16x16.png", 16),
            ("icon_16x16@2x.png", 32),
            ("icon_32x32.png", 32),
            ("icon_32x32@2x.png", 64),
            ("icon_128x128.png", 128),
            ("icon_128x128@2x.png", 256),
            ("icon_256x256.png", 256),
            ("icon_256x256@2x.png", 512),
            ("icon_512x512.png", 512),
            ("icon_512x512@2x.png", 1024),
        )
        for filename, size in icon_sizes:
            output_file = iconset_dir / filename
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


def verify_macos_bundle(app_bundle: Path) -> None:
    """Fail the build if PyInstaller's final app signature is invalid."""
    result = run(
        [
            "codesign",
            "--verify",
            "--deep",
            "--strict",
            "--verbose=2",
            str(app_bundle),
        ],
        capture_output=True,
        text=True,
    )
    if result.returncode != 0:
        details = result.stderr.strip() or result.stdout.strip()
        raise RuntimeError(f"macOS bundle signature verification failed: {details}")
    print(f"Verified macOS bundle signature: {app_bundle}")


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


def build_app() -> str:
    project_root = Path(__file__).resolve().parent
    pyinstaller_folder = project_root / "pyinstaller_build"
    pyinstaller_folder.mkdir(exist_ok=True)

    dev_runtime = project_root / "runtime"
    desktop_script = project_root / "frontend_desktop" / "main.py"
    system = platform.system()

    # Give PyInstaller the finished icon before it assembles and signs the
    # native app. Modifying the bundle afterward would invalidate its seal.
    mac_icon_path = pyinstaller_folder / "AppIcon.icns"
    has_mac_icon = False
    if system == "Darwin":
        icon_png = dev_runtime / "images" / "mp4.png"
        if icon_png.exists():
            has_mac_icon = create_icns_from_png(icon_png, mac_icon_path)

    output_root = pyinstaller_folder / "bundled_mode"
    build_args = [
        "uv",
        "run",
        "--frozen",
        "pyinstaller",
        "-n",
        "Mp4Forge",
        "--distpath",
        str(output_root),
        f"--add-data={dev_runtime}:runtime",
        "--contents-directory",
        "bundle",
        "--windowed",
        "--clean",
    ]

    if system == "Darwin":
        build_args.append("--osx-bundle-identifier=io.github.jessielw.mp4forge")
        if has_mac_icon:
            build_args.append(f"--icon={mac_icon_path}")
    else:
        icon_path = dev_runtime / "images" / "mp4.ico"
        build_args.append(f"--icon={icon_path}")

    build_args.extend(["-y", str(desktop_script)])
    run(build_args, check=True, cwd=pyinstaller_folder)

    # The macOS .app must remain byte-for-byte as PyInstaller produced it;
    # its Resources/Frameworks symlinks and signatures are part of the bundle.
    if system == "Darwin":
        output_path = output_root / "Mp4Forge.app"
        if not output_path.is_dir():
            raise FileNotFoundError(f"macOS app bundle not found: {output_path}")
        verify_macos_bundle(output_path)
    else:
        bundled_runtime = output_root / "Mp4Forge" / "bundle" / "runtime"
        if bundled_runtime.exists():
            for item in bundled_runtime.iterdir():
                if item.is_dir() and item.name != "images":
                    shutil.rmtree(item)
                    print(f"Removed: {item.name}")
                elif item.is_file():
                    item.unlink()
                    print(f"Removed: {item.name}")

        executable = f"Mp4Forge{get_executable_extension()}"
        output_path = output_root / "Mp4Forge" / executable
        if not output_path.is_file():
            raise FileNotFoundError(f"Bundle executable not found: {output_path}")

    return f"Bundle build success! Path: {output_path}"


if __name__ == "__main__":
    build = build_app()
    print(build)
