from dataclasses import asdict, dataclass
from pathlib import Path

from iso639 import Language


@dataclass(frozen=True, slots=True)
class BaseTabState:
    """Base data structure for exporting tab states."""

    def to_dict(self) -> dict:
        """Converts the tab state to a dictionary."""
        return asdict(self)


@dataclass(frozen=True, slots=True)
class VideoTabState(BaseTabState):
    """Data structure for exporting the state of the Video tab."""

    input_file: Path
    language: Language | None
    title: str
    delay_ms: int
