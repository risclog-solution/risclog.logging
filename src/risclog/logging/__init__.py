import logging
from typing import Any, Callable, TypeVar

from risclog.logging.decorators import log_decorator as logging_decorator
from risclog.logging.log import get_logger as old_get_logger
from risclog.logging.log import getLogger as logger

F = TypeVar('F', bound=Callable[..., Any])

getLogger: Callable[[str], logging.Logger] = logger
log_decorator: Callable[[F], F] = logging_decorator

# DeprecationWarning: 'get_logger' is obsolete and will be removed from version 2.1.0. Please use 'getLogger' instead.
get_logger: Callable[[str], logging.Logger] = old_get_logger
