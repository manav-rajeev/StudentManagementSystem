"""Create MySQL connections using the application's environment settings."""

from __future__ import annotations

import mysql.connector
from mysql.connector import MySQLConnection

from config.settings import load_database_settings


def create_connection() -> MySQLConnection:
    """Open a connection to the configured application database.

    Callers own the returned connection and should close it with a context
    manager or explicitly. The connector's parameter binding is used by the
    repository layer for all values in SQL statements.
    """
    settings = load_database_settings()
    return mysql.connector.connect(
        host=settings.host,
        port=settings.port,
        database=settings.database,
        user=settings.user,
        password=settings.password,
        charset="utf8mb4",
        use_unicode=True,
        connection_timeout=5,
    )
