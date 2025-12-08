from pathlib import Path

from fastapi import FastAPI, WebSocket

from core.muxer import ProgressCallback, VideoMuxer

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


@app.get("/")
async def root():
    return {"message": "Video Muxer API"}


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

    with concurrent.futures.ThreadPoolExecutor() as executor:
        await asyncio.get_event_loop().run_in_executor(
            executor, muxer.mux_video, files, output
        )


# Run with: uvicorn backend.main:app --reload
