"""
Tests for confirmation manager.
"""
from __future__ import annotations

import time

import pytest

from pitunnel.commands.confirm import ConfirmationManager


def test_create_confirmation() -> None:
    """Test creating a confirmation."""
    manager = ConfirmationManager()

    callback_data, keyboard = manager.create_confirmation(
        alias="reboot",
        user_id=123456789,
        chat_id=987654321,
    )

    assert callback_data.startswith("confirm:")
    assert keyboard is not None
    assert len(keyboard.inline_keyboard) == 1
    assert len(keyboard.inline_keyboard[0]) == 2


def test_verify_valid_confirmation() -> None:
    """Test verifying a valid confirmation."""
    manager = ConfirmationManager()

    callback_data, _ = manager.create_confirmation(
        alias="reboot",
        user_id=123456789,
        chat_id=987654321,
    )

    pending = manager.verify_confirmation(callback_data, 123456789)

    assert pending.alias == "reboot"
    assert pending.user_id == 123456789
    assert pending.chat_id == 987654321


def test_verify_expired_confirmation() -> None:
    """Test verifying an expired confirmation."""
    manager = ConfirmationManager()

    callback_data, _ = manager.create_confirmation(
        alias="reboot",
        user_id=123456789,
        chat_id=987654321,
    )

    # Manually expire by manipulating the timestamp in callback data
    # The callback data format is: confirm:alias:user_id:timestamp:signature
    parts = callback_data.split(":")
    old_timestamp = str(int(time.time()) - 120)  # 2 minutes ago
    parts[3] = old_timestamp

    # Recalculate signature for the old timestamp
    import hmac
    expected_data = f"reboot:123456789:{old_timestamp}"
    new_signature = hmac.new(
        manager.HMAC_SECRET,
        expected_data.encode(),
        "sha256"
    ).hexdigest()[:16]
    parts[4] = new_signature
    expired_callback_data = ":".join(parts)

    with pytest.raises(Exception, match="expired"):
        manager.verify_confirmation(expired_callback_data, 123456789)


def test_verify_wrong_user() -> None:
    """Test verifying with wrong user."""
    manager = ConfirmationManager()

    callback_data, _ = manager.create_confirmation(
        alias="reboot",
        user_id=123456789,
        chat_id=987654321,
    )

    with pytest.raises(Exception, match="expired"):
        manager.verify_confirmation(callback_data, 999999999)


def test_verify_invalid_hmac() -> None:
    """Test verifying with invalid HMAC."""
    manager = ConfirmationManager()

    # Create valid callback data then corrupt it
    callback_data, _ = manager.create_confirmation(
        alias="reboot",
        user_id=123456789,
        chat_id=987654321,
    )

    # Corrupt the signature
    corrupted = callback_data[:-1] + ("a" if callback_data[-1] != "a" else "b")

    with pytest.raises(Exception, match="expired"):
        manager.verify_confirmation(corrupted, 123456789)


def test_cancel_confirmation() -> None:
    """Test cancelling a confirmation."""
    manager = ConfirmationManager()

    _callback_data, _ = manager.create_confirmation(
        alias="reboot",
        user_id=123456789,
        chat_id=987654321,
    )

    assert manager.cancel_confirmation("reboot", 123456789)
    assert not manager.cancel_confirmation("reboot", 123456789)  # Already cancelled


def test_cleanup_expired() -> None:
    """Test cleaning up expired confirmations."""
    manager = ConfirmationManager()

    callback_data, _ = manager.create_confirmation(
        alias="reboot",
        user_id=123456789,
        chat_id=987654321,
    )

    # Expire it
    pending = manager._pending[callback_data]
    pending.created_at = time.time() - 120

    assert manager.cleanup_expired() == 1
    assert len(manager._pending) == 0