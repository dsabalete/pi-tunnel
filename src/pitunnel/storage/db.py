"""Database connection and schema management for PiTunnel."""
from __future__ import annotations

import sqlite3
from contextlib import contextmanager
from pathlib import Path
from typing import Iterator, Optional

from pitunnel.core.config import Config


class Database:
    """Manages SQLite database connection, schema migrations, and WAL mode."""

    # Schema migrations: list of (version, sql_statement) tuples
    # Version 0 = empty database
    # Version 1 = schema_version table (handled separately in _run_migrations)
    MIGRATIONS = [
        (
            2,
            """
            CREATE TABLE IF NOT EXISTS command_history (
                ts REAL NOT NULL,
                user_id INTEGER NOT NULL,
                alias TEXT NOT NULL,
                args TEXT,
                exit_code INTEGER,
                stdout TEXT,
                stderr TEXT
            );
            CREATE INDEX IF NOT EXISTS idx_command_history_ts ON command_history (ts DESC);
            """,
        ),
    ]

    def __init__(self, config: Config) -> None:
        self.config = config
        self._db_path = self._resolve_db_path()
        self._conn: Optional[sqlite3.Connection] = None

    def _resolve_db_path(self) -> Path:
        """Resolve database file path from config."""
        # Check if storage section exists in config
        storage_cfg = getattr(self.config, "storage", None)
        if storage_cfg and storage_cfg.get("database_path"):
            return Path(storage_cfg["database_path"])
        # Default: /app/data/db.sqlite3 (Docker) or db.sqlite3 (native)
        data_dir = Path("/app/data")
        if data_dir.exists():
            return data_dir / "db.sqlite3"
        return Path("db.sqlite3")

    def connect(self) -> sqlite3.Connection:
        """Create a new SQLite connection with WAL mode enabled."""
        conn = sqlite3.connect(self._db_path)
        conn.row_factory = sqlite3.Row
        # Enable WAL mode for better concurrency
        conn.execute("PRAGMA journal_mode=WAL")
        # Enable foreign keys
        conn.execute("PRAGMA foreign_keys=ON")
        return conn

    @contextmanager
    def get_connection(self) -> Iterator[sqlite3.Connection]:
        """Context manager for database connections.

        Ensures connections are properly closed after use.
        """
        conn = self.connect()
        try:
            yield conn
            conn.commit()
        except Exception:
            conn.rollback()
            raise
        finally:
            conn.close()

    def init_schema(self) -> None:
        """Initialize database schema and run migrations."""
        with self.get_connection() as conn:
            self._run_migrations(conn)

    def _run_migrations(self, conn: sqlite3.Connection) -> None:
        """Apply all pending migrations."""
        # Ensure schema_version table exists first
        conn.executescript(
            """
            CREATE TABLE IF NOT EXISTS schema_version (
                version INTEGER NOT NULL DEFAULT 0
            );
            INSERT OR IGNORE INTO schema_version (version) VALUES (0);
            """
        )
        # Get current schema version
        cursor = conn.execute("SELECT version FROM schema_version")
        row = cursor.fetchone()
        current_version = row[0] if row else 0

        # Apply migrations (skip version 1 which is schema_version creation)
        for version, sql in self.MIGRATIONS:
            if version > current_version and version > 1:
                conn.executescript(sql)
                # Update version
                conn.execute("UPDATE schema_version SET version = ?", (version,))
                current_version = version

    def get_schema_version(self) -> int:
        """Get current schema version."""
        with self.get_connection() as conn:
            cursor = conn.execute("SELECT version FROM schema_version")
            row = cursor.fetchone()
            return row[0] if row else 0

    def wal_checkpoint(self, mode: str = "TRUNCATE") -> None:
        """Checkpoint the WAL file to control its size.

        Args:
            mode: Checkpoint mode (PASSIVE, FULL, RESTART, TRUNCATE)
        """
        with self.get_connection() as conn:
            conn.execute(f"PRAGMA wal_checkpoint({mode})")

    def close(self) -> None:
        """Close any cached connection."""
        if self._conn is not None:
            self._conn.close()
            self._conn = None