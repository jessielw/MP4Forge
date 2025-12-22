from pydantic import BaseModel

from core.logger import LogLevel


class LogRequest(BaseModel):
    message: str
    level: LogLevel


class BrowseRequest(BaseModel):
    path: str | None = None


class MediaInfoRequest(BaseModel):
    file_path: str


class ExtractChaptersRequest(BaseModel):
    file_path: str


class ReadFileRequest(BaseModel):
    file_path: str


class AddJobRequest(BaseModel):
    video_file: str
    video_language: str | None = None
    video_title: str | None = None
    video_delay: int = 0
    audio_tracks: list[dict] = []
    subtitle_tracks: list[dict] = []
    chapters: str | None = None
    output_file: str
