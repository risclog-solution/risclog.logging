import logging
import sys
from unittest.mock import patch

import pytest
from risclog.logging import RiscLogger, get_logger, rename_event_to_message


def test_logger_singleton(setup_logger):
    logger1 = get_logger('test_logger')
    logger2 = get_logger(__name__)

    assert logger1 is logger2, 'RiscLogger should be a singleton instance'


def test_debug_log(setup_logger, caplog):
    logger = setup_logger

    with caplog.at_level(logging.DEBUG):
        logger.debug('This is a debug message')

    assert 'This is a debug message' in caplog.text
    assert 'test_logger' in caplog.text
    assert 'DEBUG' in caplog.text


def test_info_log(setup_logger, caplog):
    logger = setup_logger

    with caplog.at_level(logging.INFO):
        logger.info('This is an info message')

    assert 'This is an info message' in caplog.text
    assert 'test_logger' in caplog.text
    assert 'INFO' in caplog.text


def test_warning_log(setup_logger, caplog):
    logger = setup_logger

    with caplog.at_level(logging.WARNING):
        logger.warning('This is a warning message')

    assert 'This is a warning message' in caplog.text
    assert 'test_logger' in caplog.text
    assert 'WARNING' in caplog.text


def test_error_log(setup_logger, caplog):
    logger = setup_logger

    with caplog.at_level(logging.ERROR):
        logger.error('This is an error message')

    assert 'This is an error message' in caplog.text
    assert 'test_logger' in caplog.text
    assert 'ERROR' in caplog.text


def test_critical_log(setup_logger, caplog):
    logger = setup_logger

    with caplog.at_level(logging.CRITICAL):
        logger.critical('This is a critical message')

    assert 'This is a critical message' in caplog.text
    assert 'test_logger' in caplog.text
    assert 'CRITICAL' in caplog.text


def test_fatal_log(setup_logger, caplog):
    logger = setup_logger

    with caplog.at_level(logging.FATAL):
        logger.fatal('This is a fatal message')

    assert 'This is a fatal message' in caplog.text
    assert 'test_logger' in caplog.text
    assert 'CRITICAL' in caplog.text


def test_exception_log(setup_logger, caplog):
    logger = setup_logger

    with caplog.at_level(logging.INFO):
        logger.exception('This is a exception message')

    assert 'This is a exception message' in caplog.text
    assert 'test_logger' in caplog.text
    assert 'ERROR' in caplog.text


@pytest.mark.asyncio
async def test_async_logging_decorator(setup_logger, caplog):
    logger = setup_logger

    @logger.decorator
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


def test_sync_logging_decorator(setup_logger, caplog):
    logger = setup_logger

    @logger.decorator()
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
def test_exception_logging_with_email(mock_smtp_send, setup_logger, caplog):
    logger = setup_logger

    @logger.decorator(send_email=True)
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
    expected_logger_name = 'test_logger'
    assert (
        expected_message in kwargs['message']
    ), f"First keyword argument should be '{expected_message}'"
    assert (
        kwargs['logger_name'] == expected_logger_name
    ), f"Second keyword argument should be '{expected_logger_name}'"


@patch('risclog.logging.smtp_email_send')
@pytest.mark.asyncio
async def test_async_exception_logging_with_email(
    mock_smtp_send, setup_logger, caplog
):
    logger = setup_logger

    @logger.decorator(send_email=True)
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
        'test_logger' in kwargs['logger_name']
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
    result_dict = rename_event_to_message(None, None, event_dict)

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
    result_dict = rename_event_to_message(None, None, event_dict)

    assert (
        result_dict == expected_dict
    ), f'Expected {expected_dict} but got {result_dict}'


def test_empty_dict():
    event_dict = {}
    expected_dict = {}
    result_dict = rename_event_to_message(None, None, event_dict)

    assert (
        result_dict == expected_dict
    ), f'Expected {expected_dict} but got {result_dict}'


def test_handle_keyboard_interrupt(setup_logger):
    with patch('sys.__excepthook__') as mock_excepthook:
        RiscLogger._configure_logger()
        sys.excepthook(KeyboardInterrupt, None, None)
        mock_excepthook.assert_called_once_with(KeyboardInterrupt, None, None)
