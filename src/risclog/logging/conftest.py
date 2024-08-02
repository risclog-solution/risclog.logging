import pytest
from risclog.logging import get_logger


@pytest.fixture(scope='function')
def setup_logger(monkeypatch):
    monkeypatch.setenv('logging_email_smtp_user', 'user@example.com')
    monkeypatch.setenv('logging_email_smtp_password', 'password')
    monkeypatch.setenv('logging_email_to', 'recipient@example.com')
    monkeypatch.setenv('logging_email_smtp_server', 'smtp.example.com')

    logger = get_logger('test_logger')
    return logger
