"""Load application settings from environment variables and an optional .env."""

from __future__ import annotations

import os
from dataclasses import dataclass, field
from pathlib import Path

from dotenv import load_dotenv


PROJECT_ROOT = Path(__file__).resolve().parent.parent


@dataclass(frozen=True, slots=True)
class DatabaseSettings:
    """Connection settings for the application's MySQL account."""

    host: str
    port: int
    database: str
    user: str
    password: str = field(repr=False)


def load_database_settings() -> DatabaseSettings:
    """Return database settings or raise a clear error for missing/invalid values."""
    load_dotenv(PROJECT_ROOT / ".env")

    required = ("DB_HOST", "DB_NAME", "DB_USER", "DB_PASSWORD")
    missing = [key for key in required if not os.getenv(key)]
    if missing:
        names = ", ".join(missing)
        raise ValueError(f"Missing required database setting(s): {names}")

    raw_port = os.getenv("DB_PORT", "3306")
    try:
        port = int(raw_port)
    except ValueError as exc:
        raise ValueError("DB_PORT must be an integer") from exc
    if not 1 <= port <= 65535:
        raise ValueError("DB_PORT must be between 1 and 65535")

    return DatabaseSettings(
        host=os.environ["DB_HOST"],
        port=port,
        database=os.environ["DB_NAME"],
        user=os.environ["DB_USER"],
        password=os.environ["DB_PASSWORD"],
    )
