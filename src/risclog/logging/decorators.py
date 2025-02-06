from __future__ import annotations

import inspect
import time
import traceback
from concurrent.futures import ThreadPoolExecutor
from functools import partial, wraps
from pathlib import Path

from risclog.logging.log import HybridLogger, getLogger


def exception_to_string(excp: BaseException) -> str:
    stack = traceback.extract_stack()[:-3] + traceback.extract_tb(
        excp.__traceback__
    )
    pretty = traceback.format_list(stack)
    return ''.join(pretty) + '\n  {} {}'.format(excp.__class__, excp)


def format_args(func, args, kwargs):
    param_names = list(inspect.signature(func).parameters.keys())
    formatted_args = [
        f'{name}:{type(value).__name__}={value}'
        for name, value in zip(param_names, args)
    ]
    formatted_kwargs = [
        f'{key}:{type(value).__name__}={value}'
        for key, value in kwargs.items()
    ]

    return tuple(formatted_args + formatted_kwargs)


def log_decorator(func=None, send_email=False):
    from risclog.logging.sender import smtp_email_send

    if func is None:
        return lambda m: log_decorator(m, send_email)

    logger: HybridLogger = getLogger(func.__module__)
    method_id = id(func.__name__)

    if inspect.iscoroutinefunction(func):

        @wraps(func)
        async def wrapper(*args, **kwargs):
            script = Path(inspect.getfile(func)).name
            formatted_args = format_args(func, args, kwargs)
            start_time = time.perf_counter()

            await logger.info(
                f'[{method_id} Decorator start: {func.__name__}]',
                _function=func.__name__,
                _script=script,
                args=formatted_args,
                kwargs=kwargs,
            )

            try:
                result = await func(*args, **kwargs)
                end_time = time.perf_counter()
                duration = end_time - start_time
                await logger.info(
                    f'[{method_id} Decorator success: {func.__name__}]',
                    _function=func.__name__,
                    _script=script,
                    result=result,
                    duration=f'{duration:.5f}sec',
                )

                return result
            except Exception as e:
                msg = (f'[{method_id} Decorator error in {func.__name__}]',)
                if send_email:
                    with ThreadPoolExecutor() as executor:
                        message = f'{msg}\n\n\n{exception_to_string(excp=e)}'
                        executor.submit(
                            partial(
                                smtp_email_send,
                                message=message,
                                logger_name=logger.name,
                            )
                        )

                await logger.error(
                    msg,
                    _function=func.__name__,
                    _script=script,
                    error=str(e),
                )
                raise

    else:

        @wraps(func)
        def wrapper(*args, **kwargs):
            script = Path(inspect.getfile(func)).name
            formatted_args = format_args(func, args, kwargs)
            start_time = time.perf_counter()

            logger.info(
                f'[{method_id} Decorator start: {func.__name__}]',
                _function=func.__name__,
                _script=script,
                args=formatted_args,
                kwargs=kwargs,
            )
            try:
                result = func(*args, **kwargs)
                end_time = time.perf_counter()
                duration = end_time - start_time
                logger.info(
                    f'[{method_id} Decorator success: {func.__name__}]',
                    _function=func.__name__,
                    _script=script,
                    result=result,
                    duration=f'{duration:.5f}sec',
                )
                return result
            except Exception as e:
                msg = (f'[{method_id} Decorator error in {func.__name__}]',)
                if send_email:
                    with ThreadPoolExecutor() as executor:
                        message = f'{msg}\n\n\n{exception_to_string(excp=e)}'
                        executor.submit(
                            partial(
                                smtp_email_send,
                                message=message,
                                logger_name=logger.name,
                            )
                        )

                logger.error(
                    msg,
                    _function=func.__name__,
                    _script=script,
                    error=str(e),
                )
                raise

    return wrapper
