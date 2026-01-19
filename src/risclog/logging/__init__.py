from typing import Any, Callable, TypeVar

from risclog.logging.decorators import log_decorator as logging_decorator
from risclog.logging.log import HybridLogger, get_logger as old_get_logger
from risclog.logging.log import getLogger as logger

F = TypeVar("F", bound=Callable[..., Any])

getLogger: Callable[[str], HybridLogger] = logger
log_decorator: Callable[[F], F] = logging_decorator

# DeprecationWarning: 'get_logger' is obsolete and will be removed from version 2.1.0. Please use 'getLogger' instead.
get_logger: Callable[[str], HybridLogger] = old_get_logger
