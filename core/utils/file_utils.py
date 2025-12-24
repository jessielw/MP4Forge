import os
from pathlib import Path


def browse_directory(path: Path | None = None) -> dict:
    """
    Browse directory contents, returning structured data.

    Returns:
        dict with current_path, parent_path, and items
    """
    target_path = path.resolve() if path else Path.home()

    if not target_path.exists():
        raise FileNotFoundError(f"Path not found: {target_path}")

    if not target_path.is_dir():
        raise NotADirectoryError("Path is not a directory")

    # use scandir for better performance - it caches stat results
    items = []
    with os.scandir(target_path) as entries:
        for entry in entries:
            try:
                items.append(
                    {
                        "name": entry.name,
                        "path": entry.path,
                        "is_dir": entry.is_dir(),
                        "size": entry.stat().st_size if entry.is_file() else None,
                    }
                )
            except (OSError, PermissionError):
                # skip files we can't access
                continue

    # sort: directories first, then alphabetically
    items.sort(key=lambda x: (not x["is_dir"], x["name"].lower()))

    # allow navigating to parent
    parent = target_path.parent
    parent_path = str(parent) if parent != target_path else None

    return {
        "current_path": str(target_path),
        "parent_path": parent_path,
        "items": items,
    }


def list_directory(path: Path) -> list[Path]:
    """List files in directory"""
    if not path.exists() or not path.is_dir():
        return []
    return sorted(path.iterdir(), key=lambda x: (not x.is_dir(), x.name))


def get_video_files(path: Path) -> list[Path]:
    """Get only video files"""
    video_exts = {".mp4", ".mkv", ".avi", ".mov", ".wmv"}
    return [
        f
        for f in list_directory(path)
        if f.is_file() and f.suffix.lower() in video_exts
    ]
