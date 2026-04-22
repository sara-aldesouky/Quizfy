#!/usr/bin/env python3
"""
Main entry point for running the Performance Analytics FastAPI server.
Usage: python -m performance_analytics.main
"""

import sys
import logging
import uvicorn
from .config import config

# Configure logging early
logging.basicConfig(
    level=config.LOG_LEVEL,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)

logger = logging.getLogger(__name__)


def main() -> None:
    """Start the FastAPI server."""
    try:
        logger.info(f"Starting Quizfy Performance Analytics Service ({config.ENV} environment)")
        
        # Validate configuration
        config.validate_startup()
        logger.info("✓ Configuration validated")
        
        # Import app after config validation
        from .api import app
        
        # Run server
        uvicorn.run(
            app,
            host="0.0.0.0",
            port=8001,
            log_level=config.LOG_LEVEL.lower(),
            reload=config.DEBUG,
        )
    except Exception as e:
        logger.error(f"Failed to start service: {e}", exc_info=True)
        sys.exit(1)


if __name__ == "__main__":
    main()
