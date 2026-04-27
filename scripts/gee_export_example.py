import csv
import os
import sys
from typing import List
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from PIL import Image, ImageDraw
try:
    import ee
except Exception:  # pragma: no cover - optional runtime dependency
    ee = None

from gee_flood.data.gee_client import (
    authenticate_and_initialize,
    build_water_index,
    get_sentinel2_collection,
    sample_tiles,
)


def export_metadata_to_csv(rows: List[dict], path: str) -> None:
    with open(path, "w", encoding="utf-8", newline="") as f:
        writer = csv.DictWriter(
            f, fieldnames=["image_uri", "lat", "lon", "date", "label", "split"]
        )
        writer.writeheader()
        writer.writerows(rows)


def create_placeholder_tiles(rows: List[dict]) -> None:
    tiles_dir = os.path.join("data", "tiles")
    os.makedirs(tiles_dir, exist_ok=True)
    for row in rows:
        tile_path = row["image_uri"]
        if os.path.exists(tile_path):
            continue
        img = Image.new("RGB", (64, 64), (40, 80, 120))
        draw = ImageDraw.Draw(img)
        if row["label"] == 1:
            draw.rectangle((8, 24, 56, 56), fill=(40, 120, 220))
        else:
            draw.rectangle((8, 8, 56, 40), fill=(90, 140, 90))
        img.save(tile_path)


if __name__ == "__main__":
    start_date = "2020-07-01"
    end_date = "2020-07-31"
    try:
        if ee is None:
            raise RuntimeError("Earth Engine SDK unavailable")
        authenticate_and_initialize()
        geometry = ee.Geometry.Rectangle([72.75, 18.9, 72.95, 19.1])
        collection = get_sentinel2_collection(geometry, start_date, end_date)
        _ = build_water_index(collection.median())
        rows = sample_tiles(geometry, start_date, end_date, scale_m=10, max_tiles=50)
    except Exception:
        # Fallback keeps local MVP runnable even when GEE auth isn't set up yet.
        rows = []
        for idx in range(50):
            rows.append(
                {
                    "image_uri": os.path.join("data", "tiles", f"tile_{idx:04d}.png"),
                    "lat": 19.0 + idx * 0.0001,
                    "lon": 72.8 + idx * 0.0001,
                    "date": start_date,
                    "label": 1 if idx % 2 == 0 else 0,
                    "split": None,
                }
            )
    create_placeholder_tiles(rows)

    metadata_path = os.path.join("data", "tile_metadata.csv")
    export_metadata_to_csv(rows, metadata_path)
    print(f"Wrote metadata to {metadata_path}")
