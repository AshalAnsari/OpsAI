import logging
import smtplib
from email.message import EmailMessage

from app.core.config import get_settings

logger = logging.getLogger(__name__)
settings = get_settings()


def send_email(*, to_email: str, subject: str, body: str) -> bool:
    """
    Send an email via SMTP when configured.
    In demo mode (no SMTP host), logs the message and returns True so flows continue.
    """
    if not settings.smtp_host:
        logger.info(
            "EMAIL_DEMO to=%s subject=%s body=%s",
            to_email,
            subject,
            body[:500],
        )
        return True

    message = EmailMessage()
    message["From"] = settings.smtp_from_email or settings.seed_admin_email
    message["To"] = to_email
    message["Subject"] = subject
    message.set_content(body)

    try:
        with smtplib.SMTP(settings.smtp_host, settings.smtp_port, timeout=20) as server:
            if settings.smtp_use_tls:
                server.starttls()
            if settings.smtp_username and settings.smtp_password:
                server.login(settings.smtp_username, settings.smtp_password)
            server.send_message(message)
        return True
    except Exception:
        logger.exception("Failed to send email to %s", to_email)
        return False
