from .common import ReadModel


class FileRead(ReadModel):
    id: int
    url: str
    mime_type: str
    size_bytes: int
