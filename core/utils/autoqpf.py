from pathlib import Path

from auto_qpf.generate_chapters import ChapterGenerator
from pymediainfo import MediaInfo


def auto_gen_chapters(mi: MediaInfo) -> str | None:
    chapters = ChapterGenerator().generate_ogm_chapters(
        media_info_obj=mi,
        output_path=Path("."),
        write_to_file=False,
    )
    if isinstance(chapters, Path):
        raise RuntimeError("Chapters should only be str or None")
    return chapters
