from typing import Optional

from pydantic import BaseModel, Field


class HealthResponse(BaseModel):
    status: str
    model_version: str


class TilePredictRequest(BaseModel):
    tile_id: int = Field(ge=1, description="Tile id from Postgres")


class PredictionResponse(BaseModel):
    prediction: int
    confidence: float
    tile_id: Optional[int] = None
