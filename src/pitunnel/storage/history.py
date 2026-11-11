"""History and persistence API for PiTunnel."""
from __future__ import annotations

import sqlite3
import time
from typing import Any

from pitunnel.storage.db import Database


class History:
    """High-level API for logging and querying command history."""

    def __init__(self, database: Database) -> None:
        self.db = database

    def log_command(
        self,
        ts: float | None = None,
        user_id: int = 0,
        alias: str = "",
        args: str = "",
        exit_code: int = 0,
        stdout: str = "",
        stderr: str = "",
    ) -> int:
        """Log a command execution to the database.

        Returns the row ID of the inserted record.
        """
        if ts is None:
            ts = time.time()
        with self.db.get_connection() as conn:
            cursor = conn.execute(
                """
                INSERT INTO command_history (ts, user_id, alias, args, exit_code, stdout, stderr)
                VALUES (?, ?, ?, ?, ?, ?, ?)
                """,
                (ts, user_id, alias, args, exit_code, stdout, stderr),
            )
            return cursor.lastrowid

    def get_history(self, limit: int = 10) -> list[dict[str, Any]]:
        """Get the most recent command history entries.

        Returns list of dicts ordered by timestamp descending.
        """
        with self.db.get_connection() as conn:
            cursor = conn.execute(
                """
                SELECT ts, user_id, alias, args, exit_code, stdout, stderr
                FROM command_history
                ORDER BY ts DESC
                LIMIT ?
                """,
                (limit,),
            )
            return [dict(row) for row in cursor.fetchall()]

    def purge_older_than(self, days: int = 30) -> int:
        """Delete history entries older than the specified number of days.

        Returns the total number of rows deleted.
        """
        cutoff_ts = time.time() - (days * 86400)
        total_deleted = 0

        with self.db.get_connection() as conn:
            # Purge command_history
            cursor = conn.execute(
                "DELETE FROM command_history WHERE ts < ?", (cutoff_ts,)
            )
            total_deleted += cursor.rowcount

        # Checkpoint WAL to control file size (separate connection to avoid lock)
        try:
            self.db.wal_checkpoint("TRUNCATE")
        except sqlite3.OperationalError:
            # Ignore if database is locked
            pass

        return total_deleted