"""
Authorization filter for PiTunnel.
"""
from __future__ import annotations

from telegram import Update
from telegram.ext.filters import BaseFilter

from pitunnel.core.config import Config
from pitunnel.core.errors import UnauthorizedError
from pitunnel.core.logging import get_logger

logger = get_logger(__name__)


class AuthorizedFilter(BaseFilter):
    """
    Filter to check if user is authorized.

    Only users in the authorized_users list pass this filter.
    """

    def __init__(self, config: Config) -> None:
        self.authorized_users = set(config.telegram.authorized_users)

    def filter(self, update: Update) -> bool:
        """Check if update is from authorized user."""
        user = update.effective_user
        if user is None:
            # No user info (e.g., channel posts), allow through
            return True

        user_id = user.id
        if user_id not in self.authorized_users:
            logger.warning(
                "Unauthorized access attempt",
                extra={"user_id": user_id, "username": user.username or "unknown"}
            )
            raise UnauthorizedError(user_id)

        return True


def get_authorized_filter(config: Config) -> AuthorizedFilter:
    """
    Get an authorized filter for the given config.

    Args:
        config: Configuration object.

    Returns:
        AuthorizedFilter instance.
    """
    return AuthorizedFilter(config)