"""
Custom SendGrid email backend with debug logging
"""
import logging
from sendgrid_backend import SendgridBackend as OriginalSendgridBackend

from .safe_logging import redact

logger = logging.getLogger(__name__)


class SendgridBackend(OriginalSendgridBackend):
    """SendGrid backend with detailed logging"""
    
    def send_messages(self, email_messages):
        """Send messages and log the results"""
        if not email_messages:
            return 0
        
        logger.info(f"[SENDGRID] Attempting to send {len(email_messages)} message(s)")
        
        for msg in email_messages:
            logger.info("[SENDGRID] Subject: %s", redact(msg.subject))
            logger.info("[SENDGRID] From: %s", redact(msg.from_email))
            logger.info("[SENDGRID] To: %s", redact(msg.to))
        
        try:
            result = super().send_messages(email_messages)
            logger.info(f"[SENDGRID] Successfully sent {result} message(s)")
            return result
        except Exception as e:
            logger.error("[SENDGRID] Error: %s", redact(type(e).__name__))
            raise
