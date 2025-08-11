from fastapi import FastAPI, UploadFile, File, BackgroundTasks, Depends, HTTPException
from typing import List
from pathlib import Path
import asyncio
import os

from .config import UPLOAD_DIR, MAX_FILE_SIZE, OPTIMIZED_SUFFIX
from .utils import validate_image_file, secure_uuid_filename, save_bytes_to_file
from .image_processing import optimize_image_bytes
from .schemas import UploadResponse, FileItem
from .auth import fake_current_user

app = FastAPI(title="Art Gallery Image Upload API")

@app.post("/upload", response_model=UploadResponse)
async def upload_images(
    files: List[UploadFile] = File(...),
    background_tasks: BackgroundTasks = Depends(),
    current_user: dict = Depends(fake_current_user),
):
    if not files:
        raise HTTPException(status_code=400, detail="No files uploaded")

    saved = []
    loop = asyncio.get_running_loop()

    for upload in files:
        data, ext = await validate_image_file(upload, MAX_FILE_SIZE)
        filename = secure_uuid_filename(upload.filename, ext)
        dest_path = UPLOAD_DIR / filename

        # Запис файлу у фоні через executor, щоб не блокувати event loop на довгих писаннях
        await loop.run_in_executor(None, save_bytes_to_file, data, dest_path)

        # Додаємо таску оптимізації у BackgroundTasks (виконається після відповіді)
        background_tasks.add_task(_background_optimize, dest_path)

        saved.append(FileItem(id=filename.rsplit('.', 1)[0], filename=filename, url=f"/files/{filename}"))

    return UploadResponse(uploaded=saved)

@app.get("/files/{fname}")
async def serve_file(fname: str):
    # Проста валідація і доставка файлу. У продакшні — підписані URL/CDN.
    parts = fname.split('.')
    if len(parts) != 2:
        raise HTTPException(status_code=400, detail="Invalid filename")
    uid, ext = parts
    if len(uid) != 32 or any(c not in '0123456789abcdef' for c in uid):
        raise HTTPException(status_code=400, detail="Invalid file id")
    path = UPLOAD_DIR / fname
    if not path.exists():
        raise HTTPException(status_code=404, detail="File not found")
    return fastapi.responses.FileResponse(path)

# Функція, яку ми додаємо у BackgroundTasks
async def _background_optimize(path: Path):
    try:
        loop = asyncio.get_running_loop()
        data = await loop.run_in_executor(None, path.read_bytes)
        new_data, new_ext = await loop.run_in_executor(None, optimize_image_bytes, data)
        opt_name = path.with_name(path.stem + OPTIMIZED_SUFFIX + '.' + new_ext)
        await loop.run_in_executor(None, save_bytes_to_file, new_data, opt_name)
        os.chmod(opt_name, 0o644)
    except Exception as exc:
        # У продакшні логувати через logger
        print(f"Background optimization failed for {path}: {exc}")