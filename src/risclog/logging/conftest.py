import pytest
from risclog.logging import getLogger

# @pytest.fixture
# def mock_environment(monkeypatch):
#     monkeypatch.setenv('LOG_LEVEL', 'DEBUG')
#     monkeypatch.setenv('logging_email_smtp_user', 'test_user@example.com')
#     monkeypatch.setenv('logging_email_smtp_password', 'test_password')
#     monkeypatch.setenv('logging_email_to', 'admin@example.com')
#     monkeypatch.setenv('logging_email_smtp_server', 'smtp.example.com')


@pytest.fixture(autouse=True)
def clear_env(monkeypatch):
    """Stellt sicher, dass die für den Test relevanten Environment-Variablen nicht gesetzt sind."""
    env_vars = [
        'LOGGING_EMAIL_SMTP_USER',
        'LOGGING_EMAIL_SMTP_PASSWORD',
        'LOGGING_EMAIL_TO',
        'LOGGING_EMAIL_SMTP_SERVER',
    ]
    for var in env_vars:
        monkeypatch.delenv(var, raising=False)


@pytest.fixture
def logger1():
    return getLogger('test_logger_1')


@pytest.fixture
def logger2():
    return getLogger('test_logger_2')
