from pathlib import Path

from fastapi import FastAPI, HTTPException, WebSocket

from backend.schemas import BrowseRequest, LogRequest, MediaInfoRequest
from core.logger import LOG, LogLevel
from core.muxer import ProgressCallback, VideoMuxer
from core.utils.file_utils import browse_directory
from core.utils.mediainfo import get_media_info_web

app = FastAPI()


class WebSocketCallback(ProgressCallback):
    """Send progress via WebSocket"""

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
        target_path = Path(request.path) if request.path else None
        result = browse_directory(target_path)
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


@app.websocket("/ws/jobs")
async def job_websocket(websocket: WebSocket):
    await websocket.accept()

    callback = WebSocketCallback(websocket)
    muxer = VideoMuxer(progress_callback=callback)

    # Get job params
    data = await websocket.receive_json()
    files = [Path(f) for f in data.get("files", [])]
    output = Path(data.get("output", "output.mp4"))

    # Run in thread pool
    import asyncio
    import concurrent.futures

    # Note: This is a placeholder - actual implementation would need MuxJob
    # For now, just accepting the websocket connection
    await websocket.send_json(
        {"type": "error", "error": "Job processing not yet implemented"}
    )
