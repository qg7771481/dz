from pydantic import BaseModel
from typing import List

class FileItem(BaseModel):
    id: str
    filename: str
    url: str

class UploadResponse(BaseModel):
    uploaded: List[FileItem]