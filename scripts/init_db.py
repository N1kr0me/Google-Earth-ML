from gee_flood.data.db import init_db


if __name__ == "__main__":
    # TODO: Run after Postgres is available.
    # Why it matters: initializing tables shows you can own database schema setup.
    init_db()
    print("Database initialized.")
