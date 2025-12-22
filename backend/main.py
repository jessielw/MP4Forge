import asyncio
import threading
from contextlib import asynccontextmanager
from dataclasses import dataclass, field
from pathlib import Path
from uuid import UUID

from fastapi import FastAPI, HTTPException, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles
from iso639 import Language as Iso639Language

from backend.schemas import (
    AddJobRequest,
    BrowseRequest,
    ExtractChaptersRequest,
    LogRequest,
    MediaInfoRequest,
    ReadFileRequest,
)
from core.enums.job_status import JobStatus
from core.job_states import AudioState, ChapterState, SubtitleState, VideoState
from core.logger import LOG, LogLevel
from core.muxer import ProgressCallback, VideoMuxer
from core.payloads.mux_job import MuxJob
from core.queue_manager import QueueCallback, QueueManager
from core.utils.autoqpf import auto_gen_chapters
from core.utils.file_utils import browse_directory
from core.utils.mediainfo import get_media_info, get_media_info_web


@dataclass(slots=True)
class AppState:
    """Application state container."""

    queue_manager: QueueManager
    active_connections: list[WebSocket] = field(default_factory=list)
    processor_thread: threading.Thread | None = None
    processor_running: bool = False
    processor_lock: threading.Lock = field(default_factory=threading.Lock)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Lifespan context manager to handle startup and shutdown events."""
    # initialize application state
    queue_manager = QueueManager()
    queue_manager.enable_persistence()

    app.state.app_state = AppState(queue_manager=queue_manager)

    # register WebSocket callback
    web_callback = WebQueueCallback(app)
    queue_manager.register_callback(web_callback)

    yield

    # cleanup: stop processor if running
    state = app.state.app_state
    with state.processor_lock:
        state.processor_running = False
    if state.processor_thread and state.processor_thread.is_alive():
        state.processor_thread.join(timeout=5.0)


app = FastAPI(lifespan=lifespan)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


class WebSocketCallback(ProgressCallback):
    """Send progress via WebSocket."""

    def __init__(self, websocket: WebSocket):
        self.websocket = websocket

    async def on_progress(self, percent: float, message: str):
        await self.websocket.send_json(
            {"type": "progress", "percent": percent, "message": message}
        )

    async def on_complete(self, output_file: str):
        await self.websocket.send_json({"type": "complete", "output": output_file})

    async def on_error(self, error: str):
        await self.websocket.send_json({"type": "error", "error": error})


@app.post("/api/mediainfo")
async def get_mediainfo(request: MediaInfoRequest):
    """Get MediaInfo for a file path."""
    file_path = Path(request.file_path)

    if not file_path.exists():
        raise HTTPException(
            status_code=404, detail=f"File not found: {request.file_path}"
        )

    if not file_path.is_file():
        raise HTTPException(
            status_code=400, detail=f"Path is not a file: {request.file_path}"
        )

    try:
        mediainfo_json = get_media_info_web(file_path)
        return {"mediainfo": mediainfo_json}
    except Exception as e:
        raise HTTPException(
            status_code=500, detail=f"Error getting media info: {str(e)}"
        )


@app.post("/api/browse")
async def browse_dir(request: BrowseRequest):
    """Browse directory contents within allowed base path."""
    try:
        # target_path = Path(request.path) if request.path else None
        target_path = (
            Path(request.path)
            if request.path
            else Path(r"C:\Users\jlw_4049\Desktop\sample\mp4testing")
        )  # testing set this to None later
        result = browse_directory(target_path)
        LOG.debug(f"Browse result: {result['current_path']}")
        return result
    except PermissionError as e:
        raise HTTPException(status_code=403, detail=str(e))
    except FileNotFoundError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except NotADirectoryError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(
            status_code=500, detail=f"Error browsing directory: {str(e)}"
        )


@app.post("/api/create-folder")
async def create_folder(request: BrowseRequest):
    """Create a new folder."""
    if not request.path:
        raise HTTPException(status_code=400, detail="Path is required")

    try:
        folder_path = Path(request.path)
        folder_path.mkdir(parents=True, exist_ok=False)
        return {"success": True, "path": str(folder_path)}
    except FileExistsError:
        raise HTTPException(status_code=409, detail="Folder already exists")
    except PermissionError as e:
        raise HTTPException(status_code=403, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error creating folder: {str(e)}")


@app.post("/api/log")
async def log_from_frontend(request: LogRequest) -> None:
    """Log message from frontend with specified log level."""
    if request.level is LogLevel.DEBUG:
        LOG.debug(request.message, LOG.SRC.FE)
    elif request.level is LogLevel.INFO:
        LOG.info(request.message, LOG.SRC.FE)
    elif request.level is LogLevel.WARNING:
        LOG.warning(request.message, LOG.SRC.FE)
    elif request.level is LogLevel.ERROR:
        LOG.error(request.message, LOG.SRC.FE)
    elif request.level is LogLevel.CRITICAL:
        LOG.critical(request.message, LOG.SRC.FE)


@app.post("/api/extract-chapters")
async def extract_chapters(request: ExtractChaptersRequest):
    """Extract chapters from a video file."""
    file_path = Path(request.file_path)

    if not file_path.exists():
        raise HTTPException(
            status_code=404, detail=f"File not found: {request.file_path}"
        )

    if not file_path.is_file():
        raise HTTPException(
            status_code=400, detail=f"Path is not a file: {request.file_path}"
        )

    try:
        media_info, _ = get_media_info(file_path)
        chapters = auto_gen_chapters(media_info)
        return {"chapters": chapters if chapters else ""}
    except Exception as e:
        raise HTTPException(
            status_code=500, detail=f"Error extracting chapters: {str(e)}"
        )


@app.post("/api/read-file")
async def read_file(request: ReadFileRequest):
    """Read a text file and return its contents."""
    file_path = Path(request.file_path)

    if not file_path.exists():
        raise HTTPException(
            status_code=404, detail=f"File not found: {request.file_path}"
        )

    if not file_path.is_file():
        raise HTTPException(
            status_code=400, detail=f"Path is not a file: {request.file_path}"
        )

    try:
        with open(file_path, encoding="utf-8") as f:
            content = f.read()
        return {"content": content}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error reading file: {str(e)}")


@app.websocket("/ws/jobs")
async def job_websocket(websocket: WebSocket):
    """WebSocket endpoint for real-time job updates."""
    state = app.state.app_state
    await websocket.accept()
    state.active_connections.append(websocket)

    try:
        # send initial job list
        jobs = state.queue_manager.get_all_jobs()
        await websocket.send_json(
            {"type": "init", "jobs": [serialize_job(job) for job in jobs]}
        )

        # keep connection alive and listen for commands
        while True:
            data = await websocket.receive_json()  # TODO: use if needed?
            # handle client commands if needed

    except WebSocketDisconnect:
        state.active_connections.remove(websocket)
    except Exception as e:
        LOG.error(f"WebSocket error: {e}")
        if websocket in state.active_connections:
            state.active_connections.remove(websocket)


async def broadcast_job_update(state: AppState, job: MuxJob, event_type: str):
    """Broadcast job update to all connected clients."""
    message = {"type": event_type, "job": serialize_job(job)}
    for connection in state.active_connections:
        try:
            await connection.send_json(message)
        except Exception as e:
            LOG.error(f"Failed to send update to client: {e}")


def serialize_job(job: MuxJob) -> dict:
    """Serialize MuxJob to JSON-compatible dict."""
    # map backend status to frontend status names
    status_map = {
        "QUEUED": "pending",
        "PROCESSING": "processing",
        "COMPLETED": "completed",
        "FAILED": "failed",
        "CANCELLED": "failed",  # treat cancelled as failed for frontend
    }

    return {
        "id": str(job.job_id),
        "status": status_map.get(job.status.name, job.status.name.lower()),
        "progress": job.progress,
        "videoFile": str(job.video.input_file) if job.video else None,
        "audioTracks": [str(track.input_file) for track in job.audio_tracks],
        "subtitleTracks": [str(track.input_file) for track in job.subtitle_tracks],
        "chapters": job.chapters.chapters if job.chapters else None,
        "outputFile": str(job.output_file),
        "error": job.error_message,
        "createdAt": job.created_at.isoformat() if job.created_at else None,
        "startedAt": job.started_at.isoformat() if job.started_at else None,
        "completedAt": job.completed_at.isoformat() if job.completed_at else None,
    }


class WebQueueCallback(QueueCallback):
    """Callback to broadcast queue changes via WebSocket."""

    def __init__(self, app: FastAPI) -> None:
        super().__init__()
        self.app = app
        self.main_event_loop = asyncio.get_event_loop()

    def on_job_added(self, job: MuxJob):
        if self.main_event_loop and not self.main_event_loop.is_closed():
            asyncio.run_coroutine_threadsafe(
                broadcast_job_update(self.app.state.app_state, job, "job_added"),
                self.main_event_loop,
            )

    def on_job_status_changed(self, job: MuxJob):
        if self.main_event_loop and not self.main_event_loop.is_closed():
            asyncio.run_coroutine_threadsafe(
                broadcast_job_update(
                    self.app.state.app_state, job, "job_status_changed"
                ),
                self.main_event_loop,
            )

    def on_job_progress(self, job: MuxJob, progress: float, message: str):
        if self.main_event_loop and not self.main_event_loop.is_closed():
            asyncio.run_coroutine_threadsafe(
                broadcast_job_update(self.app.state.app_state, job, "job_progress"),
                self.main_event_loop,
            )


class BackendProgressCallback(ProgressCallback):
    """Progress callback that updates queue manager."""

    def __init__(self, job_id: UUID, queue_manager: QueueManager):
        self.job_id = job_id
        self.queue_manager = queue_manager

    def on_progress(self, percent: float, message: str) -> None:
        self.queue_manager.update_job_progress(self.job_id, percent, message)

    def on_complete(self, output_file: str) -> None:
        self.queue_manager.update_job_status(self.job_id, JobStatus.COMPLETED)

    def on_error(self, error: str) -> None:
        self.queue_manager.update_job_status(self.job_id, JobStatus.FAILED, error)


def process_queue(state: AppState):
    """Background thread to process queued jobs."""
    LOG.info("Queue processor started")

    while state.processor_running:
        with state.processor_lock:
            if not state.processor_running:
                break

            queued_jobs = state.queue_manager.get_queued_jobs()

            if not queued_jobs:
                # no more jobs to process, stop processor
                LOG.info("No more jobs in queue, stopping processor")
                state.processor_running = False
                break

            job = queued_jobs[0]

        try:
            LOG.info(f"Processing job {job.job_id}: {job.output_file}")

            # create muxer with progress callback
            callback = BackendProgressCallback(job.job_id, state.queue_manager)
            muxer = VideoMuxer(progress_callback=callback)

            # process the job
            muxer.mux_from_job(job)

            # check if job was cancelled during processing
            current_job = state.queue_manager.get_job(job.job_id)
            if current_job and current_job.status == JobStatus.CANCELLED:
                LOG.info(f"Job {job.job_id} was cancelled")
            elif current_job and current_job.status != JobStatus.COMPLETED:
                # If not already marked completed or cancelled, mark it
                state.queue_manager.update_job_status(job.job_id, JobStatus.COMPLETED)
                LOG.info(f"Job {job.job_id} completed successfully")

        except Exception as e:
            error_msg = f"Job failed: {str(e)}"
            LOG.error(f"Job {job.job_id} failed: {e}")
            state.queue_manager.update_job_status(
                job.job_id, JobStatus.FAILED, error_msg
            )

    LOG.info("Queue processor stopped")


@app.post("/api/queue/start")
async def start_queue_processing():
    """Start processing the queue."""
    state = app.state.app_state

    with state.processor_lock:
        if state.processor_running:
            return {"success": True, "message": "Queue processor already running"}

        # Check if there are any queued jobs
        queued_jobs = state.queue_manager.get_queued_jobs()
        if not queued_jobs:
            raise HTTPException(status_code=400, detail="No jobs in queue to process")

        state.processor_running = True
        state.processor_thread = threading.Thread(
            target=process_queue, args=(state,), daemon=True
        )
        state.processor_thread.start()

        LOG.info("Queue processing started")
        return {"success": True, "message": "Queue processor started"}


@app.post("/api/queue/stop")
async def stop_queue_processing():
    """Stop processing the queue."""
    state = app.state.app_state

    with state.processor_lock:
        if not state.processor_running:
            return {"success": True, "message": "Queue processor not running"}

        state.processor_running = False

    # Wait for thread to finish (with timeout)
    if state.processor_thread and state.processor_thread.is_alive():
        state.processor_thread.join(timeout=5.0)

    LOG.info("Queue processing stopped")
    return {"success": True, "message": "Queue processor stopped"}


@app.get("/api/queue/status")
async def get_queue_status():
    """Get current queue processor status."""
    state = app.state.app_state
    return {
        "running": state.processor_running,
        "queued_count": len(state.queue_manager.get_queued_jobs()),
        "total_count": len(state.queue_manager.get_all_jobs()),
    }


@app.get("/api/queue/jobs")
async def get_all_jobs():
    """Get all jobs in the queue."""
    state = app.state.app_state
    jobs = state.queue_manager.get_all_jobs()
    return {"jobs": [serialize_job(job) for job in jobs]}


@app.post("/api/queue/add")
async def add_job_to_queue(request: AddJobRequest):
    """Add a new job to the queue."""
    try:
        LOG.debug(
            f"Adding job with {len(request.audio_tracks)} audio tracks and {len(request.subtitle_tracks)} subtitle tracks"
        )

        # build VideoState
        video_lang = None
        if request.video_language:
            try:
                video_lang = Iso639Language.match(request.video_language)
            except:
                pass

        video_state = VideoState(
            input_file=Path(request.video_file),
            language=video_lang,
            title=request.video_title or "",
            delay_ms=request.video_delay,
        )

        # build AudioStates
        audio_states = []
        for audio in request.audio_tracks:
            audio_lang = None
            if audio.get("language"):
                try:
                    audio_lang = Iso639Language.match(audio["language"])
                except:
                    pass

            audio_states.append(
                AudioState(
                    input_file=Path(audio["filePath"]),
                    language=audio_lang,
                    title=audio.get("title", ""),
                    delay_ms=audio.get("delay", 0),
                    default=audio.get("isDefault", False),
                    track_id=audio.get("trackId"),
                )
            )

        # build SubtitleStates
        subtitle_states = []
        for subtitle in request.subtitle_tracks:
            sub_lang = None
            if subtitle.get("language"):
                try:
                    sub_lang = Iso639Language.match(subtitle["language"])
                except:
                    pass

            subtitle_states.append(
                SubtitleState(
                    input_file=Path(subtitle["filePath"]),
                    language=sub_lang,
                    title=subtitle.get("title", ""),
                    default=subtitle.get("isDefault", False),
                    forced=subtitle.get("isForced", False),
                    track_id=subtitle.get("trackId"),
                )
            )

        # build ChapterState if chapters provided
        chapter_state = None
        if request.chapters:
            chapter_state = ChapterState(chapters=request.chapters)

        LOG.debug(
            f"Creating MuxJob with {len(audio_states)} audio states and {len(subtitle_states)} subtitle states"
        )

        # build MuxJob
        job = MuxJob(
            video=video_state,
            audio_tracks=audio_states,
            subtitle_tracks=subtitle_states,
            chapters=chapter_state,
            output_file=Path(request.output_file),
        )

        # add to queue
        state = app.state.app_state
        job_id = state.queue_manager.add_job(job)

        return {"success": True, "job_id": str(job_id), "job": serialize_job(job)}
    except Exception as e:
        LOG.error(f"Failed to add job: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/api/queue/clear-completed")
async def clear_completed_jobs():
    """Remove all completed/failed/cancelled jobs."""
    state = app.state.app_state
    state.queue_manager.clear_completed()
    return {"success": True}


@app.post("/api/queue/cancel/{job_id}")
async def cancel_job(job_id: str):
    """Cancel a specific job."""
    try:
        state = app.state.app_state
        uuid = UUID(job_id)
        state.queue_manager.cancel_job(uuid)
        return {"success": True}
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid job ID")
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.delete("/api/queue/remove/{job_id}")
async def remove_job(job_id: str):
    """Remove a specific job from queue."""
    try:
        state = app.state.app_state
        uuid = UUID(job_id)
        state.queue_manager.remove_job(uuid)
        return {"success": True}
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid job ID")
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/health")
async def health_check():
    """Health check endpoint for Docker."""
    return {"status": "healthy", "service": "mp4forge-api"}


# serve frontend static files (for production Docker deployment)
frontend_build_path = Path(__file__).parent.parent / "frontend_web" / "build"
if frontend_build_path.exists():
    # mount static assets
    app.mount(
        "/assets", StaticFiles(directory=frontend_build_path / "assets"), name="assets"
    )
    app.mount("/_app", StaticFiles(directory=frontend_build_path / "_app"), name="app")

    # serve index.html for all other routes (SPA routing)
    @app.get("/{full_path:path}")
    async def serve_frontend(full_path: str):
        """Serve the frontend application."""
        # if it's an API route, let FastAPI handle it
        if full_path.startswith("api/"):
            raise HTTPException(status_code=404, detail="API route not found")

        # otherwise serve the index.html
        index_file = frontend_build_path / "index.html"
        if index_file.exists():
            return FileResponse(index_file)
        raise HTTPException(status_code=404, detail="Frontend not found")
