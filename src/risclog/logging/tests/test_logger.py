import logging
import sys
from unittest.mock import patch

import pytest
import risclog.logging
from structlog._config import BoundLoggerLazyProxy


def test_logger_initialization(
    logger1: risclog.logging.RiscLogger, logger2: risclog.logging.RiscLogger
) -> None:
    assert logger1.logger_name == 'test_logger_1'
    assert isinstance(logger1.logger, BoundLoggerLazyProxy)

    assert logger2.logger_name == 'test_logger_2'
    assert isinstance(logger2.logger, BoundLoggerLazyProxy)


@pytest.mark.asyncio
async def test_logging_levels_with_different_loggers(
    logger1: risclog.logging.RiscLogger,
    logger2: risclog.logging.RiscLogger,
    caplog,
) -> None:
    with caplog.at_level(logging.DEBUG):
        await logger1.debug('Test debug message logger1')
        assert 'Test debug message logger1' in caplog.text
        assert any(record.name == 'test_logger_1' for record in caplog.records)

    with caplog.at_level(logging.INFO):
        await logger2.info('Test info message logger2')
        assert 'Test info message logger2' in caplog.text
        assert any(record.name == 'test_logger_2' for record in caplog.records)

    assert not any(
        record.name == 'test_logger_2'
        and 'Test debug message logger1' in record.message
        for record in caplog.records
    )
    assert not any(
        record.name == 'test_logger_1'
        and 'Test info message logger2' in record.message
        for record in caplog.records
    )


def test_sync_log_decorator_with_different_loggers(logger1, logger2, caplog):
    @risclog.logging.RiscLogger.decorator
    def sample_sync_function_logger1(a, b):
        return a + b

    @risclog.logging.RiscLogger.decorator
    def sample_sync_function_logger2(a, b):
        return a - b

    with caplog.at_level(logging.INFO):
        result1 = sample_sync_function_logger1(3, 2)
    assert result1 == 5
    assert "Method called: \"sample_sync_function_logger1\"" in caplog.text

    with caplog.at_level(logging.INFO):
        result2 = sample_sync_function_logger2(3, 2)
    assert result2 == 1
    assert "Method called: \"sample_sync_function_logger2\"" in caplog.text

    assert not any(
        record.name == 'test_logger_2'
        and 'sample_sync_function_logger1' in record.message
        for record in caplog.records
    )
    assert not any(
        record.name == 'test_logger_1'
        and 'sample_sync_function_logger2' in record.message
        for record in caplog.records
    )


def test_structlog_logger_name(logger1, logger2, caplog):
    with caplog.at_level(logging.INFO):
        logger1.info('This is a message from logger 1')
        logger2.info('This is a message from logger 2')

    assert len(caplog.records) > 0

    logger_names = []
    for record in caplog.records:
        event_dict = record.msg if isinstance(record.msg, dict) else {}
        if 'logger' in event_dict:
            logger_names.append(event_dict['logger'])

    assert 'test_logger_1' in logger_names
    assert 'test_logger_2' in logger_names

    for name in logger_names:
        print(f'Logger name: {name}')


@pytest.mark.asyncio
async def test_async_log_decorator_with_different_loggers(
    logger1, logger2, caplog
):
    @risclog.logging.RiscLogger.decorator
    async def sample_async_function_logger1(a, b):
        return a + b

    @risclog.logging.RiscLogger.decorator
    async def sample_async_function_logger2(a, b):
        return a - b

    with caplog.at_level(logging.INFO):
        result1 = await sample_async_function_logger1(3, 2)

    assert result1 == 5
    assert "Method called: \"sample_async_function_logger1\"" in caplog.text

    with caplog.at_level(logging.INFO):
        result2 = await sample_async_function_logger2(3, 2)
    assert result2 == 1
    assert "Method called: \"sample_async_function_logger2\"" in caplog.text

    assert not any(
        record.name == 'test_logger_2'
        and 'sample_async_function_logger1' in record.message
        for record in caplog.records
    )
    assert not any(
        record.name == 'test_logger_1'
        and 'sample_async_function_logger2' in record.message
        for record in caplog.records
    )


def test_exception_to_string():
    try:
        raise ValueError('An error occurred')
    except Exception as exc:
        exc_string = risclog.logging.exception_to_string(exc)
        assert 'An error occurred' in exc_string


def test_debug_log(logger1, caplog):
    with caplog.at_level(logging.DEBUG):
        logger1.debug('This is a debug message')

    assert 'This is a debug message' in caplog.text
    assert 'test_logger' in caplog.text
    assert 'DEBUG' in caplog.text


def test_info_log(logger2, caplog):
    with caplog.at_level(logging.INFO):
        logger2.info('This is an info message')

    assert 'This is an info message' in caplog.text
    assert 'test_logger' in caplog.text
    assert 'INFO' in caplog.text


def test_warning_log(logger1, caplog):
    with caplog.at_level(logging.WARNING):
        logger1.warning('This is a warning message')

    assert 'This is a warning message' in caplog.text
    assert 'test_logger' in caplog.text
    assert 'WARNING' in caplog.text


def test_error_log(logger2, caplog):
    with caplog.at_level(logging.ERROR):
        logger2.error('This is an error message')

    assert 'This is an error message' in caplog.text
    assert 'test_logger' in caplog.text
    assert 'ERROR' in caplog.text


def test_critical_log(logger1, caplog):
    with caplog.at_level(logging.CRITICAL):
        logger1.critical('This is a critical message')

    assert 'This is a critical message' in caplog.text
    assert 'test_logger' in caplog.text
    assert 'CRITICAL' in caplog.text


def test_fatal_log(logger2, caplog):
    with caplog.at_level(logging.FATAL):
        logger2.fatal('This is a fatal message')

    assert 'This is a fatal message' in caplog.text
    assert 'test_logger' in caplog.text
    assert 'CRITICAL' in caplog.text


def test_exception_log(logger1, caplog):
    with caplog.at_level(logging.INFO):
        logger1.exception('This is a exception message')

    assert 'This is a exception message' in caplog.text
    assert 'test_logger' in caplog.text
    assert 'ERROR' in caplog.text


@pytest.mark.asyncio
async def test_async_logging_decorator(logger1, caplog):
    @logger1.decorator
    async def async_test_func(arg_0, arg_1):
        return f'Result: {arg_0 + arg_1}'

    with caplog.at_level(logging.INFO):
        result = await async_test_func(1, 2)

    assert result == 'Result: 3'

    log_records = [
        record for record in caplog.records if record.levelname == 'INFO'
    ]
    assert len(log_records) >= 2

    first_log = log_records[0].msg
    second_log = log_records[1].msg

    assert (
        'Method called: "async_test_func" with: "{\'arg_0\': 1, \'arg_1\': 2}"'
        in first_log['message']
    )
    assert (
        'Method "async_test_func" returned: "Result: 3"'
        in second_log['message']
    )


def test_sync_logging_decorator(logger1, caplog):
    @logger1.decorator()
    def sync_test_func(arg1, arg2):
        return f'Result: {arg1 + arg2}'

    with caplog.at_level(logging.INFO):
        result = sync_test_func(3, 4)

    assert result == 'Result: 7'

    log_records = [
        record for record in caplog.records if record.levelname == 'INFO'
    ]
    assert len(log_records) >= 2

    first_log = log_records[0].msg
    second_log = log_records[1].msg

    assert (
        'Method called: "sync_test_func" with: "{\'arg_0\': 3, \'arg_1\': 4}"'
        in first_log['message']
    )
    assert (
        'Method "sync_test_func" returned: "Result: 7"'
        in second_log['message']
    )


@patch('risclog.logging.smtp_email_send')
def test_exception_logging_with_email(mock_smtp_send, logger1, caplog):
    @logger1.decorator(send_email=True)
    def faulty_func():
        raise ValueError('This is an error')

    with caplog.at_level(logging.ERROR):
        with pytest.raises(ValueError, match='This is an error'):
            faulty_func()

    assert 'Exception occurred in method: faulty_func' in caplog.text
    assert 'This is an error' in caplog.text

    assert (
        mock_smtp_send.called
    ), 'smtp_email_send should be called when an exception occurs with send_email=True'
    mock_smtp_send.assert_called_once()

    args, kwargs = mock_smtp_send.call_args

    assert (
        len(args) == 0
    ), 'smtp_email_send should not be called with positional arguments'
    assert (
        len(kwargs) == 2
    ), 'smtp_email_send should be called with two keyword arguments'

    expected_message = 'Exception occurred in method: faulty_func'
    expected_logger_name = 'risclog.logging.tests.test_logger'
    assert (
        expected_message in kwargs['message']
    ), f"First keyword argument should be '{expected_message}'"
    assert (
        kwargs['logger_name'] == expected_logger_name
    ), f"Second keyword argument should be '{expected_logger_name}'"


@patch('risclog.logging.smtp_email_send')
@pytest.mark.asyncio
async def test_async_exception_logging_with_email(
    mock_smtp_send, logger1, caplog
):
    @logger1.decorator(send_email=True)
    async def faulty_async_func():
        raise ValueError('This is an async error')

    with caplog.at_level(logging.ERROR):
        with pytest.raises(ValueError, match='This is an async error'):
            await faulty_async_func()

    assert 'Exception occurred in method: faulty_async_func' in caplog.text
    assert 'This is an async error' in caplog.text

    assert (
        mock_smtp_send.called
    ), 'smtp_email_send should be called when an exception occurs in async function with send_email=True'
    mock_smtp_send.assert_called_once()
    args, kwargs = mock_smtp_send.call_args

    assert (
        len(args) == 0
    ), 'smtp_email_send should not be called with positional arguments'
    assert (
        len(kwargs) == 2
    ), 'smtp_email_send should be called with two keyword arguments'

    assert (
        'This is an async error' in kwargs['message']
    ), 'The error message should be in the email content'
    assert (
        'risclog.logging' in kwargs['logger_name']
    ), 'Logger name should be passed to the smtp_email_send function'


def test_rename_event_to_message():
    event_dict = {
        'event': 'This is an event message',
        'level': 'info',
        'referer': 'https://example.com',
        'user': 'test_user',
    }
    expected_dict = {
        'level': 'info',
        'user': 'test_user',
        'message': 'This is an event message',
        'referer': 'https://example.com',
    }
    result_dict = risclog.logging.rename_event_to_message(
        None, None, event_dict
    )

    assert (
        result_dict == expected_dict
    ), f'Expected {expected_dict} but got {result_dict}'


def test_no_event_key():
    event_dict = {
        'level': 'info',
        'user': 'test_user',
        'referer': 'https://example.com',
    }
    expected_dict = {
        'level': 'info',
        'user': 'test_user',
        'referer': 'https://example.com',
    }
    result_dict = risclog.logging.rename_event_to_message(
        None, None, event_dict
    )

    assert (
        result_dict == expected_dict
    ), f'Expected {expected_dict} but got {result_dict}'


def test_empty_dict():
    event_dict = {}
    expected_dict = {}
    result_dict = risclog.logging.rename_event_to_message(
        None, None, event_dict
    )

    assert (
        result_dict == expected_dict
    ), f'Expected {expected_dict} but got {result_dict}'


def test_handle_keyboard_interrupt(logger1):
    with patch('sys.__excepthook__') as mock_excepthook:
        risclog.logging.RiscLogger._configure_logger()
        sys.excepthook(KeyboardInterrupt, None, None)
        mock_excepthook.assert_called_once_with(KeyboardInterrupt, None, None)


def test_inline_and_decorator_have_same_id_in_logs(logger1, caplog):
    @logger1.decorator()
    def test_func():
        logger1.info('This is a message from the decorator')

    with caplog.at_level(logging.INFO):
        test_func()

    log_records = [
        record for record in caplog.records if record.levelname == 'INFO'
    ]
    assert len(log_records) == 3
    assert len({r.msg['__id'] for r in log_records}) == 1
