"""Tests for storage module."""

import time
from unittest.mock import patch

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
        sensors = []
        actuators = []
        alerts = type("obj", (object,), {"rules": []})()

    db = Database(MockConfig())
    db.init_schema()
    yield db, History(db)
    db.close()


def test_database_migrations(temp_db):
    """Test that database migrations run correctly."""
    db, _ = temp_db
    # Schema should be at version 4
    assert db.get_schema_version() == 4

    # Verify tables exist
    with db.get_connection() as conn:
        tables = conn.execute(
            "SELECT name FROM sqlite_master WHERE type='table'"
        ).fetchall()
        table_names = [t[0] for t in tables]
        assert "schema_version" in table_names
        assert "command_history" in table_names
        assert "sensor_readings" in table_names
        assert "alert_history" in table_names


def test_migration_idempotent(temp_db):
    """Test that running migrations twice doesn't change schema version."""
    db, _ = temp_db
    assert db.get_schema_version() == 4

    # Re-run init_schema
    db.init_schema()
    assert db.get_schema_version() == 4


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


def test_history_log_sensor_reading(temp_db):
    """Test logging and retrieving sensor readings."""
    _, history = temp_db

    row_id = history.log_sensor_reading(
        sensor_id="temp-salon",
        value=25.5,
        unit="C",
    )
    assert row_id > 0

    readings = history.get_readings("temp-salon")
    assert len(readings) == 1
    assert readings[0]["sensor_id"] == "temp-salon"
    assert readings[0]["value"] == 25.5
    assert readings[0]["unit"] == "C"


def test_history_log_alert(temp_db):
    """Test logging and retrieving alert history."""
    _, history = temp_db

    row_id = history.log_alert(
        rule_id="temp-high",
        sensor_id="temp-salon",
        value=30.0,
    )
    assert row_id > 0

    last_ts = history.get_last_alert_ts("temp-high")
    assert last_ts is not None
    assert last_ts > 0


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
        conn.execute(
            "INSERT INTO sensor_readings (ts, sensor_id, value) VALUES (?, ?, ?)",
            (old_ts, "old-sensor", 10.0),
        )
        conn.execute(
            "INSERT INTO alert_history (ts, rule_id, sensor_id, value) VALUES (?, ?, ?, ?)",
            (old_ts, "old-rule", "old-sensor", 100.0),
        )

    # Log current entries
    from pitunnel.storage.history import History
    h = History(temp_db[0])
    h.log_command(user_id=1, alias="new-cmd")
    h.log_sensor_reading(sensor_id="new-sensor", value=20.0)
    h.log_alert(rule_id="new-rule", sensor_id="new-sensor", value=50.0)

    # Purge entries older than 30 days
    deleted = temp_db[1].purge_older_than(30)

    # Should have deleted 3 old entries
    assert deleted == 3

    # Verify new entries remain
    with temp_db[0].get_connection() as conn:
        cmd_count = conn.execute("SELECT COUNT(*) FROM command_history").fetchone()[0]
        sensor_count = conn.execute("SELECT COUNT(*) FROM sensor_readings").fetchone()[0]
        alert_count = conn.execute("SELECT COUNT(*) FROM alert_history").fetchone()[0]
        assert cmd_count == 1
        assert sensor_count == 1
        assert alert_count == 1


def test_get_readings_with_since_ts(temp_db):
    """Test get_readings with since_ts filter."""
    _, history = temp_db

    ts1 = time.time() - 100
    ts2 = time.time() - 50
    ts3 = time.time()

    with temp_db[0].get_connection() as conn:
        conn.execute(
            "INSERT INTO sensor_readings (ts, sensor_id, value) VALUES (?, ?, ?)",
            (ts1, "sensor1", 10.0),
        )
        conn.execute(
            "INSERT INTO sensor_readings (ts, sensor_id, value) VALUES (?, ?, ?)",
            (ts2, "sensor1", 20.0),
        )
        conn.execute(
            "INSERT INTO sensor_readings (ts, sensor_id, value) VALUES (?, ?, ?)",
            (ts3, "sensor1", 30.0),
        )

    # Get readings since ts2
    readings = temp_db[1].get_readings("sensor1", since_ts=ts2 + 1)
    assert len(readings) == 1
    assert readings[0]["value"] == 30.0

    # Get readings since ts1
    readings = temp_db[1].get_readings("sensor1", since_ts=ts1 + 1)
    assert len(readings) == 2


def test_alert_cooldown_logic(temp_db):
    """Test alert cooldown logic using get_last_alert_ts."""
    _, history = temp_db

    now = time.time()
    # Log an alert 1 hour ago
    history.log_alert(ts=now - 3600, rule_id="high-temp", sensor_id="temp-salon", value=28.0)
    # Log another alert 10 minutes ago
    history.log_alert(ts=now - 600, rule_id="high-temp", sensor_id="temp-salon", value=29.0)

    # Get last alert timestamp
    last_ts = history.get_last_alert_ts("high-temp")
    assert last_ts is not None
    assert abs(last_ts - (now - 600)) < 10  # Should be the most recent (10 min ago)

    # Check cooldown: 30 min cooldown
    cooldown_seconds = 30 * 60
    elapsed = now - last_ts
    in_cooldown = elapsed < cooldown_seconds
    assert in_cooldown is True  # 10 min < 30 min

    # Check with no cooldown (old alert)
    last_ts_old = history.get_last_alert_ts("non-existent")
    assert last_ts_old is None