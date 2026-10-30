"""
Main entry point for PiTunnel bot.
"""
from pitunnel.core.bot import create_bot
from pitunnel.core.config import Config, load_env


def main() -> None:
    """Start the bot."""
    # Load environment variables
    load_env()

    # Load configuration
    config = Config.load()

    # Create and run bot
    bot = create_bot(config)
    bot.run()


if __name__ == "__main__":
    main()