import pytest
from httpx import AsyncClient
import io
from PIL import Image

from app.main import app
import app.utils as utils

@pytest.fixture(autouse=True)
def cleanup_tmp(tmp_path, monkeypatch):
    monkeypatch.setattr('app.config.UPLOAD_DIR', tmp_path)
    tmp_path.mkdir(exist_ok=True)
    yield

async def make_image_bytes(format='PNG', size=(100, 100)):
    b = io.BytesIO()
    img = Image.new('RGB', size, color=(255, 0, 0))
    img.save(b, format=format)
    return b.getvalue()

@pytest.mark.asyncio
async def test_upload_single_png():
    data = await make_image_bytes('PNG')
    async with AsyncClient(app=app, base_url='http://test') as ac:
        files = [('files', ('red.png', data, 'image/png'))]
        r = await ac.post('/upload', files=files)
    assert r.status_code == 200
    j = r.json()
    assert 'uploaded' in j
    assert len(j['uploaded']) == 1

@pytest.mark.asyncio
async def test_upload_reject_large():
    big = b'a' * (6 * 1024 * 1024)
    async with AsyncClient(app=app, base_url='http://test') as ac:
        files = [('files', ('big.jpg', big, 'image/jpeg'))]
        r = await ac.post('/upload', files=files)
    assert r.status_code == 413

@pytest.mark.asyncio
async def test_upload_reject_wrong_type():
    async with AsyncClient(app=app, base_url='http://test') as ac:
        files = [('files', ('f.png', b'notanimage', 'image/png'))]
        r = await ac.post('/upload', files=files)
    assert r.status_code == 400