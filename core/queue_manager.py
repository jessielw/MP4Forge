from datetime import datetime
from uuid import UUID

from core.enums.job_status import JobStatus
from core.payloads.mux_job import MuxJob
from core.queue_storage import QueueStorage


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
    """Manages the job queue - singleton pattern with persistent storage"""

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
            self.storage: QueueStorage | None = None
            self._initialized = True

    def enable_persistence(self, storage: QueueStorage | None = None):
        """Enable persistent storage for the queue

        Args:
            storage: QueueStorage instance. If None, creates default instance.
        """
        if storage is None:
            from core.queue_storage import QueueStorage

            storage = QueueStorage()

        self.storage = storage
        self._load_from_storage()

    def _load_from_storage(self):
        """Load jobs from persistent storage on startup"""
        if not self.storage:
            return

        from core.queue_storage import deserialize_job_data

        loaded_jobs = self.storage.load_all_jobs()
        for job_id, job_data, position in loaded_jobs:
            job = deserialize_job_data(job_id, job_data)
            self.jobs[job_id] = job
            self.queue_order.append(job_id)

    def _save_to_storage(self):
        """Save current queue state to persistent storage"""
        if not self.storage:
            return

        for position, job_id in enumerate(self.queue_order):
            job = self.jobs.get(job_id)
            if job:
                self.storage.save_job(job, position)

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

        # persist to storage
        if self.storage:
            self.storage.save_job(job, len(self.queue_order) - 1)

        for callback in self.callbacks:
            callback.on_job_added(job)

        return job.job_id

    def get_job(self, job_id: UUID) -> MuxJob | None:
        """Get a specific job by ID"""
        return self.jobs.get(job_id)

    def get_all_jobs(self) -> list[MuxJob]:
        """Get all jobs in queue order"""
        return [self.jobs[jid] for jid in self.queue_order if jid in self.jobs]

    def get_queued_jobs(self) -> list[MuxJob]:
        """Get jobs waiting to be processed"""
        return [j for j in self.get_all_jobs() if j.status == JobStatus.QUEUED]

    def update_job_status(
        self, job_id: UUID, status: JobStatus, error: str | None = None
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

        # persist status change
        if self.storage:
            position = (
                self.queue_order.index(job_id) if job_id in self.queue_order else 0
            )
            self.storage.save_job(job, position)

        for callback in self.callbacks:
            callback.on_job_status_changed(job)

    def update_job_progress(self, job_id: UUID, progress: float, message: str = ""):
        """Update job progress (not persisted - transient state only)"""
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

        # remove from storage
        if self.storage:
            self.storage.delete_job(job_id)

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

        # batch delete from storage
        if self.storage:
            self.storage.delete_completed_jobs()

    def cancel_job(self, job_id: UUID):
        """Cancel a specific job (queued or processing)"""
        job = self.jobs.get(job_id)
        if job and job.status in (JobStatus.QUEUED, JobStatus.PROCESSING):
            self.update_job_status(job_id, JobStatus.CANCELLED)
