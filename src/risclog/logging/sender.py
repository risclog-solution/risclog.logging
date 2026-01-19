from __future__ import annotations

import os
import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText

import stamina


def get_env_case_insensitive(varname: str, default: str | None = None) -> str | None:
    value = os.getenv(varname.upper())
    if value is not None:
        return value
    return os.getenv(varname.lower(), default)


def smtp_email_send(
    message: str,
    logger_name: str,
    max_retries: int = 3,
    retry_delay: float = 2.0,
) -> bool:
    """
    Send an email notification with retry mechanism using stamina.

    Args:
        message: The message to send
        logger_name: Name of the logger (for error reporting)
        max_retries: Maximum number of retry attempts (default: 3)
        retry_delay: Delay between retries in seconds (default: 2.0)

    Returns:
        bool: True if successfully sent, False otherwise
    """
    smtp_user = get_env_case_insensitive("logging_email_smtp_user")
    smtp_password = get_env_case_insensitive("logging_email_smtp_password")
    email_to = get_env_case_insensitive("logging_email_to")
    smtp_server = get_env_case_insensitive("logging_email_smtp_server")
    smtp_port = int(get_env_case_insensitive("logging_email_smtp_port") or "465")

    if not (smtp_user and smtp_password and email_to and smtp_server):
        from risclog.logging import getLogger

        logger = getLogger(logger_name)
        logger.error(
            "Emails cannot be sent because one or more environment variables are not set!"
        )
        return False

    # Create the email message
    email_message = MIMEMultipart()
    email_message["From"] = smtp_user
    email_message["To"] = email_to
    email_message["Subject"] = f"Error in {logger_name}"
    email_message.attach(MIMEText(message, "plain"))

    # Retry-Mechanismus mit Stamina
    @stamina.retry(on=(smtplib.SMTPException, OSError), attempts=max_retries)  # type: ignore[misc]
    def send_email_with_retry() -> None:
        with smtplib.SMTP(host=smtp_server, port=smtp_port) as smtp:
            smtp.ehlo()
            smtp.starttls()
            smtp.login(smtp_user, smtp_password)
            smtp.send_message(email_message)

    try:
        send_email_with_retry()
        return True
    except Exception as e:
        from risclog.logging import getLogger

        logger = getLogger(logger_name)
        logger.error(
            f"Failed to send email after {max_retries} attempts",
            error=str(e),
        )
        return False
