from pathlib import Path

UPLOAD_DIR = Path("uploads")
UPLOAD_DIR.mkdir(parents=True, exist_ok=True)

ALLOWED_CONTENT_TYPES = {
    "image/jpeg": ("jpg", "jpeg"),
    "image/png": ("png",),
}

MAX_FILE_SIZE = 5 * 1024 * 1024

OPTIMIZED_SUFFIX = "_opt"