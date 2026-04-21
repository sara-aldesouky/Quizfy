#!/usr/bin/env python3
"""Fail-fast secret leakage guardrail for local tests and CI.

The scan intentionally avoids reading ignored runtime secret files such as
.env. It looks for high-risk code patterns and token-shaped strings that
should never be committed or logged.
"""

from __future__ import annotations

import argparse
import re
import sys
from pathlib import Path


DEFAULT_EXCLUDED_DIRS = {
    ".git",
    ".pytest_cache",
    ".mypy_cache",
    "__pycache__",
    "venv",
    ".venv",
    "vv",
    "uploads",
    "chroma_db",
    "logs",
    "staticfiles",
    "media",
}

DEFAULT_EXCLUDED_FILES = {
    ".env",
}

TEXT_SUFFIXES = {
    ".cfg",
    ".css",
    ".env",
    ".example",
    ".html",
    ".ini",
    ".js",
    ".json",
    ".md",
    ".py",
    ".sh",
    ".toml",
    ".txt",
    ".yaml",
    ".yml",
}

RULES = [
    (
        "print-os-getenv",
        re.compile(r"print\s*\([^)]*os\.getenv\s*\(", re.IGNORECASE),
        "Do not print environment variables.",
    ),
    (
        "openai-key-pattern",
        re.compile(r"sk-[A-Za-z0-9_-]{16,}"),
        "OpenAI-looking key pattern found.",
    ),
    (
        "sendgrid-key-pattern",
        re.compile(r"SG\.[A-Za-z0-9._-]{16,}"),
        "SendGrid-looking key pattern found.",
    ),
    (
        "bearer-token-pattern",
        re.compile(r"(?i)\bBearer\s+[A-Za-z0-9._~+/=-]{20,}"),
        "Bearer token-looking value found.",
    ),
    (
        "secret-like-json-value",
        re.compile(
            r"""(?ix)
            ["'](?:api[_-]?key|access[_-]?token|refresh[_-]?token|auth[_-]?token|
            id[_-]?token|client[_-]?secret|secret|password)["']\s*:\s*
            ["'](?!\[?REDACTED\]?|<[^>]+>|\$\{[^}]+\}|example|placeholder|changeme|test|dummy|fake|null|none|true|false)
            [^"'\s]{16,}["']
            """
        ),
        "Secret-like value found in structured data.",
    ),
    (
        "log-secret-env-name",
        re.compile(
            r"logger\.(?:debug|info|warning|error|critical|exception)\s*\([^)]*"
            r"(?:OPENAI_API_KEY|SENDGRID_API_KEY|DJANGO_SECRET_KEY|EMAIL_HOST_PASSWORD|"
            r"CLOUDINARY_API_SECRET|Authorization|authorization|x-api-key|api-key)",
            re.IGNORECASE | re.DOTALL,
        ),
        "Do not log secret environment names, authorization headers, or secret-bearing values.",
    ),
    (
        "request-headers-dump",
        re.compile(
            r"(?:print|logger\.(?:debug|info|warning|error|critical|exception))\s*\([^)]*"
            r"(?:request\.)?headers\b",
            re.IGNORECASE | re.DOTALL,
        ),
        "Do not print or log full request headers.",
    ),
    (
        "os-environ-dump",
        re.compile(
            r"(?:print|logger\.(?:debug|info|warning|error|critical|exception))\s*\([^)]*"
            r"os\.environ\b",
            re.IGNORECASE | re.DOTALL,
        ),
        "Do not print or log os.environ.",
    ),
    (
        "log-or-print-sensitive-object",
        re.compile(
            r"(?:print|logger\.(?:debug|info|warning|error|critical|exception))\s*\([^)]*"
            r"\b(?:headers|cookies|cookie|token|tokens|auth|authorization|credential|credentials|"
            r"api_key|apikey|api-key|x-api-key)\b",
            re.IGNORECASE | re.DOTALL,
        ),
        "Do not print or log headers, cookies, tokens, auth objects, or credentials.",
    ),
]

ALLOWED_RULES_BY_FILE = {
    ".env.example": set(rule_id for rule_id, _, _ in RULES),
    "scripts/security_scan.py": set(rule_id for rule_id, _, _ in RULES),
    "performance_analytics/tests/test_security_guardrails.py": set(
        rule_id for rule_id, _, _ in RULES
    ),
}


def should_skip(path: Path, root: Path) -> bool:
    relative = path.relative_to(root)
    if any(part in DEFAULT_EXCLUDED_DIRS for part in relative.parts):
        return True
    if path.name in DEFAULT_EXCLUDED_FILES:
        return True
    if path.name.startswith(".env.") and path.name != ".env.example":
        return True
    return False


def is_text_candidate(path: Path) -> bool:
    return path.suffix in TEXT_SUFFIXES or path.name in {".gitignore", ".env.example"}


def scan(root: Path) -> list[str]:
    findings: list[str] = []
    for path in sorted(root.rglob("*")):
        if not path.is_file() or should_skip(path, root) or not is_text_candidate(path):
            continue

        relative = path.relative_to(root).as_posix()
        text = path.read_text(encoding="utf-8", errors="ignore")
        allowed_rules = ALLOWED_RULES_BY_FILE.get(relative, set())

        for rule_id, pattern, message in RULES:
            if rule_id in allowed_rules:
                continue
            for match in pattern.finditer(text):
                line_number = text.count("\n", 0, match.start()) + 1
                findings.append(f"{relative}:{line_number}: {rule_id}: {message}")
    return findings


def main() -> int:
    parser = argparse.ArgumentParser(description="Scan repository for secret leakage risks.")
    parser.add_argument("--root", default=".", help="Repository root to scan.")
    args = parser.parse_args()

    root = Path(args.root).resolve()
    findings = scan(root)
    if findings:
        print("Secret guardrail scan failed:")
        for finding in findings:
            print(f" - {finding}")
        return 1

    print("Secret guardrail scan passed.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
