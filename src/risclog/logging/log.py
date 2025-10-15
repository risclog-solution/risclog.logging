from __future__ import annotations

import asyncio
import inspect
import logging
import os
import warnings
from functools import lru_cache, partial, wraps

import structlog
from structlog.dev import ConsoleRenderer
from structlog.stdlib import ProcessorFormatter

# -------------------------------
# 1) Basis-Logging-Konfiguration
# -------------------------------
LEVELS = {
    'CRITICAL': 50,
    'FATAL': 50,
    'ERROR': 40,
    'WARNING': 30,
    'WARN': 30,
    'INFO': 20,
    'DEBUG': 10,
}

log_level = LEVELS.get(os.getenv('LOG_LEVEL'), 40)

logging.basicConfig(
    level=log_level,
    format='%(message)s',
    datefmt='[%Y-%m-%d %H:%M:%S]',
    # Keine Handler hier nötig, wir fügen unten manuell Handler hinzu
    handlers=[],
)

# Entferne Uvicorn-Logger
uvicorn_loggers = ['uvicorn', 'uvicorn.error', 'uvicorn.access']
for logger_name in uvicorn_loggers:
    logger = logging.getLogger(logger_name)
    logger.handlers.clear()
    logger.propagate = False

# Entferne Watchfiles-Logger
logging.getLogger('watchfiles').setLevel(log_level)


# wrapper for structlog.stdlib.filter_by_level
def safe_filter_by_level(logger, method_name, event_dict):
    if logger is None:
        return event_dict
    return structlog.stdlib.filter_by_level(logger, method_name, event_dict)


# -------------------------------
# 2) Prozessoren definieren
# -------------------------------
def get_processors(for_async: bool = False):
    processors = [
        structlog.contextvars.merge_contextvars,
        safe_filter_by_level,
        structlog.stdlib.ExtraAdder(),
        structlog.stdlib.PositionalArgumentsFormatter(),
        structlog.processors.StackInfoRenderer(),
        # Hier KEINE ConsoleRenderer fest verdrahtet,
        # da wir pro Handler einen eigenen Renderer zuweisen
    ]

    if not for_async:
        processors.insert(
            1, structlog.processors.TimeStamper(fmt='%Y-%m-%d %H:%M:%S')
        )
        processors.insert(2, structlog.stdlib.add_log_level)
        processors.insert(3, structlog.stdlib.add_logger_name)

    return processors


structlog.configure(
    processors=get_processors(for_async=False)
    + [
        structlog.stdlib.ProcessorFormatter.wrap_for_formatter,
    ],
    context_class=dict,
    logger_factory=structlog.stdlib.LoggerFactory(),
    wrapper_class=structlog.stdlib.BoundLogger,
    cache_logger_on_first_use=True,
)


def get_async_logger(name: str) -> structlog.BoundLogger:
    return structlog.wrap_logger(
        structlog.get_logger(name),
        wrapper_class=structlog.stdlib.AsyncBoundLogger,
        processors=get_processors(for_async=True),
    )


class HybridLogger:
    def __init__(self, name: str) -> None:
        self.name = name
        self.sync_logger: structlog.BoundLogger = structlog.get_logger(name)
        self.async_logger = None

    def set_level(self, level: int | str) -> None:
        if isinstance(level, str):
            level = getattr(logging, level.upper(), log_level)

        if self.name:
            logging.getLogger(self.name).setLevel(level)
        else:
            logging.getLogger().setLevel(level)

        logging.getLogger().setLevel(level)

    def add_file_handler(self, filename: str, level: int = log_level) -> None:
        file_handler = logging.FileHandler(filename)
        file_handler.setLevel(level)

        file_formatter = ProcessorFormatter(
            processor=ConsoleRenderer(colors=False),
            foreign_pre_chain=[
                structlog.contextvars.merge_contextvars,
                safe_filter_by_level,
                structlog.stdlib.add_log_level,
                structlog.stdlib.PositionalArgumentsFormatter(),
                structlog.processors.StackInfoRenderer(),
            ],
        )
        file_handler.setFormatter(file_formatter)
        py_sync_logger: structlog.BoundLogger = self.sync_logger
        py_sync_logger.addHandler(file_handler)

        if self.async_logger:
            py_async_logger = self.async_logger
            py_async_logger.addHandler(file_handler)

    def __getattr__(self, method_name: str):
        sync_method = getattr(self.sync_logger, method_name)
        function_wrappers = ['sync_wrapper', 'async_wrapper', 'wrapper']

        @wraps(sync_method)
        def sync_wrapper(*args, **kwargs):
            if kwargs.get('function_id', None):
                function_id = kwargs.pop('function_id')
                args = tuple([f'[{function_id} {arg}]' for arg in args])
            else:
                args = tuple([f'{arg}' for arg in args])
            return sync_method(*args, **kwargs)

        def wrapper(*args, **kwargs):
            try:
                loop = asyncio.get_event_loop_policy().get_event_loop()
                if loop.is_running():
                    stack = inspect.stack()
                    caller_frame = stack[1]

                    if caller_frame.function not in function_wrappers:
                        kwargs['function_id'] = id(caller_frame.function)
                    func = partial(sync_wrapper, *args, **kwargs)
                    return loop.run_in_executor(None, func)
                else:
                    return sync_wrapper(*args, **kwargs)
            except RuntimeError:
                stack = inspect.stack()
                caller_frame = stack[1]

                if caller_frame.function not in function_wrappers:
                    kwargs['function_id'] = id(caller_frame.function)

                return sync_wrapper(*args, **kwargs)

        return wrapper

    def decorator(self, send_email: bool = False):
        warnings.warn(
            "'decorator' is deprecated and will be removed from version 1.4.0. Please use 'log_decorator' instead.",
            DeprecationWarning,
            stacklevel=2,
        )
        from risclog.logging import log_decorator

        return partial(log_decorator, send_email=send_email)


# -----------------------------------
# 4) Globaler Logger + Handler
# -----------------------------------
# A) Konsole: mit Farbigem ConsoleRenderer
console_handler = logging.StreamHandler()
console_handler.setLevel(log_level)

console_formatter = ProcessorFormatter(
    processor=ConsoleRenderer(colors=True),
    foreign_pre_chain=[
        structlog.contextvars.merge_contextvars,
        safe_filter_by_level,
        structlog.stdlib.add_log_level,
        structlog.stdlib.PositionalArgumentsFormatter(),
        structlog.processors.StackInfoRenderer(),
    ],
)
console_handler.setFormatter(console_formatter)

root_logger = logging.getLogger()
root_logger.setLevel(log_level)
root_logger.handlers = []
root_logger.addHandler(console_handler)

logging.getLogger('asyncio').setLevel(log_level)


@lru_cache(maxsize=None)
def getLogger(name: str = __name__):
    return HybridLogger(name=name)


def get_logger(name: str = __name__):
    warnings.warn(
        "'get_logger' is obsolete and will be removed from version 1.4.0. Please use 'getLogger' instead.",
        DeprecationWarning,
        stacklevel=2,
    )
    return getLogger(name=name)
