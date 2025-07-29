#!/usr/bin/env python3
"""Resume Assistant main entry point."""

import sys
from pathlib import Path

from .config import get_settings
from .utils import configure_logging, get_logger, error_handler


def main() -> None:
    """Main entry point for the Resume Assistant application."""
    try:
        # Initialize configuration and logging
        settings = get_settings()
        configure_logging()
        logger = get_logger(__name__)
        
        logger.info("Resume Assistant v0.1.0 starting...")
        logger.info(f"Using configuration: theme={settings.theme}, log_level={settings.log_level}")
        
        print("🚀 Resume Assistant v0.1.0")
        print("📝 AI-powered resume optimization tool")
        print("Starting application...")
        
        # TODO: Initialize and run the TUI application
        logger.info("Application initialization complete")
        print("✅ Application initialization complete.")
        
    except KeyboardInterrupt:
        print("\n⏹️  Application interrupted by user.")
        sys.exit(0)
    except Exception as e:
        error_handler.handle_error(e, "应用程序启动")
        sys.exit(1)

if __name__ == "__main__":
    main()