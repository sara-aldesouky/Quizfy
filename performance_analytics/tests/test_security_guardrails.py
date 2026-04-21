from pathlib import Path

from scripts.security_scan import scan


def test_secret_guardrail_scan_passes():
    repo_root = Path(__file__).resolve().parents[2]
    findings = scan(repo_root)
    assert findings == []


def test_secret_guardrail_detects_high_risk_patterns(tmp_path):
    risky = tmp_path / "risky.py"
    fake_openai_key = "sk-" + ("a" * 32)
    fake_sendgrid_key = "SG." + ("b" * 32)
    fake_bearer_token = "Bearer " + ("c" * 32)
    risky.write_text(
        "\n".join(
            [
                "import os",
                "print(os.getenv('OPENAI_API_KEY'))",
                "logger.info(request.headers)",
                "logger.debug(os.environ)",
                "logger.warning('x-api-key: value')",
                "print(cookies)",
                f"OPENAI_TEST = '{fake_openai_key}'",
                f"SENDGRID_TEST = '{fake_sendgrid_key}'",
                f"AUTH_TEST = '{fake_bearer_token}'",
            ]
        ),
        encoding="utf-8",
    )
    fixture = tmp_path / "fixture.json"
    fixture.write_text('{"access_token": "' + "d" * 32 + '"}', encoding="utf-8")

    findings = "\n".join(scan(tmp_path))

    assert "print-os-getenv" in findings
    assert "request-headers-dump" in findings
    assert "os-environ-dump" in findings
    assert "log-secret-env-name" in findings
    assert "log-or-print-sensitive-object" in findings
    assert "openai-key-pattern" in findings
    assert "sendgrid-key-pattern" in findings
    assert "bearer-token-pattern" in findings
    assert "secret-like-json-value" in findings


def test_secret_guardrail_allows_safe_patterns(tmp_path):
    safe = tmp_path / "safe.py"
    safe.write_text(
        "\n".join(
            [
                "from quizz_app.safe_logging import redact_headers",
                "logger.info('request complete path=%s status=%s', path, status)",
                "safe_headers = redact_headers(dict(request.headers))",
                "api_key = os.getenv('OPENAI_API_KEY')",
                "if not api_key:",
                "    raise RuntimeError('OPENAI_API_KEY not set')",
            ]
        ),
        encoding="utf-8",
    )
    fixture = tmp_path / "fixture.json"
    fixture.write_text(
        '{"access_token": "[REDACTED]", "api_key": "placeholder"}',
        encoding="utf-8",
    )

    assert scan(tmp_path) == []
