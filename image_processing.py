from PIL import Image
import io
from typing import Tuple

def optimize_image_bytes(data: bytes, max_width: int = 1920) -> Tuple[bytes, str]:
    img = Image.open(io.BytesIO(data))
    img_format = img.format

    if img.width > max_width:
        ratio = max_width / float(img.width)
        new_height = int(img.height * ratio)
        img = img.resize((max_width, new_height), Image.LANCZOS)

    out = io.BytesIO()
    if img_format == "JPEG":
        img.save(out, format="JPEG", quality=85, optimize=True)
        new_ext = "jpg"
    else:
        img.save(out, format="PNG", optimize=True)
        new_ext = "png"
    return out.getvalue(), new_ext