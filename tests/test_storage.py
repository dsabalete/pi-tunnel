"""Tests for storage module."""
from __future__ import annotations

import time

import pytest

from pitunnel.storage.db import Database
from pitunnel.storage.history import History


@pytest.fixture
def temp_db():
    """Create a temporary database for testing."""
    import tempfile
    import os

    with tempfile.NamedTemporaryFile(suffix=".db", delete=False) as f:
        db_path = f.name
    os.unlink(db_path)

    class MockConfig:
        storage = {"database_path": db_path}
        telegram = type("obj", (object,), {"authorized_users": [123], "language": "en"})()
        limits = type("obj", (object,), {"command_timeout_s": 10, "max_output_chars": 4000, "history_retention_days": 30})()
        commands = type("obj", (object,), {"aliases": {}})()

    db = Database(MockConfig())
    db.init_schema()
    yield db, History(db)
    db.close()


def test_database_migrations(temp_db):
    """Test that database migrations run correctly."""
    db, _ = temp_db
    # Schema should be at version 2
    assert db.get_schema_version() == 2

    # Verify tables exist
    with db.get_connection() as conn:
        tables = conn.execute(
            "SELECT name FROM sqlite_master WHERE type='table'"
        ).fetchall()
        table_names = [t[0] for t in tables]
        assert "schema_version" in table_names
        assert "command_history" in table_names


def test_migration_idempotent(temp_db):
    """Test that running migrations twice doesn't change schema version."""
    db, _ = temp_db
    assert db.get_schema_version() == 2

    # Re-run init_schema
    db.init_schema()
    assert db.get_schema_version() == 2


def test_wal_mode_enabled(temp_db):
    """Test that WAL mode is enabled on database connections."""
    db, _ = temp_db
    with db.get_connection() as conn:
        cursor = conn.execute("PRAGMA journal_mode")
        result = cursor.fetchone()
        assert result[0].lower() == "wal"


def test_history_log_command(temp_db):
    """Test logging and retrieving command history."""
    _, history = temp_db

    row_id = history.log_command(
        user_id=12345,
        alias="test-cmd",
        args="arg1 arg2",
        exit_code=0,
        stdout="output",
        stderr="",
    )
    assert row_id > 0

    entries = history.get_history(limit=10)
    assert len(entries) == 1
    assert entries[0]["user_id"] == 12345
    assert entries[0]["alias"] == "test-cmd"
    assert entries[0]["args"] == "arg1 arg2"
    assert entries[0]["exit_code"] == 0
    assert entries[0]["stdout"] == "output"
    assert entries[0]["stderr"] == ""


def test_purge_older_than(temp_db):
    """Test purging old history entries."""
    _, history = temp_db

    # Log some entries with old timestamps
    old_ts = time.time() - (31 * 86400)  # 31 days ago

    # Use direct SQL to insert old timestamps
    import sqlite3
    with temp_db[0].get_connection() as conn:
        conn.execute(
            "INSERT INTO command_history (ts, user_id, alias) VALUES (?, ?, ?)",
            (old_ts, 1, "old-cmd"),
        )

    # Log current entries
    from pitunnel.storage.history import History
    h = History(temp_db[0])
    h.log_command(user_id=1, alias="new-cmd")

    # Purge entries older than 30 days
    deleted = temp_db[1].purge_older_than(30)

    # Should have deleted 1 old entry
    assert deleted == 1

    # Verify new entries remain
    with temp_db[0].get_connection() as conn:
        cmd_count = conn.execute("SELECT COUNT(*) FROM command_history").fetchone()[0]
        assert cmd_count == 1