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
        configure_logging(enable_console=True)
        
        logger = get_logger(__name__)
        
        logger.info("Resume Assistant v0.1.0 starting...")
        logger.info(f"Using configuration: theme={settings.theme}, log_level={settings.log_level}")
        
        # 基础功能初始化
        logger.info("Application core modules initialized")
        logger.info("Resume Assistant is ready for interface integration")
        
    except KeyboardInterrupt:
        sys.exit(0)
    except Exception as e:
        error_handler.handle_error(e, "应用程序启动")
        sys.exit(1)


if __name__ == "__main__":
    main()