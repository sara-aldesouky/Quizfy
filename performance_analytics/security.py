"""Security helpers for analytics logging and error handling."""

from __future__ import annotations

import logging

from quizz_app.safe_logging import RedactingFilter, redact, redact_headers


def configure_safe_logging() -> None:
    """Attach redaction to root handlers without logging environment values."""
    redacting_filter = RedactingFilter()
    root_logger = logging.getLogger()
    for handler in root_logger.handlers:
        if not any(isinstance(item, RedactingFilter) for item in handler.filters):
            handler.addFilter(redacting_filter)


__all__ = ["RedactingFilter", "configure_safe_logging", "redact", "redact_headers"]

