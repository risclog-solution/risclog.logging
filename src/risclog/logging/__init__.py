import asyncio
import inspect
import logging
import os
import smtplib
import sys
import traceback
from concurrent.futures import ThreadPoolExecutor
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from functools import partial, wraps
from pathlib import Path
from typing import Coroutine

import structlog
from structlog.types import Processor


def rename_event_to_message(_, __, event_dict):
    if 'event' in event_dict:
        event_dict['message'] = event_dict.pop('event')
    keys_at_end = ['referer']
    sorted_keys = sorted(
        event_dict.keys(), key=lambda x: (x in keys_at_end, x)
    )
    sorted_dict = {k: event_dict[k] for k in sorted_keys}
    return sorted_dict


class RiscLoggerSingletonMeta(type):
    _instances = {}

    def __call__(cls, *args, **kwargs):
        if cls not in cls._instances:
            cls._instances[cls] = super(RiscLoggerSingletonMeta, cls).__call__(
                *args, **kwargs
            )

        return cls._instances[cls]


class RiscLogger(metaclass=RiscLoggerSingletonMeta):
    def __init__(self, name: str = None) -> None:
        self.logger = structlog.stdlib.get_logger(name)
        self.logger_name = name

    def __new__(cls, *args, **kwargs):
        cls._configure_logger()
        instance = super().__new__(cls)

        return instance

    @classmethod
    def _configure_logger(cls):
        LEVELS = {
            'CRITICAL': 50,
            'FATAL': 50,
            'ERROR': 40,
            'WARNING': 30,
            'WARN': 30,
            'INFO': 20,
            'DEBUG': 10,
        }

        log_level = LEVELS.get(os.getenv('LOG_LEVEL'), 20)

        timestamper = structlog.processors.TimeStamper(fmt='%Y-%m-%d %H:%M:%S')
        shared_processors: list[Processor] = [
            structlog.contextvars.merge_contextvars,
            structlog.stdlib.add_logger_name,
            structlog.stdlib.add_log_level,
            structlog.stdlib.PositionalArgumentsFormatter(),
            structlog.stdlib.ExtraAdder(),
            timestamper,
            structlog.processors.StackInfoRenderer(),
            rename_event_to_message,
        ]

        structlog.configure(
            logger_factory=structlog.stdlib.LoggerFactory(),
            processors=shared_processors
            + [
                structlog.stdlib.ProcessorFormatter.wrap_for_formatter,
            ],
            wrapper_class=structlog.stdlib.BoundLogger,
            cache_logger_on_first_use=True,
        )

        log_renderer: structlog.types.Processor
        log_renderer = structlog.dev.ConsoleRenderer()
        formatter = structlog.stdlib.ProcessorFormatter(
            foreign_pre_chain=shared_processors,
            processors=[
                structlog.stdlib.ProcessorFormatter.remove_processors_meta,
                log_renderer,
            ],
        )
        # set logger Level from asyncio package to WARNING
        logging.getLogger('asyncio').setLevel(logging.WARNING)
        handler = logging.StreamHandler()
        handler.setFormatter(formatter)
        root_logger = logging.getLogger()
        root_logger.addHandler(handler)
        root_logger.setLevel(log_level)

        for _log in ['uvicorn', 'uvicorn.error']:
            logging.getLogger(_log).handlers.clear()
            logging.getLogger(_log).propagate = True

        logging.getLogger('uvicorn.access').handlers.clear()
        logging.getLogger('uvicorn.access').propagate = False

        def handle_exception(exc_type, exc_value, exc_traceback):
            if issubclass(exc_type, KeyboardInterrupt):
                sys.__excepthook__(exc_type, exc_value, exc_traceback)
                return False

        sys.excepthook = handle_exception

    async def _async_log(
        self,
        level: str,
        msg: str,
        sender: str,
        function_id: int,
        *args,
        **kwargs,
    ) -> Coroutine:
        await asyncio.sleep(0)
        func = getattr(self.logger, level.lower())
        sender = kwargs.get('sender') if kwargs.get('sender') else sender
        kwargs = {**{'__id': function_id, '__sender': sender}, **kwargs}
        func(msg, *args, **kwargs)

    def _log(
        self,
        level: str,
        msg: str,
        function_id: int,
        sender: str = 'inline',
        *args,
        **kwargs,
    ) -> Coroutine:
        try:
            loop = asyncio.get_running_loop()
        except RuntimeError:
            loop = None

        if loop and loop.is_running():
            return self._async_log(
                level=level,
                msg=msg,
                sender=sender,
                function_id=function_id,
                *args,
                **kwargs,
            )
        else:
            return asyncio.run(
                self._async_log(
                    level=level,
                    msg=msg,
                    sender=sender,
                    function_id=function_id,
                    *args,
                    **kwargs,
                )
            )

    @staticmethod
    def set_caller_id(func):
        def wrapper(*args, **kwargs):
            if 'function_id' not in kwargs:
                caller_frame = inspect.stack()[1]
                caller_name = caller_frame.function
                function_id = id(caller_name)
                kwargs['function_id'] = function_id

            return func(*args, **kwargs)

        return wrapper

    @set_caller_id
    def debug(
        self, msg: str = None, function_id: int = None, *args, **kwargs
    ) -> Coroutine:
        return self._log(
            'debug', msg, function_id=function_id, *args, **kwargs
        )

    @set_caller_id
    def info(
        self, msg: str = None, function_id: int = None, *args, **kwargs
    ) -> Coroutine:
        return self._log('info', msg, function_id=function_id, *args, **kwargs)

    @set_caller_id
    def warning(
        self, msg: str = None, function_id: int = None, *args, **kwargs
    ) -> Coroutine:
        return self._log(
            'warning', msg, function_id=function_id, *args, **kwargs
        )

    @set_caller_id
    def fatal(
        self, msg: str = None, function_id: int = None, *args, **kwargs
    ) -> Coroutine:
        return self._log(
            'fatal', msg, function_id=function_id, *args, **kwargs
        )

    @set_caller_id
    def critical(
        self, msg: str = None, function_id: int = None, *args, **kwargs
    ) -> Coroutine:
        return self._log(
            'critical', msg, function_id=function_id, *args, **kwargs
        )

    @set_caller_id
    def exception(
        self, msg: str = None, function_id: int = None, *args, **kwargs
    ) -> Coroutine:
        return self._log(
            'error', msg, function_id=function_id, *args, **kwargs
        )

    @set_caller_id
    def error(
        self, msg: str = None, function_id: int = None, *args, **kwargs
    ) -> Coroutine:
        return self._log(
            'error', msg, function_id=function_id, *args, **kwargs
        )

    @classmethod
    def decorator(cls, method=None, send_email=False):
        if method is None:
            return lambda m: cls.decorator(m, send_email)

        function_id = id(method)
        if not cls._instances:
            logger = cls(name=__name__)
        else:
            logger = cls._instances[cls]

        if inspect.iscoroutinefunction(method):

            @wraps(method)
            async def async_wrapper(*args, **kwargs):
                try:
                    script = Path(inspect.getfile(method)).name
                    structlog.contextvars.bind_contextvars(
                        _function=method.__name__,
                        _script=script,
                    )

                    frame = inspect.currentframe()
                    _, _, _, frame_values = inspect.getargvalues(frame)
                    args_dict = {f'arg_{i}': arg for i, arg in enumerate(args)}
                    params = {**args_dict, **frame_values.get('kwargs')}

                    if params:
                        await logger.info(
                            f'Method called: "{method.__name__}" with: "{params}"',
                            function_id=function_id,
                            sender='async_logging_decorator',
                        )
                    else:
                        await logger.info(
                            f'Method "{method.__name__}" called with no arguments.',
                            sender='async_logging_decorator',
                            function_id=function_id,
                        )

                    value = await method(*args, **kwargs)
                    await logger.info(
                        f'Method "{method.__name__}" returned: "{value}"',
                        sender='async_logging_decorator',
                        function_id=function_id,
                    )
                    return value
                except Exception as exc:
                    message = f'Exception occurred in method: {method.__name__}, exception: {exc}'
                    if send_email:
                        with ThreadPoolExecutor() as executor:
                            message = f'{message}\n\n\n{exception_to_string(excp=exc)}'
                            executor.submit(
                                partial(
                                    smtp_email_send,
                                    message=message,
                                    logger_name=logger.logger_name,
                                )
                            )
                    await logger.exception(
                        message,
                        sender='async_logging_decorator',
                        function_id=function_id,
                    )
                    raise exc
                finally:
                    structlog.contextvars.unbind_contextvars(
                        '_function', '_script'
                    )

            return async_wrapper
        else:

            @wraps(method)
            def sync_wrapper(*args, **kwargs):
                try:
                    script = Path(inspect.getfile(method)).name
                    structlog.contextvars.bind_contextvars(
                        _function=method.__name__,
                        _script=script,
                    )

                    frame = inspect.currentframe()
                    _, _, _, frame_values = inspect.getargvalues(frame)
                    args_dict = {f'arg_{i}': arg for i, arg in enumerate(args)}
                    params = {**args_dict, **frame_values.get('kwargs')}

                    if params:
                        logger.info(
                            f'Method called: "{method.__name__}" with: "{params}"',
                            function_id=function_id,
                            sender='logging_decorator',
                        )
                    else:
                        logger.info(
                            f'Method "{method.__name__}" called with no arguments.',
                            sender='logging_decorator',
                            function_id=function_id,
                        )

                    value = method(*args, **kwargs)
                    logger.info(
                        f'Method "{method.__name__}" returned: "{value}"',
                        sender='logging_decorator',
                        function_id=function_id,
                    )
                    return value
                except Exception as exc:
                    message = f'Exception occurred in method: {method.__name__}, exception: {exc}'
                    if send_email:
                        with ThreadPoolExecutor() as executor:
                            message = f'{message}\n\n\n{exception_to_string(excp=exc)}'
                            executor.submit(
                                partial(
                                    smtp_email_send,
                                    message=message,
                                    logger_name=logger.logger_name,
                                )
                            )
                    logger.exception(
                        message,
                        sender='logging_decorator',
                        function_id=function_id,
                    )
                    raise exc
                finally:
                    structlog.contextvars.unbind_contextvars(
                        '_function', '_script'
                    )

            return sync_wrapper


def get_logger(name: str = None):
    if not name:
        frm = inspect.stack()[1]
        mod = inspect.getmodule(frm[0])
        name = mod.__name__
    return RiscLogger(name=name)


def exception_to_string(excp):
    stack = traceback.extract_stack()[:-3] + traceback.extract_tb(
        excp.__traceback__
    )
    pretty = traceback.format_list(stack)
    return ''.join(pretty) + '\n  {} {}'.format(excp.__class__, excp)


def smtp_email_send(message: str, logger_name: str) -> None:
    smtp_user = os.getenv('logging_email_smtp_user')
    smtp_password = os.getenv('logging_email_smtp_password')
    email_to = os.getenv('logging_email_to')
    smtp_server = os.getenv('logging_email_smtp_server')

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
        logger = get_logger(name=logger_name)
        logger.error(
            'Emails cannot be sent because one or more environment variables are not set!'
        )
