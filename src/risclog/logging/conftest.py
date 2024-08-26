import pytest
from risclog.logging import RiscLogger, get_logger


@pytest.fixture
def mock_environment(monkeypatch):
    monkeypatch.setenv('LOG_LEVEL', 'DEBUG')
    monkeypatch.setenv('logging_email_smtp_user', 'test_user@example.com')
    monkeypatch.setenv('logging_email_smtp_password', 'test_password')
    monkeypatch.setenv('logging_email_to', 'admin@example.com')
    monkeypatch.setenv('logging_email_smtp_server', 'smtp.example.com')


@pytest.fixture
def logger1() -> RiscLogger:
    return get_logger('test_logger_1')


@pytest.fixture
def logger2() -> RiscLogger:
    return get_logger('test_logger_2')
