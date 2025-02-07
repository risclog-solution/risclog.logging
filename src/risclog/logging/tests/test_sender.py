import smtplib
import sys
import types
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText

import pytest
from risclog.logging.sender import get_env_case_insensitive, smtp_email_send


class FakeSMTP:
    last_instance = None

    def __init__(self, host, port):
        FakeSMTP.last_instance = self
        self.host = host
        self.port = port
        self.ehlo_called = False
        self.starttls_called = False
        self.login_called_with = None
        self.sent_message = None

    def ehlo(self):
        self.ehlo_called = True

    def starttls(self):
        self.starttls_called = True

    def login(self, user, password):
        self.login_called_with = (user, password)

    def send_message(self, message):
        self.sent_message = message

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_value, traceback):
        pass


class FakeLogger:
    def __init__(self):
        self.messages = []

    def error(self, msg):
        self.messages.append(msg)


class TestSender:
    def test_smtp_email_send_success(
        self, monkeypatch: pytest.MonkeyPatch
    ) -> types.NoneType:
        monkeypatch.setenv('LOGGING_EMAIL_SMTP_USER', 'user@example.com')
        monkeypatch.setenv('LOGGING_EMAIL_SMTP_PASSWORD', 'password')
        monkeypatch.setenv('LOGGING_EMAIL_TO', 'to@example.com')
        monkeypatch.setenv('LOGGING_EMAIL_SMTP_SERVER', 'smtp.example.com')

        monkeypatch.setattr(smtplib, 'SMTP', FakeSMTP)

        smtp_email_send('Test message', 'TestLogger')

        smtp_instance = FakeSMTP.last_instance
        assert smtp_instance is not None, 'FakeSMTP wurde nicht instanziiert.'

        assert smtp_instance.host == 'smtp.example.com'
        assert smtp_instance.port == 465

        assert smtp_instance.ehlo_called is True
        assert smtp_instance.starttls_called is True
        assert smtp_instance.login_called_with == (
            'user@example.com',
            'password',
        )

        email_message = smtp_instance.sent_message
        assert isinstance(email_message, MIMEMultipart)
        assert email_message['From'] == 'user@example.com'
        assert email_message['To'] == 'to@example.com'
        assert email_message['Subject'] == 'Error in TestLogger'

        payload = email_message.get_payload()
        found = any(
            isinstance(part, MIMEText) and 'Test message' in part.get_payload()
            for part in (payload if isinstance(payload, list) else [payload])
        )
        assert (
            found
        ), "Der Text 'Test message' wurde in der Email nicht gefunden."

    def test_smtp_email_send_missing_env(
        self, monkeypatch: pytest.MonkeyPatch
    ) -> types.NoneType:
        fake_logger = FakeLogger()
        fake_logging_module = types.ModuleType('risclog.logging')
        fake_logging_module.getLogger = lambda name: fake_logger
        monkeypatch.setitem(
            sys.modules, 'risclog.logging', fake_logging_module
        )

        def fake_smtp(*args, **kwargs):
            raise Exception(
                'SMTP sollte nicht aufgerufen werden, wenn Variablen fehlen!'
            )

        monkeypatch.setattr(smtplib, 'SMTP', fake_smtp)

        smtp_email_send('Test message', 'TestLogger')

        expected_message = 'Emails cannot be sent because one or more environment variables are not set!'
        assert (
            fake_logger.messages
        ), 'Es wurde keine Logger-Fehlermeldung erzeugt.'
        assert expected_message in fake_logger.messages[0]


class TestCaseInsensitive:
    def test_returns_uppercase_when_set(
        self, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        monkeypatch.setenv('MYVAR', 'upper_value')
        monkeypatch.delenv('myvar', raising=False)

        result = get_env_case_insensitive('myvar', default='default')
        assert result == 'upper_value'

    def test_returns_lowercase_when_only_lowercase_set(
        self, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        monkeypatch.delenv('MYVAR', raising=False)
        monkeypatch.setenv('myvar', 'lower_value')

        result = get_env_case_insensitive('MYVAR', default='default')
        assert result == 'lower_value'

    def test_returns_default_when_not_set(
        self, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        monkeypatch.delenv('NONEXISTENT', raising=False)
        monkeypatch.delenv('nonexistent', raising=False)

        result = get_env_case_insensitive(
            'nonexistent', default='default_value'
        )
        assert result == 'default_value'

    def test_prefers_uppercase_when_both_set(
        self, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        monkeypatch.setenv('VAR', 'upper_value')
        monkeypatch.setenv('var', 'lower_value')

        result = get_env_case_insensitive('var')
        assert result == 'upper_value'

    def test_returns_none_when_not_set_and_no_default(
        self, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        monkeypatch.delenv('UNSETVAR', raising=False)
        monkeypatch.delenv('unsetvar', raising=False)

        result = get_env_case_insensitive('unsetvar')
        assert result is None
