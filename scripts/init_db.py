import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from gee_flood.data.db import init_db


if __name__ == "__main__":
    # TODO: Run after Postgres is available.
    # Why it matters: initializing tables shows you can own database schema setup.
    init_db()
    print("Database initialized.")
