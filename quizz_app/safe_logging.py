"""Logging helpers that redact secrets before they reach handlers."""

from __future__ import annotations

import logging
import re
from typing import Any


SECRET_PATTERNS = [
    re.compile(r"(?i)(authorization\s*[:=]\s*bearer\s+)[^\s,;]+"),
    re.compile(r"(?i)((?:api[_-]?key|token|secret|password)\s*[:=]\s*)[^\s,;]+"),
    re.compile(r"(?i)(OPENAI_API_KEY|SENDGRID_API_KEY|DJANGO_SECRET_KEY|EMAIL_HOST_PASSWORD)(\s*[:=]\s*)[^\s,;]+"),
    re.compile(r"sk-[A-Za-z0-9_-]+"),
    re.compile(r"SG\.[A-Za-z0-9._-]+"),
]

SENSITIVE_HEADER_NAMES = {
    "authorization",
    "proxy-authorization",
    "x-api-key",
    "api-key",
    "cookie",
    "set-cookie",
}

REDACTED = "[REDACTED]"


def redact(value: Any) -> str:
    """Return a log-safe string with common secret patterns removed."""
    text = str(value)
    for pattern in SECRET_PATTERNS:
        if pattern.pattern.startswith("(?i)(OPENAI"):
            text = pattern.sub(r"\1\2" + REDACTED, text)
        elif "sk-" in pattern.pattern or "SG\\." in pattern.pattern:
            text = pattern.sub(REDACTED, text)
        else:
            text = pattern.sub(r"\1" + REDACTED, text)
    return text


def redact_headers(headers: dict[str, Any]) -> dict[str, str]:
    """Return headers with credential-bearing values redacted."""
    safe_headers = {}
    for key, value in headers.items():
        if key.lower() in SENSITIVE_HEADER_NAMES:
            safe_headers[key] = REDACTED
        else:
            safe_headers[key] = redact(value)
    return safe_headers


class RedactingFilter(logging.Filter):
    """Logging filter that redacts secrets from message and args."""

    def filter(self, record: logging.LogRecord) -> bool:
        record.msg = redact(record.msg)
        if isinstance(record.args, dict):
            record.args = {key: redact(value) for key, value in record.args.items()}
        elif isinstance(record.args, tuple):
            record.args = tuple(redact(value) for value in record.args)
        return True

