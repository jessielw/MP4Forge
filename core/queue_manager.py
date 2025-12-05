from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum, auto
from pathlib import Path
from typing import Optional
from uuid import UUID, uuid4

from core.job_states import AudioState, ChapterState, SubtitleState, VideoState


class JobStatus(Enum):
    """Status of a muxing job"""

    QUEUED = auto()
    PROCESSING = auto()
    COMPLETED = auto()
    FAILED = auto()
    CANCELLED = auto()


@dataclass
class MuxJob:
    """Represents a single muxing job with full metadata"""

    job_id: UUID = field(default_factory=uuid4)
    video: Optional[VideoState] = None
    audio_tracks: list[AudioState] = field(default_factory=list)
    subtitle_tracks: list[SubtitleState] = field(default_factory=list)
    chapters: Optional[ChapterState] = None
    output_file: Path = Path("output.mp4")
    status: JobStatus = JobStatus.QUEUED
    progress: float = 0.0
    error_message: Optional[str] = None
    created_at: datetime = field(default_factory=datetime.now)
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None

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


class QueueCallback:
    """Override in UI layer to receive queue updates"""

    def on_job_added(self, job: MuxJob):
        pass

    def on_job_status_changed(self, job: MuxJob):
        pass

    def on_job_progress(self, job: MuxJob, progress: float, message: str):
        pass

    def on_queue_completed(self):
        pass


class QueueManager:
    """Manages the job queue - singleton pattern"""

    _instance = None

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance

    def __init__(self):
        if not hasattr(self, "_initialized"):
            self.jobs: dict[UUID, MuxJob] = {}
            self.queue_order: list[UUID] = []
            self.callbacks: list[QueueCallback] = []
            self.is_processing = False
            self._initialized = True

    def register_callback(self, callback: QueueCallback):
        """Register a callback for queue updates"""
        if callback not in self.callbacks:
            self.callbacks.append(callback)

    def unregister_callback(self, callback: QueueCallback):
        """Remove a callback"""
        if callback in self.callbacks:
            self.callbacks.remove(callback)

    def add_job(self, job: MuxJob) -> UUID:
        """Add a job to the queue"""
        self.jobs[job.job_id] = job
        self.queue_order.append(job.job_id)

        for callback in self.callbacks:
            callback.on_job_added(job)

        return job.job_id

    def get_job(self, job_id: UUID) -> Optional[MuxJob]:
        """Get a specific job by ID"""
        return self.jobs.get(job_id)

    def get_all_jobs(self) -> list[MuxJob]:
        """Get all jobs in queue order"""
        return [self.jobs[jid] for jid in self.queue_order if jid in self.jobs]

    def get_queued_jobs(self) -> list[MuxJob]:
        """Get jobs waiting to be processed"""
        return [j for j in self.get_all_jobs() if j.status == JobStatus.QUEUED]

    def update_job_status(
        self, job_id: UUID, status: JobStatus, error: Optional[str] = None
    ):
        """Update job status"""
        job = self.jobs.get(job_id)
        if not job:
            return

        job.status = status
        if error:
            job.error_message = error

        if status == JobStatus.PROCESSING:
            job.started_at = datetime.now()
        elif status in (JobStatus.COMPLETED, JobStatus.FAILED, JobStatus.CANCELLED):
            job.completed_at = datetime.now()

        for callback in self.callbacks:
            callback.on_job_status_changed(job)

    def update_job_progress(self, job_id: UUID, progress: float, message: str = ""):
        """Update job progress"""
        job = self.jobs.get(job_id)
        if not job:
            return

        job.progress = progress

        for callback in self.callbacks:
            callback.on_job_progress(job, progress, message)

    def remove_job(self, job_id: UUID):
        """Remove a job from the queue"""
        if job_id in self.jobs:
            del self.jobs[job_id]
        if job_id in self.queue_order:
            self.queue_order.remove(job_id)

    def clear_completed(self):
        """Remove all completed/failed/cancelled jobs"""
        to_remove = [
            jid
            for jid, job in self.jobs.items()
            if job.status
            in (JobStatus.COMPLETED, JobStatus.FAILED, JobStatus.CANCELLED)
        ]
        for jid in to_remove:
            self.remove_job(jid)

    def cancel_job(self, job_id: UUID):
        """Cancel a specific job (queued or processing)"""
        job = self.jobs.get(job_id)
        if job and job.status in (JobStatus.QUEUED, JobStatus.PROCESSING):
            self.update_job_status(job_id, JobStatus.CANCELLED)
