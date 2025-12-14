from enum import Enum, auto


class JobStatus(Enum):
    """Status of a muxing job"""

    QUEUED = auto()
    PROCESSING = auto()
    COMPLETED = auto()
    FAILED = auto()
    CANCELLED = auto()
