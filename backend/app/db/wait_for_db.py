"""Block until the database accepts connections.

Run at container start (before migrations) so the API does not race Postgres. Uses the
sync URL with a plain psycopg-style connection via SQLAlchemy's create_engine, retrying
with backoff.
"""

from __future__ import annotations

import sys
import time

from sqlalchemy import create_engine, text
from sqlalchemy.exc import OperationalError

from app.core.config import settings


def wait(max_attempts: int = 30, delay_seconds: float = 1.0) -> None:
    # psycopg (v3) sync driver for the wait check; asyncpg is used by the app.
    url = settings.sync_database_url.replace("postgresql://", "postgresql+psycopg://")
    engine = create_engine(url, pool_pre_ping=True)
    for attempt in range(1, max_attempts + 1):
        try:
            with engine.connect() as conn:
                conn.execute(text("SELECT 1"))
            print(f"Database is ready (attempt {attempt}).")
            return
        except OperationalError as exc:
            print(f"Database not ready (attempt {attempt}/{max_attempts}): {exc}")
            time.sleep(delay_seconds)
    print("Database did not become ready in time.", file=sys.stderr)
    sys.exit(1)


if __name__ == "__main__":
    wait()
