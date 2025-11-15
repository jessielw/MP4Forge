from dataclasses import asdict, dataclass
from typing import Generic, TypeVar

from PySide6.QtWidgets import QWidget


@dataclass(frozen=True, slots=True)
class BaseTabState:
    """Base data structure for exporting tab states."""

    def to_dict(self) -> dict:
        """Converts the tab state to a dictionary."""
        return asdict(self)


TState = TypeVar("TState", bound=BaseTabState)


class BaseTab(QWidget, Generic[TState]):
    """Base class for all tabs."""

    def __init__(self, parent=None) -> None:
        super().__init__(parent)

    def is_tab_ready(self) -> bool:
        """Returns whether the tab is ready for muxing."""
        raise NotImplementedError("is_tab_ready must be implemented by subclasses.")

    def export_state(self) -> TState:
        """Exports the current state of the tab as a BaseTabState (concrete subtype)."""
        raise NotImplementedError("export_state must be implemented by subclasses.")

    def reset_tab(self) -> None:
        """Resets the tab to its initial state."""
        raise NotImplementedError("reset_tab must be implemented by subclasses.")
