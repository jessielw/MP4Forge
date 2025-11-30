"""Data structures for muxing job states.

These are pure data structures with no UI dependencies,
suitable for both desktop and web front-ends.
"""

from dataclasses import dataclass
from pathlib import Path
from typing import Optional

from iso639 import Language


@dataclass(frozen=True, slots=True)
class VideoState:
    """Video track state for muxing."""

    input_file: Path
    language: Optional[Language] = None
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
    language: Optional[Language] = None
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
class SubtitleState:
    """Subtitle track state for muxing."""

    input_file: Path
    language: Optional[Language] = None
    title: str = ""

    def to_dict(self) -> dict:
        """Convert to dictionary for serialization."""
        return {
            "input_file": str(self.input_file),
            "language": self.language.part3 if self.language else None,
            "title": self.title,
        }


@dataclass(frozen=True, slots=True)
class ChapterState:
    """Chapter state for muxing."""

    chapters: Optional[str] = None

    def to_dict(self) -> dict:
        """Convert to dictionary for serialization."""
        return {
            "chapters": self.chapters,
        }
