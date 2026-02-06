import io
import logging
import os
from typing import Optional

import requests
from fastapi import FastAPI, File, Form, HTTPException, Request, UploadFile
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from PIL import Image
from slowapi import Limiter
from slowapi.errors import RateLimitExceeded
from slowapi.util import get_remote_address

from gee_flood.api.schemas import HealthResponse, PredictionResponse, TilePredictRequest
from gee_flood.model.inference import load_model, predict_by_tile_id, predict_pil


app = FastAPI(title="GEE-Flood API", version="0.1.0")

limiter = Limiter(key_func=get_remote_address)
app.state.limiter = limiter

logging.basicConfig(level=os.getenv("LOG_LEVEL", "INFO"))
logger = logging.getLogger("gee_flood_api")


@app.exception_handler(RateLimitExceeded)
def rate_limit_handler(request: Request, exc: RateLimitExceeded):
    # Security: return a generic rate-limit message to avoid leaking internals.
    return JSONResponse(status_code=429, content={"detail": "Rate limit exceeded"})


@app.exception_handler(RequestValidationError)
def validation_handler(request: Request, exc: RequestValidationError):
    # Security: avoid returning stack traces or raw exceptions to clients.
    return JSONResponse(status_code=422, content={"detail": "Invalid request"})


@app.exception_handler(Exception)
def unhandled_exception_handler(request: Request, exc: Exception):
    # Security: log server-side for debugging but return safe messages to clients.
    logger.exception("Unhandled error")
    return JSONResponse(status_code=500, content={"detail": "Internal server error"})


def _allowed_types() -> set:
    types = os.getenv("ALLOWED_IMAGE_TYPES", "image/jpeg,image/png")
    return set(t.strip() for t in types.split(",") if t.strip())


def _max_image_bytes() -> int:
    return int(os.getenv("MAX_IMAGE_BYTES", "3145728"))


def _validate_image_content(image_bytes: bytes, content_type: str) -> Image.Image:
    # Security: enforce content type and size limits to prevent abuse.
    if content_type not in _allowed_types():
        raise HTTPException(status_code=400, detail="Unsupported image type")
    if len(image_bytes) > _max_image_bytes():
        raise HTTPException(status_code=413, detail="Image too large")

    try:
        img = Image.open(io.BytesIO(image_bytes))
        img.verify()
        img = Image.open(io.BytesIO(image_bytes))
        return img.convert("RGB")
    except Exception as exc:
        raise HTTPException(status_code=400, detail="Invalid image") from exc


def _fetch_image_from_url(url: str) -> Image.Image:
    # Security: use timeouts and size limits for remote content.
    try:
        response = requests.get(url, stream=True, timeout=10)
        response.raise_for_status()
    except Exception as exc:
        raise HTTPException(status_code=400, detail="Invalid URL") from exc

    content_type = response.headers.get("Content-Type", "")
    if content_type:
        content_type = content_type.split(";")[0].strip()

    data = bytearray()
    for chunk in response.iter_content(chunk_size=8192):
        data.extend(chunk)
        if len(data) > _max_image_bytes():
            raise HTTPException(status_code=413, detail="Image too large")

    return _validate_image_content(bytes(data), content_type or "application/octet-stream")


@app.get("/health", response_model=HealthResponse)
@limiter.limit("30/minute")
def health() -> HealthResponse:
    model_version = os.getenv("MODEL_VERSION", "unknown")
    return HealthResponse(status="ok", model_version=model_version)


@app.post("/predict_tile", response_model=PredictionResponse)
@limiter.limit("10/minute")
def predict_tile(request: TilePredictRequest) -> PredictionResponse:
    try:
        result = predict_by_tile_id(request.tile_id)
    except ValueError:
        # Security: avoid leaking internal DB details in error responses.
        raise HTTPException(status_code=404, detail="Tile not found")
    return PredictionResponse(**result, tile_id=request.tile_id)


@app.post("/predict_image", response_model=PredictionResponse)
@limiter.limit("10/minute")
def predict_image(
    image_url: Optional[str] = Form(default=None),
    file: Optional[UploadFile] = File(default=None),
) -> PredictionResponse:
    if not image_url and not file:
        raise HTTPException(status_code=400, detail="Provide image_url or file")

    artifact_path = os.getenv("MODEL_ARTIFACT_PATH", "artifacts/model_v1/model.pt")
    model, config = load_model(artifact_path)

    if image_url:
        # Security: validate URL input and remote content.
        image = _fetch_image_from_url(image_url)
        result = predict_pil(model, config, image)
        return PredictionResponse(**result)

    content_type = file.content_type or ""
    data = file.file.read()
    image = _validate_image_content(data, content_type)
    result = predict_pil(model, config, image)
    return PredictionResponse(**result)
