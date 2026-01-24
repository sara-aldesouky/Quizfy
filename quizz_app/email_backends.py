# quizz_app/email_backends.py

import os
import logging

from django.core.mail.backends.base import BaseEmailBackend
from django.core.mail import EmailMultiAlternatives

from sendgrid import SendGridAPIClient
from sendgrid.helpers.mail import Mail

logger = logging.getLogger(__name__)


class SendGridBackend(BaseEmailBackend):
    """
    Django email backend that sends emails using SendGrid Web API.
    Works with Django's EmailMessage / EmailMultiAlternatives.
    """

    def __init__(self, fail_silently=False, **kwargs):
        super().__init__(fail_silently=fail_silently)
        self.api_key = os.environ.get("SENDGRID_API_KEY", "")

    def send_messages(self, email_messages):
        if not email_messages:
            return 0

        if not self.api_key:
            logger.error("SENDGRID_API_KEY is missing. Emails will not be sent.")
            return 0

        sent_count = 0
        client = SendGridAPIClient(self.api_key)

        for message in email_messages:
            try:
                # message is Django EmailMessage/EmailMultiAlternatives
                to_emails = list(message.to or [])
                from_email = message.from_email
                subject = message.subject or ""
                text_content = message.body or ""

                # If EmailMultiAlternatives has html alternative, use it
                html_content = None
                if isinstance(message, EmailMultiAlternatives):
                    for alt, mimetype in getattr(message, "alternatives", []):
                        if mimetype == "text/html":
                            html_content = alt
                            break

                logger.info("SendGrid sending to=%s subject=%s", to_emails, subject)

                sg_mail = Mail(
                    from_email=from_email,
                    to_emails=to_emails,
                    subject=subject,
                    plain_text_content=text_content,
                    html_content=html_content,
                )

                response = client.send(sg_mail)

                if 200 <= response.status_code < 300:
                    sent_count += 1
                else:
                    logger.error(
                        "SendGrid failed: status=%s body=%s",
                        response.status_code,
                        getattr(response, "body", b"")[:500],
                    )

            except Exception as e:
                logger.exception("SendGrid email send failed: %s", e)
                if not self.fail_silently:
                    raise

        return sent_count
