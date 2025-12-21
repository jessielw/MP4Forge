from pydantic import BaseModel

from core.logger import LogLevel


class LogRequest(BaseModel):
    message: str
    level: LogLevel


class BrowseRequest(BaseModel):
    path: str | None = None


class MediaInfoRequest(BaseModel):
    file_path: str
