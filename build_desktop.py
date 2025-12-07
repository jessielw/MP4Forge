import os
import platform
from pathlib import Path
from subprocess import run


def get_executable_extension() -> str:
    return ".exe" if platform.system() == "Windows" else ""


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
    # define and create pyinstaller output path
    pyinstaller_folder = Path(Path(__file__).parent / "pyinstaller_build")
    pyinstaller_folder.mkdir(exist_ok=True)

    # define paths before changing directory
    desktop_script = Path(Path.cwd() / "frontend_desktop" / "main.py")
    # icon_path = Path(Path.cwd() / "icon" / "icon.ico")

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
    build_job_onedir = run(
        [
            "uv",
            "run",
            "pyinstaller",
            "-n",
            "Mp4Forge",
            "--distpath",
            "bundled_mode",
            "--contents-directory",
            "bundle",
            # f"--icon={str(icon_path)}",
            "-y",
            str(desktop_script),
        ]
    )

    exe_str = get_executable_extension()
    success_msgs = []

    # # Check onefile build
    # onefile_path = Path("dist") / f"Mp4Forge{exe_str}"
    # if onefile_path.is_file() and str(build_job_onefile.returncode) == "0":
    #     success_msgs.append(f"Onefile build success! Path: {Path.cwd() / onefile_path}")
    # else:
    #     success_msgs.append("Onefile build did not complete successfully")

    # Check onedir (bundle) build
    onedir_path = Path("bundled_mode") / "Mp4Forge" / f"Mp4Forge{exe_str}"
    if onedir_path.is_file() and str(build_job_onedir.returncode) == "0":
        success_msgs.append(f"Bundle build success! Path: {Path.cwd() / onedir_path}")
    else:
        success_msgs.append("Bundle build did not complete successfully")

    # change directory back to original directory
    os.chdir(desktop_script.parent)

    return "\n".join(success_msgs)


if __name__ == "__main__":
    build = build_app()
    print(build)
