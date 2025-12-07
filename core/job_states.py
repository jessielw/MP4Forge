"""Data structures for muxing job states.

These are pure data structures with no UI dependencies,
suitable for both desktop and web front-ends.
"""

from dataclasses import dataclass
from pathlib import Path

from iso639 import Language


@dataclass(frozen=True, slots=True)
class VideoState:
    """Video track state for muxing."""

    input_file: Path
    language: Language | None = None
    title: str = ""
    delay_ms: int = 0

    def to_dict(self) -> dict:
        """Convert to dictionary for serialization."""
        return {
            "input_file": str(self.input_file),
            "language": self.language.part3 if self.language else None,
            "title": self.title,
            "delay_ms": self.delay_ms,
        }


@dataclass(frozen=True, slots=True)
class AudioState:
    """Audio track state for muxing."""

    input_file: Path
    language: Language | None = None
    title: str = ""
    delay_ms: int = 0
    default: bool = False
    track_id: int | None = None  # for multi-track MP4 inputs

    def to_dict(self) -> dict:
        """Convert to dictionary for serialization."""
        return {
            "input_file": str(self.input_file),
            "language": self.language.part3 if self.language else None,
            "title": self.title,
            "delay_ms": self.delay_ms,
            "default": self.default,
            "track_id": self.track_id,
        }


@dataclass(frozen=True, slots=True)
class SubtitleState:
    """Subtitle track state for muxing."""

    input_file: Path
    language: Language | None = None
    title: str = ""
    default: bool = False
    forced: bool = False

    def to_dict(self) -> dict:
        """Convert to dictionary for serialization."""
        return {
            "input_file": str(self.input_file),
            "language": self.language.part3 if self.language else None,
            "title": self.title,
            "default": self.default,
            "forced": self.forced,
        }


@dataclass(frozen=True, slots=True)
class ChapterState:
    """Chapter state for muxing."""

    chapters: str | None = None

    def to_dict(self) -> dict:
        """Convert to dictionary for serialization."""
        return {
            "chapters": self.chapters,
        }
