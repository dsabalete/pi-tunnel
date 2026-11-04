"""Integration tests for command handlers."""

import tempfile
import os
import pytest
import pytest_asyncio
from unittest.mock import AsyncMock, MagicMock, patch

from telegram import Update, Message, User, Chat
from telegram.ext import Application, ContextTypes

from pitunnel.core.config import Config
from pitunnel.commands.handlers import setup_handlers, start_command, help_command, status_command, history_command, alerts_command
from pitunnel.storage.db import Database
from pitunnel.storage.history import History


@pytest.fixture
def temp_db_path():
    """Create a temporary database file path."""
    with tempfile.NamedTemporaryFile(suffix=".db", delete=False) as f:
        db_path = f.name
    yield db_path
    # Cleanup
    try:
        os.unlink(db_path)
    except OSError:
        pass


@pytest.fixture
def mock_config(temp_db_path):
    """Create a mock config for testing."""
    config = Config()
    config.telegram = type('obj', (object,), {
        'token': 'test-token',
        'authorized_users': [12345],
        'language': 'en'
    })()
    config.limits = type('obj', (object,), {
        'command_timeout_s': 10,
        'max_output_chars': 4000,
        'history_retention_days': 30
    })()
    config.commands = type('obj', (object,), {'aliases': {}})()
    config.sensors = []
    config.actuators = []
    config.alerts = type('obj', (object,), {'rules': []})()
    config.storage = {'database_path': temp_db_path}
    return config


@pytest.fixture
def mock_db(mock_config):
    """Create a test database with schema initialized."""
    db = Database(mock_config)
    db.init_schema()
    yield db
    db.close()


@pytest.fixture
def mock_history(mock_db):
    """Create a test history instance."""
    return History(mock_db)


@pytest.fixture
def mock_update():
    """Create a mock Update object."""
    update = MagicMock(spec=Update)
    update.effective_user = MagicMock(spec=User)
    update.effective_user.id = 12345
    update.effective_user.username = "testuser"
    update.effective_chat = MagicMock(spec=Chat)
    update.effective_chat.id = 12345
    update.message = MagicMock(spec=Message)
    update.message.reply_text = AsyncMock()
    update.message.chat_id = 12345
    return update


@pytest.fixture
def mock_context(mock_config, mock_history):
    """Create a mock Context object."""
    context = MagicMock(spec=ContextTypes.DEFAULT_TYPE)
    context.bot_data = {
        "config": mock_config,
        "registry": MagicMock(),
        "executor": MagicMock(),
        "confirmation_manager": MagicMock(),
        "history_logger": mock_history,
    }
    context.args = []
    return context


class TestStatusCommand:
    """Tests for /status command."""

    @pytest.mark.asyncio
    async def test_status_command_with_mocked_system(self, mock_update, mock_context, mock_history):
        """Test /status command returns formatted system status."""
        with patch("pitunnel.commands.handlers.get_system_status") as mock_get_status:
            from pitunnel.system.status import SystemStatus
            mock_get_status.return_value = SystemStatus(
                cpu_percent=25.0,
                ram_percent=50.0,
                cpu_temp_c=45.5,
                disk_root_percent=70.0,
                disk_nas_percent=None,
                uptime_seconds=86400 + 3600,  # 1d 1h
                local_ip="192.168.1.100",
                public_ip="1.2.3.4",
            )

            await status_command(mock_update, mock_context)

            # Verify reply_text was called
            mock_update.message.reply_text.assert_called_once()
            call_args = mock_update.message.reply_text.call_args
            text = call_args[0][0]

            # Verify content
            assert "Estado del sistema" in text
            assert "CPU: 25.0%" in text
            assert "RAM: 50.0%" in text
            assert "Temp CPU: 45.5°C" in text
            assert "Disco /: 70.0%" in text
            assert "Disco /mnt/nas" not in text  # disk_nas_percent is None, should not show
            assert "Uptime: 1d 1h 0m" in text
            assert "IP local: 192.168.1.100" in text
            assert "IP pública: 1.2.3.4" in text

    @pytest.mark.asyncio
    async def test_status_command_with_nas_disk(self, mock_update, mock_context, mock_history):
        """Test /status command shows NAS disk when available."""
        with patch("pitunnel.commands.handlers.get_system_status") as mock_get_status:
            from pitunnel.system.status import SystemStatus
            mock_get_status.return_value = SystemStatus(
                cpu_percent=30.0,
                ram_percent=60.0,
                cpu_temp_c=50.0,
                disk_root_percent=80.0,
                disk_nas_percent=45.0,
                uptime_seconds=172800,  # 2d
                local_ip="10.0.0.1",
                public_ip="5.6.7.8",
            )

            await status_command(mock_update, mock_context)

            mock_update.message.reply_text.assert_called_once()
            call_args = mock_update.message.reply_text.call_args
            text = call_args[0][0]

            # Verify NAS disk is shown
            assert "Disco /mnt/nas" in text
            assert "45.0%" in text


class TestHistoryCommand:
    """Tests for /history command."""

    @pytest.mark.asyncio
    async def test_history_command_with_entries(self, mock_update, mock_context, mock_history):
        """Test /history command returns formatted history entries."""
        import time

        # Add some history entries
        mock_history.log_command(
            ts=time.time() - 100,
            user_id=12345,
            alias="test-cmd",
            args="arg1",
            exit_code=0,
            stdout="output",
            stderr=""
        )
        mock_history.log_command(
            ts=time.time() - 200,
            user_id=12345,
            alias="another-cmd",
            args="",
            exit_code=1,
            stdout="",
            stderr="error"
        )

        await history_command(mock_update, mock_context)

        mock_update.message.reply_text.assert_called_once()
        call_args = mock_update.message.reply_text.call_args
        text = call_args[0][0]

        assert "Historial" in text
        assert "test-cmd" in text
        assert "another-cmd" in text
        assert "exit: 0" in text or "exit: 1" in text

    @pytest.mark.asyncio
    async def test_history_command_empty(self, mock_update, mock_context, mock_history):
        """Test /history command with empty database."""
        await history_command(mock_update, mock_context)

        mock_update.message.reply_text.assert_called_once()
        call_args = mock_update.message.reply_text.call_args
        text = call_args[0][0]

        assert "No hay historial" in text or "empty" in text.lower() or "historial" in text.lower()


class TestAlertsCommand:
    """Tests for /alerts command."""

    @pytest.mark.asyncio
    async def test_alerts_command_no_rules(self, mock_update, mock_context, mock_history):
        """Test /alerts command with no configured rules."""
        mock_context.bot_data["config"].alerts.rules = []

        await alerts_command(mock_update, mock_context)

        mock_update.message.reply_text.assert_called_once()
        call_args = mock_update.message.reply_text.call_args
        text = call_args[0][0]

        assert "Reglas de alerta" in text or "alertas" in text.lower()

    @pytest.mark.asyncio
    async def test_alerts_command_with_rules(self, mock_update, mock_context, mock_history):
        """Test /alerts command with configured rules."""
        import time

        # Add an alert rule to config
        mock_context.bot_data["config"].alerts.rules = [
            type('obj', (object,), {
                'rule_id': 'high-temp',
                'sensor_id': 'temp-salon',
                'when': '> 27.5',
                'cooldown_min': 30
            })()
        ]

        # Add an alert in history (within cooldown)
        mock_history.log_alert(
            ts=time.time() - 600,  # 10 minutes ago
            rule_id='high-temp',
            sensor_id='temp-salon',
            value=28.0
        )

        await alerts_command(mock_update, mock_context)

        mock_update.message.reply_text.assert_called_once()
        call_args = mock_update.message.reply_text.call_args
        text = call_args[0][0]

        assert "Reglas de alerta" in text
        assert "high-temp" in text
        assert "temp-salon" in text
        assert "COOLDOWN" in text or "OK" in text


class TestStartCommand:
    """Tests for /start command."""

    @pytest.mark.asyncio
    async def test_start_command(self, mock_update, mock_context, mock_history):
        """Test /start command sends welcome message."""
        mock_context.bot_data["config"].telegram.language = "en"

        await start_command(mock_update, mock_context)

        mock_update.message.reply_text.assert_called_once()
        call_args = mock_update.message.reply_text.call_args
        text = call_args[0][0]

        assert "Welcome" in text or "Bienvenido" in text