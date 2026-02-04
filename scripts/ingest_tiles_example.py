import csv

from gee_flood.data.tiles_repo import insert_tiles


def load_csv(path: str):
    rows = []
    with open(path, "r", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        for row in reader:
            split = row.get("split")
            split = split if split else None
            rows.append(
                {
                    "image_uri": row["image_uri"],
                    "lat": float(row["lat"]),
                    "lon": float(row["lon"]),
                    "date": row["date"],
                    "label": int(row["label"]),
                    "split": split,
                }
            )
    return rows


if __name__ == "__main__":
    # TODO: Create a CSV from your GEE export metadata and run this script.
    # Why it matters: ingestion proves you can move data from GEE to Postgres.
    csv_path = "data\\tile_metadata.csv"
    tiles = load_csv(csv_path)
    count = insert_tiles(tiles)
    print(f"Inserted {count} tiles.")
