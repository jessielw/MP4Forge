from os import PathLike
from pathlib import Path

from pymediainfo import MediaInfo


def get_media_info(file_path: PathLike[str]) -> tuple[MediaInfo, Path]:
    """Retrieve media information for a given file."""
    fp = Path(file_path)
    mi = MediaInfo.parse(fp, legacy_stream_display=True)
    return mi, fp


def get_media_info_web(file_path: PathLike[str]) -> str:
    """Retrieve media information as JSON for web."""
    return get_media_info(file_path)[0].to_json()
