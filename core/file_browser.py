"""File browsing logic"""

from pathlib import Path


class FileBrowser:
    """Pure file system operations"""

    def list_directory(self, path: Path) -> list[Path]:
        """List files in directory"""
        if not path.exists() or not path.is_dir():
            return []
        return sorted(path.iterdir(), key=lambda x: (not x.is_dir(), x.name))

    def get_video_files(self, path: Path) -> list[Path]:
        """Get only video files"""
        video_exts = {".mp4", ".mkv", ".avi", ".mov", ".wmv"}
        return [
            f
            for f in self.list_directory(path)
            if f.is_file() and f.suffix.lower() in video_exts
        ]
