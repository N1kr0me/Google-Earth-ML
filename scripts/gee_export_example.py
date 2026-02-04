import csv
from typing import List

import ee

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


if __name__ == "__main__":
    # TODO: Run authentication locally before any GEE usage.
    # Why it matters: proves you can safely access remote imagery sources.
    authenticate_and_initialize()

    # TODO: Define your region of interest and date range.
    # Why it matters: selection impacts data quality and model performance.
    geometry = ee.Geometry.Rectangle([72.75, 18.9, 72.95, 19.1])
    start_date = "2020-07-01"
    end_date = "2020-07-31"

    collection = get_sentinel2_collection(geometry, start_date, end_date)
    image = build_water_index(collection.median())

    # TODO: Replace sample_tiles with real export jobs.
    # Why it matters: exporting tiles is the core data engineering step.
    rows = sample_tiles(geometry, start_date, end_date, scale_m=10, max_tiles=50)

    export_metadata_to_csv(rows, "data\\tile_metadata.csv")
    print("Wrote metadata to data\\tile_metadata.csv")
