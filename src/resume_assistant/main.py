#!/usr/bin/env python3
"""Resume Assistant main entry point."""

import sys
from pathlib import Path

# 添加项目根目录到 Python 路径
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

from src.resume_assistant.config import get_settings
from src.resume_assistant.utils import configure_logging, get_logger, error_handler


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
        print("Starting TUI application...")
        
        # Initialize and run the TUI application
        from src.resume_assistant.ui.app import ResumeAssistantApp
        
        logger.info("Initializing TUI application")
        app = ResumeAssistantApp()
        
        logger.info("Application initialization complete, starting UI")
        app.run()
        
    except KeyboardInterrupt:
        print("\n⏹️  Application interrupted by user.")
        sys.exit(0)
    except Exception as e:
        error_handler.handle_error(e, "应用程序启动")
        sys.exit(1)

if __name__ == "__main__":
    main()