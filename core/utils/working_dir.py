import sys
from pathlib import Path


def _get_working_directories() -> tuple[Path, Path, bool]:
    """
    Used to determine the correct working directory automatically.
    This way we can utilize files/relative paths easily.

    Returns:
        (Path, Path, bool): Current working directory, runtime directory, frozen.
    """
    # we're in a pyinstaller bundle
    if getattr(sys, "frozen", False) and hasattr(sys, "_MEIPASS"):
        path = Path(sys.executable).parent
        return path, path / "bundle" / "runtime", True

    # we're running from a *.py file
    else:
        path = Path.cwd()
        return path, path / "runtime", False


CURRENT_DIR, RUNTIME_DIR, IS_FROZEN = _get_working_directories()
