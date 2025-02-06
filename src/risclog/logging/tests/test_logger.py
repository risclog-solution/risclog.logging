import asyncio
import logging
import os
import re
import tempfile
from unittest.mock import patch

import pytest
from risclog.logging import getLogger, log_decorator
from risclog.logging.log import HybridLogger
from structlog.testing import capture_logs

try:
    from structlog.stdlib import ProcessorFormatter
except ImportError:
    ProcessorFormatter = None


class TestLogger:
    def test_bind(self):
        with capture_logs() as cap_logs:
            getLogger(__name__).bind(x='y').info('hello')
            assert cap_logs == [
                {'x': 'y', 'event': 'hello', 'log_level': 'info'}
            ]

    @pytest.mark.asyncio
    async def test_async_logging_levels_with_different_loggers(
        self, logger1: HybridLogger, logger2: HybridLogger
    ) -> None:
        with capture_logs() as cap_logs:
            logger1.set_level(logging.DEBUG)
            logger2.set_level(logging.INFO)

            await logger1.error('Test error message logger1')
            await logger2.info('Test info message logger2')

            assert 'Test error message logger1' in cap_logs[0]['event']
            assert cap_logs[0]['log_level'] == 'error'

            assert 'Test info message logger2' in cap_logs[1]['event']
            assert cap_logs[1]['log_level'] == 'info'

    def test_sync_logging_levels_with_different_loggers(
        self, logger1: HybridLogger, logger2: HybridLogger
    ) -> None:
        with capture_logs() as cap_logs:
            logger1.set_level(logging.DEBUG)
            logger2.set_level(logging.INFO)

            logger1.debug('Test debug message logger1')
            logger2.info('Test info message logger2')

            assert 'Test debug message logger1' in cap_logs[0]['event']
            assert cap_logs[0]['log_level'] == 'debug'

            assert 'Test info message logger2' in cap_logs[1]['event']
            assert cap_logs[1]['log_level'] == 'info'

    def test_structlog_logger_name(
        self,
        caplog: pytest.LogCaptureFixture,
        logger1: HybridLogger,
        logger2: HybridLogger,
    ) -> None:
        with caplog.at_level(logging.INFO):
            logger1.bind(x='y').info('hello')
            logger2.bind(x='y').info('hello')

        assert len(caplog.records) > 0

        logger_names = []
        for record in caplog.records:
            event_dict = record.msg if isinstance(record.msg, dict) else {}
            if 'logger' in event_dict:
                logger_names.append(event_dict['logger'])

        assert 'test_logger_1' in logger_names
        assert 'test_logger_2' in logger_names

    @pytest.mark.asyncio
    async def test_log_decorator_logging_behavior_for_mixed_sync_async_functions(
        self,
    ) -> None:
        @log_decorator
        async def sample_async_function(a, b):
            return a + b

        @log_decorator
        def sample_sync_function(a, b):
            return a - b

        with capture_logs() as cap_logs:
            await sample_async_function(3, 2)

            assert cap_logs[0]['_function'] == 'sample_async_function'
            assert cap_logs[0]['_script'] == 'test_logger.py'
            assert cap_logs[0]['args'] == ('a:int=3', 'b:int=2')
            assert cap_logs[0]['kwargs'] == {}
            assert (
                'Decorator start: sample_async_function'
                in cap_logs[0]['event']
            )
            assert cap_logs[0]['log_level'] == 'info'

            assert cap_logs[1]['_function'] == 'sample_async_function'
            assert cap_logs[1]['_script'] == 'test_logger.py'
            assert isinstance(cap_logs[1]['duration'], str)
            assert (
                'Decorator success: sample_async_function'
                in cap_logs[1]['event']
            )
            assert cap_logs[1]['log_level'] == 'info'

            loop = asyncio.get_running_loop()
            await loop.run_in_executor(None, sample_sync_function, 3, 2)

            assert cap_logs[2]['_function'] == 'sample_sync_function'
            assert cap_logs[2]['_script'] == 'test_logger.py'
            assert cap_logs[2]['args'] == ('a:int=3', 'b:int=2')
            assert cap_logs[2]['kwargs'] == {}
            assert (
                'Decorator start: sample_sync_function' in cap_logs[2]['event']
            )
            assert cap_logs[2]['log_level'] == 'info'

            assert cap_logs[3]['_function'] == 'sample_sync_function'
            assert cap_logs[3]['_script'] == 'test_logger.py'
            assert isinstance(cap_logs[3]['duration'], str)
            assert (
                'Decorator success: sample_sync_function'
                in cap_logs[3]['event']
            )
            assert cap_logs[1]['log_level'] == 'info'

    def test_exception_to_string(self) -> None:
        from risclog.logging.decorators import exception_to_string

        try:
            raise ValueError('An error occurred')
        except Exception as exc:
            exc_string = exception_to_string(exc)
        assert 'An error occurred' in exc_string

    def test_debug_log(self, logger1: HybridLogger):
        with capture_logs() as cap_logs:
            logger1.debug('This is a debug message')

        assert cap_logs == [
            {'event': 'This is a debug message', 'log_level': 'debug'}
        ]

    def test_info_log(self, logger2: HybridLogger):
        with capture_logs() as cap_logs:
            logger2.info('This is a info message')

        assert cap_logs == [
            {'event': 'This is a info message', 'log_level': 'info'}
        ]

    def test_warning_log(self, logger1: HybridLogger):
        with capture_logs() as cap_logs:
            logger1.warning('This is a warning message')

        assert cap_logs == [
            {'event': 'This is a warning message', 'log_level': 'warning'}
        ]

    def test_error_log(self, logger2: HybridLogger):
        with capture_logs() as cap_logs:
            logger2.error('This is a error message')

        assert cap_logs == [
            {'event': 'This is a error message', 'log_level': 'error'}
        ]

    def test_critical_log(self, logger1: HybridLogger):
        with capture_logs() as cap_logs:
            logger1.critical('This is a critical message')

        assert cap_logs == [
            {'event': 'This is a critical message', 'log_level': 'critical'}
        ]

    def test_fatal_log(self, logger2: HybridLogger):
        with capture_logs() as cap_logs:
            logger2.fatal('This is a fatal message')

        assert cap_logs == [
            {'event': 'This is a fatal message', 'log_level': 'critical'}
        ]

    def test_exception_log(self, logger1: HybridLogger):
        with capture_logs() as cap_logs:
            logger1.exception('This is a exception message')

        assert cap_logs == [
            {
                'event': 'This is a exception message',
                'exc_info': True,
                'log_level': 'error',
            }
        ]

    @patch('risclog.logging.sender.smtp_email_send')
    def test_exception_logging_with_email(self, mock_smtp_send):
        @log_decorator(send_email=True)
        def faulty_func():
            raise ValueError('This is an error')

        with capture_logs() as cap_logs:
            with pytest.raises(ValueError, match='This is an error'):
                faulty_func()

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

        assert cap_logs[1]['_function'] == 'faulty_func'
        assert cap_logs[1]['_script'] == 'test_logger.py'
        assert 'Decorator error in faulty_func' in cap_logs[1]['event']
        assert cap_logs[1]['log_level'] == 'error'

    @patch('risclog.logging.sender.smtp_email_send')
    @pytest.mark.asyncio
    async def test_async_exception_logging_with_email(self, mock_smtp_send):
        @log_decorator(send_email=True)
        async def faulty_async_func():
            raise ValueError('This is an async error')

        with capture_logs() as cap_logs:
            with pytest.raises(ValueError, match='This is an async error'):
                await faulty_async_func()

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

        assert cap_logs[1]['_function'] == 'faulty_async_func'
        assert cap_logs[1]['_script'] == 'test_logger.py'
        assert 'Decorator error in faulty_async_func' in cap_logs[1]['event']
        assert cap_logs[1]['log_level'] == 'error'

    def test_inline_and_decorator_have_same_id_in_logs(
        self, logger1: HybridLogger
    ) -> None:
        @log_decorator
        def test_func():
            logger1.info('This is a message from the decorator')

        with capture_logs() as cap_logs:
            test_func()

        log_text1 = cap_logs[0]['event']
        log_text1_id = re.findall(r'\d+', log_text1)
        log_text2 = cap_logs[2]['event']
        log_text2_id = re.findall(r'\d+', log_text2)

        assert log_text1_id == log_text2_id

    def test_set_level_int(self, logger1: HybridLogger) -> None:
        logger1.set_level(logging.DEBUG)

        named_logger = logging.getLogger('test_logger_1')
        root_logger = logging.getLogger()

        assert named_logger.level == logging.DEBUG
        assert root_logger.level == logging.DEBUG

    def test_set_level_str(self, logger1: HybridLogger) -> None:
        logger1.set_level('info')

        named_logger = logging.getLogger('test_logger_1')
        root_logger = logging.getLogger()

        assert named_logger.level == logging.INFO
        assert root_logger.level == logging.INFO

    def test_add_file_handler_sync_only(self):
        hybrid_logger = HybridLogger('test_logger')
        standard_logger = logging.getLogger('test_logger')
        standard_logger.handlers = []
        hybrid_logger.sync_logger = standard_logger
        hybrid_logger.async_logger = None

        temp_file = tempfile.NamedTemporaryFile(delete=False)
        temp_file.close()
        try:
            hybrid_logger.add_file_handler(temp_file.name, level=logging.DEBUG)
            file_handlers = [
                h
                for h in standard_logger.handlers
                if isinstance(h, logging.FileHandler)
            ]
            assert len(file_handlers) > 0

            file_handler = file_handlers[0]
            assert file_handler.level == logging.DEBUG
            assert file_handler.formatter is not None
            if ProcessorFormatter:
                assert isinstance(file_handler.formatter, ProcessorFormatter)
        finally:
            os.remove(temp_file.name)

    def test_add_file_handler_sync_and_async(self):
        hybrid_logger = HybridLogger('test_logger')
        sync_logger = logging.getLogger('test_logger_sync')
        async_logger = logging.getLogger('test_logger_async')
        sync_logger.handlers = []
        async_logger.handlers = []
        hybrid_logger.sync_logger = sync_logger
        hybrid_logger.async_logger = async_logger

        temp_file = tempfile.NamedTemporaryFile(delete=False)
        temp_file.close()
        try:
            hybrid_logger.add_file_handler(
                temp_file.name, level=logging.WARNING
            )
            sync_handlers = [
                h
                for h in sync_logger.handlers
                if isinstance(h, logging.FileHandler)
            ]

            assert len(sync_handlers) > 0
            assert sync_handlers[0].level == logging.WARNING

            async_handlers = [
                h
                for h in async_logger.handlers
                if isinstance(h, logging.FileHandler)
            ]
            assert len(async_handlers) > 0
            assert async_handlers[0].level == logging.WARNING
        finally:
            os.remove(temp_file.name)
