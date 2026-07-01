from __future__ import annotations

import inspect
import logging
import os
import re
import time
import traceback
from collections.abc import Mapping
from concurrent.futures import ThreadPoolExecutor
from functools import partial, wraps
from pathlib import Path
from typing import Any, Callable, TypeVar, cast, overload

from typing_extensions import ParamSpec

from risclog.logging.log import HybridLogger, getLogger

P = ParamSpec("P")
R = TypeVar("R")

REDACTED_VALUE = "***REDACTED***"
TRUNCATED_VALUE = "...[truncated]"
MAX_STRING_LENGTH = 500
MAX_COLLECTION_ITEMS = 20
MAX_DEPTH = 4
MIN_SECRET_VALUE_LENGTH = 8

SENSITIVE_FIELD_MARKERS = frozenset(
    {
        "access_key",
        "access_key_id",
        "api_key",
        "apikey",
        "authorization",
        "bearer",
        "client_secret",
        "cookie",
        "credential",
        "credentials",
        "csrf",
        "jwt",
        "passwd",
        "password",
        "private_key",
        "pwd",
        "refresh_token",
        "secret",
        "secret_access_key",
        "secret_key",
        "session",
        "smtp_password",
        "token",
    }
)

_INLINE_SECRET_KEYS = (
    r"access[_-]?key(?:[_-]?id)?|api[_-]?key|access[_-]?token|"
    r"authorization|bearer|client[_-]?secret|cookie|jwt|passwd|password|"
    r"pwd|refresh[_-]?token|secret(?:[_-]?access)?[_-]?key|secret|session|"
    r"token"
)

_QUOTED_INLINE_SECRET_RE = re.compile(
    rf"(?i)([\"']?\b(?:{_INLINE_SECRET_KEYS})\b[\"']?\s*[:=]\s*)"
    r"([\"'])(.*?)(\2)"
)

_INLINE_SECRET_RE = re.compile(
    rf"(?i)([\"']?\b(?:{_INLINE_SECRET_KEYS})\b[\"']?\s*[:=]\s*)"
    r"([\"']?)([^\"'\s,;&}]+)([\"']?)"
)

_AUTHORIZATION_RE = re.compile(
    r"(?i)([\"']?\bauthorization\b[\"']?\s*[:=]\s*)([\"']?)"
    r"(?:bearer\s+|basic\s+)?([^\"'\s,;&}]+)([\"']?)"
)

_BEARER_TOKEN_RE = re.compile(r"(?i)\b(bearer\s+)([a-z0-9._~+/=-]+)")

_URL_CREDENTIAL_RE = re.compile(r"(?i)([a-z][a-z0-9+.-]*://[^/\s:@]+:)([^@\s/]+)(@)")

_PRIVATE_KEY_BLOCK_RE = re.compile(
    r"-----BEGIN [A-Z0-9 ]*PRIVATE KEY-----.*?"
    r"-----END [A-Z0-9 ]*PRIVATE KEY-----",
    re.DOTALL,
)


class LogValueSanitizer:
    def __init__(self, environ: Mapping[str, str] | None = None) -> None:
        self.environ = os.environ if environ is None else environ

    def sanitize(
        self,
        value: Any,
        *,
        field_name: Any = None,
        max_string_length: int | None = None,
        max_collection_items: int | None = None,
        max_depth: int | None = None,
        _depth: int = 0,
        _seen: set[int] | None = None,
    ) -> Any:
        max_string_length = self._limit(
            max_string_length,
            "LOG_DECORATOR_MAX_STRING_LENGTH",
            MAX_STRING_LENGTH,
        )
        max_collection_items = self._limit(
            max_collection_items,
            "LOG_DECORATOR_MAX_COLLECTION_ITEMS",
            MAX_COLLECTION_ITEMS,
        )
        max_depth = self._limit(
            max_depth,
            "LOG_DECORATOR_MAX_DEPTH",
            MAX_DEPTH,
        )

        if self.is_sensitive_field_name(field_name):
            return REDACTED_VALUE

        if _depth >= max_depth:
            return f"<{type(value).__name__} depth limit reached>"

        if isinstance(value, str):
            return self.truncate_string(
                self.redact_inline_secrets(value),
                max_string_length,
            )

        if isinstance(value, (bytes, bytearray)):
            return f"<{type(value).__name__} length={len(value)}>"

        if value is None or isinstance(value, (bool, int, float)):
            return value

        if _seen is None:
            _seen = set()

        value_id = id(value)
        if value_id in _seen:
            return f"<{type(value).__name__} recursion>"

        if isinstance(value, Mapping):
            return self._sanitize_mapping(
                value,
                max_string_length,
                max_collection_items,
                max_depth,
                _depth,
                _seen,
            )

        if isinstance(value, tuple):
            sanitized_items = self._sanitize_iterable(
                value,
                max_string_length,
                max_collection_items,
                max_depth,
                _depth,
                _seen,
            )
            return tuple(sanitized_items)

        if isinstance(value, list):
            return self._sanitize_iterable(
                value,
                max_string_length,
                max_collection_items,
                max_depth,
                _depth,
                _seen,
            )

        if isinstance(value, (set, frozenset)):
            return self._sanitize_iterable(
                list(value),
                max_string_length,
                max_collection_items,
                max_depth,
                _depth,
                _seen,
            )

        return self.truncate_string(
            self.redact_inline_secrets(self.safe_repr(value)),
            max_string_length,
        )

    def is_sensitive_field_name(self, field_name: Any) -> bool:
        if field_name is None:
            return False

        normalized = self.safe_to_string(field_name).lower().replace("-", "_")
        markers = SENSITIVE_FIELD_MARKERS | self.configured_field_markers()
        return any(marker in normalized for marker in markers)

    def redact_inline_secrets(self, value: str) -> str:
        value = self.redact_known_secret_values(value)
        value = _PRIVATE_KEY_BLOCK_RE.sub(REDACTED_VALUE, value)
        value = _AUTHORIZATION_RE.sub(
            lambda match: f"{match.group(1)}{match.group(2)}"
            f"{REDACTED_VALUE}{match.group(4)}",
            value,
        )
        value = _BEARER_TOKEN_RE.sub(
            lambda match: f"{match.group(1)}{REDACTED_VALUE}",
            value,
        )
        value = _QUOTED_INLINE_SECRET_RE.sub(
            lambda match: f"{match.group(1)}{match.group(2)}"
            f"{REDACTED_VALUE}{match.group(4)}",
            value,
        )
        value = _INLINE_SECRET_RE.sub(
            lambda match: f"{match.group(1)}{match.group(2)}"
            f"{REDACTED_VALUE}{match.group(4)}",
            value,
        )
        return _URL_CREDENTIAL_RE.sub(
            lambda match: f"{match.group(1)}{REDACTED_VALUE}{match.group(3)}",
            value,
        )

    def redact_known_secret_values(self, value: str) -> str:
        for secret_value in self.known_secret_values_from_env():
            value = value.replace(secret_value, REDACTED_VALUE)
        return value

    def known_secret_values_from_env(self) -> list[str]:
        min_secret_value_length = self.env_int(
            "LOG_DECORATOR_MIN_SECRET_VALUE_LENGTH",
            MIN_SECRET_VALUE_LENGTH,
        )
        configured_names = self.configured_env_names()
        secret_values = set()

        for name, value in self.environ.items():
            if not value or len(value) < min_secret_value_length:
                continue
            if name in configured_names or self.is_sensitive_field_name(name):
                secret_values.add(value)

        return sorted(secret_values, key=len, reverse=True)

    def configured_field_markers(self) -> set[str]:
        configured_markers = self.environ.get("LOG_DECORATOR_REDACT_KEYS", "")
        return {
            marker.strip().lower().replace("-", "_")
            for marker in configured_markers.split(",")
            if marker.strip()
        }

    def configured_env_names(self) -> set[str]:
        configured_names = self.environ.get(
            "LOG_DECORATOR_REDACT_ENV_VARS",
            "",
        )
        return {name.strip() for name in configured_names.split(",") if name.strip()}

    def env_int(self, name: str, default: int) -> int:
        raw_value = self.environ.get(name)
        if raw_value is None:
            return default
        try:
            value = int(raw_value)
        except ValueError:
            return default
        return max(0, value)

    @staticmethod
    def safe_to_string(value: Any) -> str:
        try:
            return str(value)
        except Exception:
            return f"<{type(value).__name__} string failed>"

    @staticmethod
    def safe_repr(value: Any) -> str:
        try:
            return repr(value)
        except Exception:
            return f"<{type(value).__name__} repr failed>"

    @staticmethod
    def truncate_string(value: str, max_string_length: int) -> str:
        if len(value) <= max_string_length:
            return value

        return f"{value[:max_string_length]}{TRUNCATED_VALUE}(chars={len(value)})"

    def _limit(
        self,
        configured_value: int | None,
        env_name: str,
        default: int,
    ) -> int:
        if configured_value is not None:
            return configured_value
        return self.env_int(env_name, default)

    def _sanitize_mapping(
        self,
        value: Mapping[Any, Any],
        max_string_length: int,
        max_collection_items: int,
        max_depth: int,
        depth: int,
        seen: set[int],
    ) -> dict[Any, Any]:
        seen.add(id(value))
        sanitized_items = []

        for index, (key, item) in enumerate(value.items()):
            if index >= max_collection_items:
                sanitized_items.append((TRUNCATED_VALUE, f"items={len(value)}"))
                break
            sanitized_items.append(
                (
                    key,
                    self.sanitize(
                        item,
                        field_name=key,
                        max_string_length=max_string_length,
                        max_collection_items=max_collection_items,
                        max_depth=max_depth,
                        _depth=depth + 1,
                        _seen=seen,
                    ),
                )
            )

        seen.remove(id(value))
        return dict(sanitized_items)

    def _sanitize_iterable(
        self,
        value: list[Any] | tuple[Any, ...],
        max_string_length: int,
        max_collection_items: int,
        max_depth: int,
        depth: int,
        seen: set[int],
    ) -> list[Any]:
        seen.add(id(value))
        # Used for complex iterable values: sanitize the configured prefix
        # and mark skipped items.
        sanitized_items = [
            self.sanitize(
                item,
                max_string_length=max_string_length,
                max_collection_items=max_collection_items,
                max_depth=max_depth,
                _depth=depth + 1,
                _seen=seen,
            )
            for item in value[:max_collection_items]
        ]
        seen.remove(id(value))

        if len(value) > max_collection_items:
            sanitized_items.append(f"{TRUNCATED_VALUE}(items={len(value)})")
        return sanitized_items


DEFAULT_LOG_VALUE_SANITIZER = LogValueSanitizer()


def is_sensitive_field_name(field_name: Any) -> bool:
    return DEFAULT_LOG_VALUE_SANITIZER.is_sensitive_field_name(field_name)


def sanitize_log_value(
    value: Any,
    *,
    field_name: Any = None,
    max_string_length: int | None = None,
    max_collection_items: int | None = None,
    max_depth: int | None = None,
    _depth: int = 0,
    _seen: set[int] | None = None,
) -> Any:
    return DEFAULT_LOG_VALUE_SANITIZER.sanitize(
        value,
        field_name=field_name,
        max_string_length=max_string_length,
        max_collection_items=max_collection_items,
        max_depth=max_depth,
        _depth=_depth,
        _seen=_seen,
    )


def exception_to_string(excp: BaseException) -> str:
    stack = traceback.extract_stack()[:-3] + traceback.extract_tb(excp.__traceback__)
    pretty = traceback.format_list(stack)
    return "".join(pretty) + "\n  {} {}".format(
        excp.__class__,
        DEFAULT_LOG_VALUE_SANITIZER.safe_to_string(excp),
    )


def exception_to_log_string(excp: BaseException, prefix: Any = "") -> str:
    max_exception_length = DEFAULT_LOG_VALUE_SANITIZER.env_int(
        "LOG_DECORATOR_MAX_EXCEPTION_LENGTH",
        DEFAULT_LOG_VALUE_SANITIZER.env_int(
            "LOG_DECORATOR_MAX_STRING_LENGTH",
            8000,
        ),
    )
    message = "{}\n\n\n{}".format(
        DEFAULT_LOG_VALUE_SANITIZER.safe_to_string(prefix),
        exception_to_string(excp=excp),
    )
    return cast(
        str,
        sanitize_log_value(
            message,
            max_string_length=max_exception_length,
        ),
    )


def format_args(func: Any, args: tuple, kwargs: dict) -> tuple:  # type: ignore[type-arg]
    param_names = list(inspect.signature(func).parameters.keys())
    formatted_args = [
        f"{name}:{type(value).__name__}={sanitize_log_value(value, field_name=name)}"
        for name, value in zip(param_names, args)
    ]
    formatted_kwargs = [
        f"{key}:{type(value).__name__}={sanitize_log_value(value, field_name=key)}"
        for key, value in kwargs.items()
    ]

    return tuple(formatted_args + formatted_kwargs)


@overload
def log_decorator(func: Callable[P, R], send_email: bool = False) -> Callable[P, R]: ...


@overload
def log_decorator(
    func: None = None, send_email: bool = False
) -> Callable[[Callable[P, R]], Callable[P, R]]: ...


def log_decorator(
    func: Callable[P, R] | None = None, send_email: bool = False
) -> Callable[P, R] | Callable[[Callable[P, R]], Callable[P, R]]:
    from risclog.logging.sender import smtp_email_send

    if func is None:

        def _decorator(method: Callable[P, R]) -> Callable[P, R]:
            return log_decorator(method, send_email)

        return _decorator

    logger: HybridLogger = getLogger(func.__module__)
    method_id = id(func.__name__)

    if inspect.iscoroutinefunction(func):

        @wraps(func)
        async def wrapper(*args: P.args, **kwargs: P.kwargs) -> Any:
            if not logging.getLogger(logger.name).isEnabledFor(logging.DEBUG):
                try:
                    return await func(*args, **kwargs)
                except Exception as e:
                    if send_email:
                        with ThreadPoolExecutor() as executor:
                            executor.submit(
                                partial(
                                    smtp_email_send,
                                    message=exception_to_log_string(
                                        e,
                                        prefix=e,
                                    ),
                                    logger_name=logger.name,
                                )
                            )
                    raise
            script = Path(inspect.getfile(func)).name
            formatted_args = format_args(func, args, kwargs)
            start_time = time.perf_counter()

            await logger.info(
                f"[{method_id} Decorator start: {func.__name__}]",
                _function=func.__name__,
                _script=script,
                args=formatted_args,
                kwargs=sanitize_log_value(kwargs),
            )

            try:
                result = await func(*args, **kwargs)
                end_time = time.perf_counter()
                duration = end_time - start_time
                await logger.info(
                    f"[{method_id} Decorator success: {func.__name__}]",
                    _function=func.__name__,
                    _script=script,
                    result=sanitize_log_value(result),
                    duration=f"{duration:.5f}sec",
                )

                return result
            except Exception as e:
                msg = (f"[{method_id} Decorator error in {func.__name__}]",)
                if send_email:
                    with ThreadPoolExecutor() as executor:
                        executor.submit(
                            partial(
                                smtp_email_send,
                                message=exception_to_log_string(
                                    e,
                                    prefix=msg,
                                ),
                                logger_name=logger.name,
                            )
                        )

                await logger.error(
                    msg,
                    _function=func.__name__,
                    _script=script,
                    error=sanitize_log_value(str(e)),
                )
                raise

    else:

        @wraps(func)
        def wrapper(*args: P.args, **kwargs: P.kwargs) -> R:
            if not logging.getLogger(logger.name).isEnabledFor(logging.DEBUG):
                try:
                    return func(*args, **kwargs)
                except Exception as e:
                    if send_email:
                        with ThreadPoolExecutor() as executor:
                            executor.submit(
                                partial(
                                    smtp_email_send,
                                    message=exception_to_log_string(
                                        e,
                                        prefix=e,
                                    ),
                                    logger_name=logger.name,
                                )
                            )
                    raise
            script = Path(inspect.getfile(func)).name
            formatted_args = format_args(func, args, kwargs)
            start_time = time.perf_counter()

            logger.info(
                f"[{method_id} Decorator start: {func.__name__}]",
                _function=func.__name__,
                _script=script,
                args=formatted_args,
                kwargs=sanitize_log_value(kwargs),
            )
            try:
                result = func(*args, **kwargs)
                end_time = time.perf_counter()
                duration = end_time - start_time
                logger.info(
                    f"[{method_id} Decorator success: {func.__name__}]",
                    _function=func.__name__,
                    _script=script,
                    result=sanitize_log_value(result),
                    duration=f"{duration:.5f}sec",
                )
                return result
            except Exception as e:
                msg = (f"[{method_id} Decorator error in {func.__name__}]",)
                if send_email:
                    with ThreadPoolExecutor() as executor:
                        executor.submit(
                            partial(
                                smtp_email_send,
                                message=exception_to_log_string(
                                    e,
                                    prefix=msg,
                                ),
                                logger_name=logger.name,
                            )
                        )

                logger.error(
                    msg,
                    _function=func.__name__,
                    _script=script,
                    error=sanitize_log_value(str(e)),
                )
                raise

    return cast(Callable[P, R], wrapper)
