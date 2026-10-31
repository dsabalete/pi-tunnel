"""History and persistence API for PiTunnel."""

from __future__ import annotations

import sqlite3
import time
from typing import Any

from pitunnel.storage.db import Database


class History:
    """High-level API for logging and querying command, sensor, and alert history."""

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

    def log_sensor_reading(
        self,
        ts: float | None = None,
        sensor_id: str = "",
        value: float = 0.0,
        unit: str = "",
    ) -> int:
        """Log a sensor reading to the database.

        Returns the row ID of the inserted record.
        """
        if ts is None:
            ts = time.time()
        with self.db.get_connection() as conn:
            cursor = conn.execute(
                """
                INSERT INTO sensor_readings (ts, sensor_id, value, unit)
                VALUES (?, ?, ?, ?)
                """,
                (ts, sensor_id, value, unit),
            )
            return cursor.lastrowid

    def get_readings(
        self, sensor_id: str, since_ts: float | None = None
    ) -> list[dict[str, Any]]:
        """Get sensor readings for a specific sensor, optionally since a timestamp.

        Returns list of dicts ordered by timestamp descending.
        """
        with self.db.get_connection() as conn:
            if since_ts is not None:
                cursor = conn.execute(
                    """
                    SELECT ts, sensor_id, value, unit
                    FROM sensor_readings
                    WHERE sensor_id = ? AND ts >= ?
                    ORDER BY ts DESC
                    """,
                    (sensor_id, since_ts),
                )
            else:
                cursor = conn.execute(
                    """
                    SELECT ts, sensor_id, value, unit
                    FROM sensor_readings
                    WHERE sensor_id = ?
                    ORDER BY ts DESC
                    """,
                    (sensor_id,),
                )
            return [dict(row) for row in cursor.fetchall()]

    def log_alert(
        self,
        ts: float | None = None,
        rule_id: str = "",
        sensor_id: str = "",
        value: float = 0.0,
    ) -> int:
        """Log an alert event to the database.

        Returns the row ID of the inserted record.
        """
        if ts is None:
            ts = time.time()
        with self.db.get_connection() as conn:
            cursor = conn.execute(
                """
                INSERT INTO alert_history (ts, rule_id, sensor_id, value)
                VALUES (?, ?, ?, ?)
                """,
                (ts, rule_id, sensor_id, value),
            )
            return cursor.lastrowid

    def get_last_alert_ts(self, rule_id: str) -> float | None:
        """Get the timestamp of the last alert for a rule.

        Returns None if no alert found for the rule.
        """
        with self.db.get_connection() as conn:
            cursor = conn.execute(
                """
                SELECT ts FROM alert_history
                WHERE rule_id = ?
                ORDER BY ts DESC
                LIMIT 1
                """,
                (rule_id,),
            )
            row = cursor.fetchone()
            return row[0] if row else None

    def purge_older_than(self, days: int = 30) -> int:
        """Delete history entries older than the specified number of days.

        Returns the total number of rows deleted across all tables.
        """
        cutoff_ts = time.time() - (days * 86400)
        total_deleted = 0

        with self.db.get_connection() as conn:
            # Purge command_history
            cursor = conn.execute(
                "DELETE FROM command_history WHERE ts < ?", (cutoff_ts,)
            )
            total_deleted += cursor.rowcount

            # Purge sensor_readings
            cursor = conn.execute(
                "DELETE FROM sensor_readings WHERE ts < ?", (cutoff_ts,)
            )
            total_deleted += cursor.rowcount

            # Purge alert_history
            cursor = conn.execute(
                "DELETE FROM alert_history WHERE ts < ?", (cutoff_ts,)
            )
            total_deleted += cursor.rowcount

        # Checkpoint WAL to control file size (separate connection to avoid lock)
        try:
            self.db.wal_checkpoint("TRUNCATE")
        except sqlite3.OperationalError:
            # Ignore if database is locked
            pass

        return total_deleted