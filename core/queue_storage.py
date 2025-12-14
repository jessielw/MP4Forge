import json
import sqlite3
from datetime import datetime
from pathlib import Path
from uuid import UUID

from iso639 import Language

from core.enums.job_status import JobStatus
from core.job_states import AudioState, ChapterState, SubtitleState, VideoState
from core.logger import LOG
from core.payloads.mux_job import MuxJob
from core.utils.working_dir import CONFIG_DIR

######### IMPORTANT #########
# Increment this when making breaking changes to the database schema
# or job serialization format that would make old jobs incompatible
DB_VERSION = 1
######### IMPORTANT #########


class QueueStorage:
    """SQLite-based persistent storage for job queue"""

    def __init__(self, db_path: Path | None = None) -> None:
        """Initialize queue storage

        Args:
            db_path: Path to SQLite database. Defaults to runtime/queue.db
        """
        self.db_path = db_path or CONFIG_DIR / "queue.db"
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        self._init_database()

    def _init_database(self) -> None:
        """Create database tables if they don't exist, check version compatibility"""
        with sqlite3.connect(self.db_path) as conn:
            # create version table
            conn.execute("""
                CREATE TABLE IF NOT EXISTS db_version (
                    version INTEGER PRIMARY KEY
                )
            """)

            # check current version
            cursor = conn.execute("SELECT version FROM db_version")
            row = cursor.fetchone()
            current_version = row[0] if row else None

            if current_version is not None and current_version != DB_VERSION:
                # version mismatch - backup and clear old data
                LOG.warning(
                    f"Queue database version mismatch (current: {current_version}, expected: {DB_VERSION}). "
                    f"Clearing incompatible jobs."
                )
                # backup old database
                backup_path = self.db_path.with_suffix(f".v{current_version}.bak")
                try:
                    import shutil

                    shutil.copy2(self.db_path, backup_path)
                    LOG.info(f"Backed up old queue to {backup_path}")
                except Exception as e:
                    LOG.error(f"Failed to backup old queue: {e}")

                # drop all tables and recreate
                conn.execute("DROP TABLE IF EXISTS jobs")
                conn.execute("DROP TABLE IF EXISTS db_version")
                conn.execute("""
                    CREATE TABLE db_version (
                        version INTEGER PRIMARY KEY
                    )
                """)

            # set/update version
            conn.execute("DELETE FROM db_version")  # clear any old version
            conn.execute("INSERT INTO db_version (version) VALUES (?)", (DB_VERSION,))

            # create jobs table
            conn.execute("""
                CREATE TABLE IF NOT EXISTS jobs (
                    job_id TEXT PRIMARY KEY,
                    video_state TEXT,
                    audio_tracks TEXT,
                    subtitle_tracks TEXT,
                    chapters TEXT,
                    output_file TEXT NOT NULL,
                    status TEXT NOT NULL,
                    error_message TEXT,
                    created_at TEXT NOT NULL,
                    started_at TEXT,
                    completed_at TEXT,
                    queue_position INTEGER NOT NULL
                )
            """)
            conn.execute("""
                CREATE INDEX IF NOT EXISTS idx_status 
                ON jobs(status)
            """)
            conn.execute("""
                CREATE INDEX IF NOT EXISTS idx_queue_position 
                ON jobs(queue_position)
            """)
            conn.commit()

    def save_job(self, job: "MuxJob", position: int) -> None:
        """Save or update a job in the database

        Args:
            job: MuxJob instance to save
            position: Position in queue order
        """
        with sqlite3.connect(self.db_path) as conn:
            conn.execute(
                """
                INSERT OR REPLACE INTO jobs (
                    job_id, video_state, audio_tracks, subtitle_tracks, chapters,
                    output_file, status, error_message,
                    created_at, started_at, completed_at, queue_position
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
                (
                    str(job.job_id),
                    json.dumps(_serialize_video_state(job.video))
                    if job.video
                    else None,
                    json.dumps([_serialize_audio_state(a) for a in job.audio_tracks]),
                    json.dumps(
                        [_serialize_subtitle_state(s) for s in job.subtitle_tracks]
                    ),
                    json.dumps(_serialize_chapter_state(job.chapters))
                    if job.chapters
                    else None,
                    str(job.output_file),
                    job.status.name,
                    job.error_message,
                    job.created_at.isoformat(),
                    job.started_at.isoformat() if job.started_at else None,
                    job.completed_at.isoformat() if job.completed_at else None,
                    position,
                ),
            )
            conn.commit()

    def load_all_jobs(self) -> list[tuple[UUID, dict, int]]:
        """Load all jobs from database

        Returns:
            List of (job_id, job_data_dict, queue_position) tuples
            sorted by queue_position
        """
        with sqlite3.connect(self.db_path) as conn:
            conn.row_factory = sqlite3.Row
            cursor = conn.execute("""
                SELECT * FROM jobs ORDER BY queue_position
            """)

            results = []
            for row in cursor:
                job_id = UUID(row["job_id"])
                job_data = {
                    "video_state": json.loads(row["video_state"])
                    if row["video_state"]
                    else None,
                    "audio_tracks": json.loads(row["audio_tracks"]),
                    "subtitle_tracks": json.loads(row["subtitle_tracks"]),
                    "chapters": json.loads(row["chapters"])
                    if row["chapters"]
                    else None,
                    "output_file": row["output_file"],
                    "status": row["status"],
                    "error_message": row["error_message"],
                    "created_at": row["created_at"],
                    "started_at": row["started_at"],
                    "completed_at": row["completed_at"],
                }
                results.append((job_id, job_data, row["queue_position"]))

            return results

    def delete_job(self, job_id: UUID) -> None:
        """Remove a job from database

        Args:
            job_id: UUID of job to remove
        """
        with sqlite3.connect(self.db_path) as conn:
            conn.execute("DELETE FROM jobs WHERE job_id = ?", (str(job_id),))
            conn.commit()

    def delete_completed_jobs(self) -> None:
        """Remove all completed, failed, and cancelled jobs"""
        with sqlite3.connect(self.db_path) as conn:
            conn.execute("""
                DELETE FROM jobs 
                WHERE status IN ('COMPLETED', 'FAILED', 'CANCELLED')
            """)
            conn.commit()

    def clear_all(self) -> None:
        """Clear entire queue database"""
        with sqlite3.connect(self.db_path) as conn:
            conn.execute("DELETE FROM jobs")
            conn.commit()


# serialization helpers
def _serialize_video_state(state: VideoState) -> dict:
    """Convert VideoState to JSON-serializable dict"""
    return {
        "input_file": str(state.input_file),
        "language": state.language.part3 if state.language else None,
        "title": state.title,
        "delay_ms": state.delay_ms,
    }


def _deserialize_video_state(data: dict) -> VideoState:
    """Reconstruct VideoState from dict"""
    return VideoState(
        input_file=Path(data["input_file"]),
        language=Language.from_part3(data["language"]) if data["language"] else None,
        title=data["title"],
        delay_ms=data["delay_ms"],
    )


def _serialize_audio_state(state: AudioState) -> dict:
    """Convert AudioState to JSON-serializable dict"""
    return {
        "input_file": str(state.input_file),
        "language": state.language.part3 if state.language else None,
        "title": state.title,
        "delay_ms": state.delay_ms,
        "default": state.default,
        "track_id": state.track_id,
    }


def _deserialize_audio_state(data: dict) -> AudioState:
    """Reconstruct AudioState from dict"""
    return AudioState(
        input_file=Path(data["input_file"]),
        language=Language.from_part3(data["language"]) if data["language"] else None,
        title=data["title"],
        delay_ms=data["delay_ms"],
        default=data["default"],
        track_id=data["track_id"],
    )


def _serialize_subtitle_state(state: SubtitleState) -> dict:
    """Convert SubtitleState to JSON-serializable dict"""
    return {
        "input_file": str(state.input_file),
        "language": state.language.part3 if state.language else None,
        "title": state.title,
        "default": state.default,
        "forced": state.forced,
        "track_id": state.track_id,
    }


def _deserialize_subtitle_state(data: dict) -> SubtitleState:
    """Reconstruct SubtitleState from dict"""
    return SubtitleState(
        input_file=Path(data["input_file"]),
        language=Language.from_part3(data["language"]) if data["language"] else None,
        title=data["title"],
        default=data["default"],
        forced=data["forced"],
        track_id=data["track_id"],
    )


def _serialize_chapter_state(state: ChapterState) -> dict:
    """Convert ChapterState to JSON-serializable dict"""
    return {
        "chapters": state.chapters,
    }


def _deserialize_chapter_state(data: dict) -> ChapterState:
    """Reconstruct ChapterState from dict"""
    return ChapterState(
        chapters=data["chapters"],
    )


def deserialize_job_data(job_id: UUID, data: dict) -> "MuxJob":
    """Reconstruct a MuxJob from database data

    Args:
        job_id: UUID for the job
        data: Dictionary with serialized job data

    Returns:
        Reconstructed MuxJob instance
    """
    return MuxJob(
        job_id=job_id,
        video=_deserialize_video_state(data["video_state"])
        if data["video_state"]
        else None,
        audio_tracks=[_deserialize_audio_state(a) for a in data["audio_tracks"]],
        subtitle_tracks=[
            _deserialize_subtitle_state(s) for s in data["subtitle_tracks"]
        ],
        chapters=_deserialize_chapter_state(data["chapters"])
        if data["chapters"]
        else None,
        output_file=Path(data["output_file"]),
        status=JobStatus[data["status"]],
        progress=0.0,  # always start at 0 on reload
        error_message=data["error_message"],
        created_at=datetime.fromisoformat(data["created_at"]),
        started_at=datetime.fromisoformat(data["started_at"])
        if data["started_at"]
        else None,
        completed_at=datetime.fromisoformat(data["completed_at"])
        if data["completed_at"]
        else None,
    )
