import io
import os
from typing import Optional

import requests
from PIL import Image


def load_image_from_uri(uri: str, max_bytes: int = 3 * 1024 * 1024) -> Image.Image:
    if uri.startswith("http://") or uri.startswith("https://"):
        return _load_from_url(uri, max_bytes=max_bytes)
    return _load_from_file(uri)


def _load_from_file(path: str) -> Image.Image:
    if not os.path.exists(path):
        raise FileNotFoundError(f"Image not found: {path}")
    img = Image.open(path)
    img = img.convert("RGB")
    return img


def _load_from_url(url: str, max_bytes: int) -> Image.Image:
    response = requests.get(url, stream=True, timeout=10)
    response.raise_for_status()

    content = bytearray()
    for chunk in response.iter_content(chunk_size=8192):
        content.extend(chunk)
        if len(content) > max_bytes:
            raise ValueError("Image exceeds size limit")

    img = Image.open(io.BytesIO(content))
    img = img.convert("RGB")
    return img
