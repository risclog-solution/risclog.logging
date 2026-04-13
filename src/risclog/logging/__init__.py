from typing import Callable

from risclog.logging.decorators import log_decorator
from risclog.logging.log import HybridLogger, get_logger as old_get_logger
from risclog.logging.log import getLogger as logger

getLogger: Callable[[str], HybridLogger] = logger

# DeprecationWarning: 'get_logger' is obsolete and will be removed from version 2.1.0. Please use 'getLogger' instead.
get_logger: Callable[[str], HybridLogger] = old_get_logger

__all__ = ["getLogger", "get_logger", "log_decorator"]
