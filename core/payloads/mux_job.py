from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path
from uuid import UUID, uuid4

from core.enums.job_status import JobStatus
from core.job_states import AudioState, ChapterState, SubtitleState, VideoState


@dataclass
class MuxJob:
    """Represents a single muxing job with full metadata"""

    job_id: UUID = field(default_factory=uuid4)
    video: VideoState | None = None
    audio_tracks: list[AudioState] = field(default_factory=list)
    subtitle_tracks: list[SubtitleState] = field(default_factory=list)
    chapters: ChapterState | None = None
    output_file: Path = Path("output.mp4")
    status: JobStatus = JobStatus.QUEUED
    progress: float = 0.0
    error_message: str | None = None
    created_at: datetime = field(default_factory=datetime.now)
    started_at: datetime | None = None
    completed_at: datetime | None = None

    def to_dict(self) -> dict:
        """Export job as dictionary for serialization"""
        return {
            "job_id": str(self.job_id),
            "video": self.video.to_dict() if self.video else None,
            "audio_tracks": [track.to_dict() for track in self.audio_tracks],
            "subtitle_tracks": [track.to_dict() for track in self.subtitle_tracks],
            "chapters": self.chapters.to_dict() if self.chapters else None,
            "output_file": str(self.output_file),
            "status": self.status.name,
            "progress": self.progress,
            "error_message": self.error_message,
            "created_at": self.created_at.isoformat(),
            "started_at": self.started_at.isoformat() if self.started_at else None,
            "completed_at": self.completed_at.isoformat()
            if self.completed_at
            else None,
        }
