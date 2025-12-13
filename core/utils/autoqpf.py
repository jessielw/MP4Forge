from pathlib import Path

from auto_qpf.enums import ChapterType
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


def determine_chapter_type(mi: MediaInfo) -> str | None:
    """Determine chapter type based on MediaInfo."""
    mi_chaps = ChapterGenerator()._get_media_info_obj_chapters(mi)
    if not mi_chaps:
        return None
    chapters_data = ChapterGenerator()._determine_chapter_type(mi_chaps)
    if chapters_data:
        try:
            chap_enum = chapters_data[0]
            if chap_enum is ChapterType.NUMBERED and len(chapters_data) >= 4:
                chap_num_details = f" ({chapters_data[2]} - {chapters_data[3]})"
            else:
                chap_num_details = ""
            chap_type_str_map = {
                ChapterType.NAMED: "Named",
                ChapterType.NUMBERED: f"Numbered{chap_num_details}",
                ChapterType.TAGGED: "Tagged",
            }

            return chap_type_str_map[chap_enum]
        except Exception:
            return None
