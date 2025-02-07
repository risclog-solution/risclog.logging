from __future__ import annotations

import os
import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText


def get_env_case_insensitive(
    varname: str, default: str | None = None
) -> str | None:
    value = os.getenv(varname.upper())
    if value is not None:
        return value
    return os.getenv(varname.lower(), default)


def smtp_email_send(message: str, logger_name: str) -> None:
    smtp_user = get_env_case_insensitive('logging_email_smtp_user')
    smtp_password = get_env_case_insensitive('logging_email_smtp_password')
    email_to = get_env_case_insensitive('logging_email_to')
    smtp_server = get_env_case_insensitive('logging_email_smtp_server')

    if smtp_user and smtp_password and email_to and smtp_server:
        # Email server setup
        smtp_user = smtp_user
        smtp_password = smtp_password

        # Create the email message
        email_message = MIMEMultipart()
        email_message['From'] = smtp_user
        email_message['To'] = email_to
        email_message['Subject'] = f'Error in {logger_name}'
        email_message.attach(MIMEText(message, 'plain'))

        # Send the email
        with smtplib.SMTP(host=smtp_server, port=465) as smtp:
            smtp.ehlo()
            smtp.starttls()
            smtp.login(smtp_user, smtp_password)
            smtp.send_message(email_message)
    else:
        from risclog.logging import getLogger

        logger = getLogger(name=logger_name)
        logger.error(
            'Emails cannot be sent because one or more environment variables are not set!'
        )
