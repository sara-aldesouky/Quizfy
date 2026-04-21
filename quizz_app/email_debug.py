"""
Custom email backend with enhanced debugging
"""
import logging
from django.core.mail.backends.smtp import EmailBackend as SMTPEmailBackend
from django.core.mail.backends.console import EmailBackend as ConsoleEmailBackend

from .safe_logging import redact

logger = logging.getLogger(__name__)


class DebugSMTPEmailBackend(SMTPEmailBackend):
    """SMTP backend with detailed logging"""
    
    def send_messages(self, email_messages):
        logger.info(f"[EMAIL] Attempting to send {len(email_messages)} message(s) via SMTP")
        for msg in email_messages:
            logger.info("[EMAIL] Subject: %s", redact(msg.subject))
            logger.info("[EMAIL] From: %s", redact(msg.from_email))
            logger.info("[EMAIL] To: %s", redact(msg.to))
        
        try:
            result = super().send_messages(email_messages)
            logger.info(f"[EMAIL] Successfully sent {result} message(s)")
            return result
        except Exception as e:
            logger.error("[EMAIL] SMTP Error: %s", redact(type(e).__name__))
            raise


class DebugConsoleEmailBackend(ConsoleEmailBackend):
    """Console backend with detailed logging"""
    
    def send_messages(self, email_messages):
        logger.warning(f"[EMAIL] EMAIL_BACKEND set to console (password not configured)")
        logger.warning(f"[EMAIL] Would send {len(email_messages)} message(s) to console instead of SMTP")
        return super().send_messages(email_messages)
