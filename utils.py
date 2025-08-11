import imghdr
import io
import os
from pathlib import Path
from uuid import uuid4
from fastapi import HTTPException, UploadFile
from typing import Tuple
from .config import ALLOWED_CONTENT_TYPES, MAX_FILE_SIZE

def secure_uuid_filename(original_name: str, ext: str) -> str:
    return f"{uuid4().hex}.{ext}"

def save_bytes_to_file(data: bytes, dest: Path) -> None:
    temp = dest.with_suffix(dest.suffix + ".tmp")
    with open(temp, "wb") as f:
        f.write(data)
        f.flush()
        os.fsync(f.fileno())
    temp.replace(dest)

def detect_image_type(bytestr: bytes) -> str:
    return imghdr.what(None, h=bytestr)

async def read_upload_file_bytes(upload_file: UploadFile, max_bytes: int) -> bytes:
    data = await upload_file.read()
    if len(data) > max_bytes:
        raise HTTPException(status_code=413, detail=f"File too large (max {max_bytes} bytes)")
    return data

async def validate_image_file(upload_file: UploadFile, max_size: int) -> Tuple[bytes, str]:
    content_type = upload_file.content_type
    if content_type not in ALLOWED_CONTENT_TYPES:
        raise HTTPException(status_code=400, detail=f"Unsupported content type: {content_type}")

    data = await read_upload_file_bytes(upload_file, max_size)
    kind = detect_image_type(data)
    if kind is None:
        raise HTTPException(status_code=400, detail="Cannot detect image type (corrupted or unsupported)")

    if kind == "jpeg":
        ext = "jpg"
    elif kind == "png":
        ext = "png"
    else:
        raise HTTPException(status_code=400, detail=f"Unsupported image kind detected: {kind}")

    if ext not in ALLOWED_CONTENT_TYPES[content_type]:
        raise HTTPException(status_code=400, detail=f"Content-type header ({content_type}) does not match file signature ({ext})")

    return data, ext