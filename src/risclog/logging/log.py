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
    "CRITICAL": 50,
    "FATAL": 50,
    "ERROR": 40,
    "WARNING": 30,
    "WARN": 30,
    "INFO": 20,
    "DEBUG": 10,
}

log_level = LEVELS.get(os.getenv("LOG_LEVEL") or "", 40)

logging.basicConfig(
    level=log_level,
    format="%(message)s",
    datefmt="[%Y-%m-%d %H:%M:%S]",
    # Keine Handler hier nötig, wir fügen unten manuell Handler hinzu
    handlers=[],
)

# Konfigurierbare Logger-Ausschlüsse via Environment-Variable
_DEFAULT_EXCLUDED_LOGGERS = [
    "uvicorn",
    "uvicorn.error",
    "uvicorn.access",
    "watchfiles",
]
_EXCLUDED_LOGGERS_ENV = os.getenv("LOG_EXCLUDED_LOGGERS", "")
EXCLUDED_LOGGERS = (
    _EXCLUDED_LOGGERS_ENV.split(",")
    if _EXCLUDED_LOGGERS_ENV
    else _DEFAULT_EXCLUDED_LOGGERS
)

# Entferne konfigurierte Logger
for logger_name in EXCLUDED_LOGGERS:
    logger_obj = logging.getLogger(logger_name.strip())
    logger_obj.handlers.clear()
    logger_obj.propagate = False
    logger_obj.setLevel(log_level)


# wrapper for structlog.stdlib.filter_by_level
def safe_filter_by_level(logger, method_name, event_dict):  # type: ignore[no-untyped-def]
    if logger is None:
        return event_dict
    return structlog.stdlib.filter_by_level(logger, method_name, event_dict)


# -------------------------------
# 2) Prozessoren definieren
# -------------------------------
def get_processors(for_async: bool = False) -> list:  # type: ignore[type-arg]
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
        processors.insert(1, structlog.processors.TimeStamper(fmt="%Y-%m-%d %H:%M:%S"))
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

    def __getattr__(self, method_name: str):  # type: ignore[no-untyped-def]
        sync_method = getattr(self.sync_logger, method_name)
        function_wrappers = ["sync_wrapper", "async_wrapper", "wrapper"]

        def _get_trace_context() -> dict[str, str | int]:
            """Extrahiert Tracing-Kontext aus dem Call-Stack für bessere Nachverfolgung."""
            stack = inspect.stack()
            # Finde den ersten nicht-wrapper Frame
            for frame_info in stack[2:]:
                if frame_info.function not in function_wrappers:
                    return {
                        "caller_function": frame_info.function,
                        "caller_file": frame_info.filename,
                        "caller_line": frame_info.lineno,
                        "trace_id": id(frame_info.frame),
                    }
            return {}

        @wraps(sync_method)
        def sync_wrapper(*args, **kwargs):  # type: ignore[no-untyped-def]
            trace_context = kwargs.pop("_trace_context", {})
            if trace_context:
                # Ergänze Args mit Trace-Informationen für besseres Debugging
                trace_info = f"[{trace_context.get('trace_id', 'unknown')}:{trace_context.get('caller_function', '?')}]"
                args = tuple([f"{trace_info} {arg}" for arg in args])
            else:
                args = tuple([f"{arg}" for arg in args])
            return sync_method(*args, **kwargs)

        def wrapper(*args, **kwargs):  # type: ignore[no-untyped-def]
            try:
                try:
                    loop = asyncio.get_running_loop()
                except RuntimeError:
                    # No running event loop, use sync wrapper directly
                    return sync_wrapper(*args, **kwargs)
                else:
                    # Event loop is running, execute sync_wrapper in executor
                    func = partial(sync_wrapper, *args, **kwargs)
                    return loop.run_in_executor(None, func)
            except RuntimeError:
                # Fallback: if anything goes wrong, extract trace context and use sync wrapper
                trace_context = _get_trace_context()
                if trace_context:
                    kwargs["_trace_context"] = trace_context
                return sync_wrapper(*args, **kwargs)

        return wrapper

    def decorator(self, send_email: bool = False):  # type: ignore[no-untyped-def]
        warnings.warn(
            "'decorator' is deprecated and will be removed from version 1.4.0. Please use 'log_decorator' instead.",
            DeprecationWarning,
            stacklevel=2,
        )
        from risclog.logging import log_decorator

        return partial(log_decorator, send_email=send_email)  # type: ignore[call-arg]


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

logging.getLogger("asyncio").setLevel(log_level)


@lru_cache(maxsize=None)
def getLogger(name: str = __name__) -> HybridLogger:
    return HybridLogger(name=name)


def get_logger(name: str = __name__) -> HybridLogger:
    warnings.warn(
        "'get_logger' is obsolete and will be removed from version 1.4.0. Please use 'getLogger' instead.",
        DeprecationWarning,
        stacklevel=2,
    )
    return getLogger(name=name)
