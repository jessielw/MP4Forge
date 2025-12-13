from dataclasses import dataclass
from pathlib import Path


@dataclass
class Context:
    """Holds shared context data for the frontend desktop application."""

    last_used_path: Path | None = None


context = Context()
