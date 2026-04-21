# quizz_app/email_backends.py
import os
import logging
from django.core.mail.backends.base import BaseEmailBackend
from django.core.mail import EmailMultiAlternatives

from sendgrid import SendGridAPIClient
from sendgrid.helpers.mail import Mail, Email, To, Content

from .safe_logging import redact

logger = logging.getLogger(__name__)

class SendGridEmailBackend(BaseEmailBackend):
    """
    Django email backend using SendGrid API (no SMTP).
    """

    def send_messages(self, email_messages):
        api_key = os.getenv("SENDGRID_API_KEY")
        if not api_key:
            logger.error("Email provider API key is missing")
            return 0

        sent_count = 0

        for message in email_messages:
            try:
                from_email = message.from_email or os.getenv("DEFAULT_FROM_EMAIL")
                to_emails = list(message.to) if message.to else []

                if not to_emails:
                    logger.warning("No recipients found, skipping email")
                    continue

                subject = message.subject or ""
                plain_body = message.body or ""

                sg_mail = Mail(
                    from_email=Email(from_email),
                    to_emails=[To(e) for e in to_emails],
                    subject=subject,
                    plain_text_content=Content("text/plain", plain_body),
                )

                # If Django built an HTML alternative, send it too
                if hasattr(message, "alternatives") and message.alternatives:
                    for alt_body, mimetype in message.alternatives:
                        if mimetype == "text/html":
                            sg_mail.add_content(Content("text/html", alt_body))

                sg = SendGridAPIClient(api_key)
                resp = sg.send(sg_mail)

                logger.info(
                    "SendGrid sent email: status=%s to=%s subject=%s",
                    resp.status_code, to_emails, subject
                )

                # 2xx = success
                if 200 <= resp.status_code < 300:
                    sent_count += 1
                else:
                    logger.error("SendGrid failed: status=%s", resp.status_code)

            except Exception as exc:
                logger.error(
                    "SendGrid exception while sending email: %s",
                    redact(type(exc).__name__),
                )

        return sent_count
