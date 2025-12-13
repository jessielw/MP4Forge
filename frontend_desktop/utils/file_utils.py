from pathlib import Path
from platform import system
from subprocess import run


def open_explorer(path: Path) -> None:
    """Multi platform way to open explorer at X path"""
    if path.exists() and path.is_dir():
        cur_platform = system()
        # windows
        if cur_platform == "Windows":
            from os import startfile

            startfile(str(path))
        # mac
        elif cur_platform == "Darwin":
            run(["open", str(path.as_posix())])
        # Linux and others
        else:
            run(["xdg-open", str(path.as_posix())])
