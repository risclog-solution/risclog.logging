===================
risclog.logging
===================

.. image:: https://github.com/risclog-solution/risclog.logging/actions/workflows/test.yml/badge.svg
   :target: https://github.com/risclog-solution/risclog.logging/actions/workflows/test.yml
   :alt: CI Status

.. image:: https://img.shields.io/pypi/v/risclog.logging.svg
   :target: https://pypi.python.org/pypi/risclog.logging

The **risclog.logging** package provides a comprehensive solution for structured logging in Python
applications. It combines Python’s built-in logging module with [structlog](https://www.structlog.org/)
to generate detailed and formatted log entries. In this new release, the API has been updated to use:

- **`getLogger`** – the new factory function for creating logger instances (the legacy ``get_logger`` is deprecated).
- **`log_decorator`** – a decorator for automatic logging of function calls, including arguments, return values,
  durations, and exceptions.

Features
========

- **Structured logging:** Combines standard logging with structlog for rich, contextual logs.
- **Synchronous and asynchronous logging:** Use the same API in both sync and async environments.
- **Automatic function logging:** Use the ``log_decorator`` to automatically log function calls and errors.
- **Email notifications:** Optionally send email notifications on exceptions (requires setting specific environment variables).
- **Rich traceback:** Enhanced exception display is provided by default via Rich.
- **Flexible configuration:** Programmatically set log levels and add handlers (e.g. file handlers).

Installation
============

Install via pip:

.. code-block:: bash

    pip install risclog.logging

Configuration and Usage
=======================

Creating a Logger
-----------------

Use the new ``getLogger`` function to obtain a logger. (Note that the old ``get_logger`` is now deprecated.)

.. code-block:: python

    from risclog.logging import getLogger

    logger = getLogger(__name__)
    logger.set_level("DEBUG")  # You can pass a string (e.g. "DEBUG") or a logging constant (logging.DEBUG)

You can also add a file handler to write warnings and above to a file:

.. code-block:: python

    file_logger = logger.add_file_handler('test.log', level=logging.WARNING)

Logging Messages
----------------

Log messages synchronously:

.. code-block:: python

    logger.debug("This is a debug message")
    logger.info("This is an info message")
    logger.warning("This is a warning message")
    logger.error("This is an error message")
    logger.critical("This is a critical message")

Or asynchronously (e.g. within async functions):

.. code-block:: python

    await logger.debug("Async debug message")
    await logger.info("Async info message")
    # etc.

Automatic Function Logging with Decorators
--------------------------------------------

The ``log_decorator`` automatically logs function calls (including arguments, execution time, results,
and any exceptions). It works with both synchronous and asynchronous functions.

.. code-block:: python

    from risclog.logging import getLogger, log_decorator
    import asyncio

    logger = getLogger(__name__)
    logger.set_level("DEBUG")

    @log_decorator
    def sync_function(a, b):
        result = a + b
        return result

    @log_decorator
    async def async_function(a, b):
        await asyncio.sleep(1)
        result = a + b
        return result

Using the Decorator in Classes
------------------------------

You can use the decorator on class methods as well. For example:

.. code-block:: python

    from risclog.logging import getLogger, log_decorator
    import asyncio

    class AwesomeClass:
        def __init__(self):
            self.logger = getLogger("AwesomeLogger")

        @log_decorator
        def class_sync_add(self, a: int, b: int):
            self.logger.warn("Debugging class_sync_add", a=a, b=b)
            self.logger.info("Information in class_sync_add", a=a, b=b)
            self.logger.info("class_sync_add called", a=a, b=b)
            return a + b

        @log_decorator
        async def class_async_add(self, a: int, b: int, c: dict):
            await self.logger.info("class_async_add called", a=a, b=b)
            await self.logger.info("Dependency class name:", c=c['dependency'].__class__.__name__)
            await asyncio.sleep(1)
            result = a + b
            await self.logger.info("class_async_add result", result=result)
            return result

    class DependencyClass:
        pass

Email Notification on Exceptions
---------------------------------

To enable email notifications when an exception occurs, pass ``send_email=True`` to the decorator.
**Remember:** The following environment variables must be set:

- ``logging_email_smtp_user``
- ``logging_email_smtp_password``
- ``logging_email_to``
- ``logging_email_smtp_server``

.. code-block:: python

    @log_decorator(send_email=True)
    def function_with_exception():
        # Your code that might raise an exception
        ...

Rich Traceback Integration
---------------------------

The package now automatically installs a beautiful traceback handler via Rich:

.. code-block:: python

    from rich import traceback
    traceback.install()

This provides enhanced, colored, and more informative tracebacks when errors occur.

Full Example
============

Below is a complete example demonstrating the usage of the new logger, decorators, and asynchronous logging.

.. code-block:: python

    import asyncio
    import logging
    from risclog.logging import getLogger, log_decorator

    # Configure logger
    logger = getLogger(__name__)
    logger.set_level(logging.DEBUG)
    logger.add_file_handler('test.log', level=logging.WARNING)

    @log_decorator
    def sync_function(a, b):
        result = a + b
        return result

    @log_decorator
    async def async_function(a, b):
        await asyncio.sleep(1)
        result = a + b
        return result

    class AwesomeClass:
        def __init__(self):
            self.logger = getLogger("AwesomeLogger")

        @log_decorator
        def class_sync_add(self, a: int, b: int):
            self.logger.warn("Debugging class_sync_add", a=a, b=b)
            self.logger.info("Information in class_sync_add", a=a, b=b)
            self.logger.info("class_sync_add called", a=a, b=b)
            return a + b

        @log_decorator
        async def class_async_add(self, a: int, b: int, c: dict):
            await self.logger.info("class_async_add called", a=a, b=b)
            await self.logger.info("Dependency class name:", c=c['dependency'].__class__.__name__)
            await asyncio.sleep(1)
            result = a + b
            await self.logger.info("class_async_add result", result=result)
            return result

    class DependencyClass:
        pass

    @log_decorator
    def sample_function(*args, **kwargs):
        logger.debug("Debugging sample_function", args=args, kwargs=kwargs)
        logger.info("Called with args", args=args)
        logger.info("Called with kwargs", kwargs=kwargs)

        result = {'sum_args': sum(args) if args else 0, **kwargs}
        logger.info("Result", result=result)
        if result['sum_args'] > 5:
            logger.warning("Sum of arguments is greater than 5", sum=result['sum_args'])

        try:
            1 / 0
        except ZeroDivisionError:
            logger.error("Division by zero error occurred during calculation. Check the input values",
                         exc_info=True)
        return result

    @log_decorator
    def sample_critical_function(*args, **kwargs):
        logger.critical("Critical issue in sample_critical_function", args=args, kwargs=kwargs)
        raise RuntimeError("Simulated critical problem")

    async def main():
        dc = DependencyClass()
        ac = AwesomeClass()
        sync_result = sync_function(3, 5)
        await async_function(4, 6)
        ac.class_sync_add(6, 7)
        await ac.class_async_add(8, 9, {'dependency': dc})
        sample_function(1, 2, 3, name='Alice', age=30)

        try:
            sample_critical_function(10, 20)
        except RuntimeError:
            pass

    if __name__ == '__main__':
        logger.info("Starting main function")
        sync_result = sync_function(3, 5)
        asyncio.run(main())

        # Trigger an exception to test rich traceback formatting:
        raise ValueError("Test exception")

Example Output
==============

Below is an example output generated by running the new logger code:

.. code-block:: bash

    2025-02-07 13:23:18 [info     ] [4311754480 Decorator start: sync_function] [__main__] _function=sync_function _script=all_in_one.py args=('a:int=3', 'b:int=5') kwargs={}
    2025-02-07 13:23:18 [info     ] [4311754480 Decorator success: sync_function] [__main__] _function=sync_function _script=all_in_one.py duration=0.00044sec result=8
    2025-02-07 13:23:19 [info     ] [4311754480 Decorator start: sync_function] [__main__] _function=sync_function _script=all_in_one.py args=('a:int=3', 'b:int=5') kwargs={}
    2025-02-07 13:23:19 [info     ] [4311754480 Decorator success: sync_function] [__main__] _function=sync_function _script=all_in_one.py duration=0.01749sec result=8
    2025-02-07 13:23:19 [info     ] [4311755376 Decorator start: async_function] [__main__] _function=async_function _script=all_in_one.py args=('a:int=4', 'b:int=6') kwargs={}
    2025-02-07 13:23:20 [info     ] [4311755376 Decorator success: async_function] [__main__] _function=async_function _script=all_in_one.py duration=1.00177sec result=10
    2025-02-07 13:23:20 [info     ] [4312228144 Decorator start: class_sync_add] [__main__] _function=class_sync_add _script=all_in_one.py args=('self:AwesomeClass=<__main__.AwesomeClass object at 0x10310b110>', 'a:int=6', 'b:int=7') kwargs={}
    2025-02-07 13:23:20 [warning  ] [4312228144 Debugging class_sync_add] [AwesomeLogger] a=6 b=7
    2025-02-07 13:23:20 [info     ] [4312228144 Information in class_sync_add] [AwesomeLogger] a=6 b=7
    2025-02-07 13:23:20 [info     ] [4312228144 class_sync_add called] [AwesomeLogger] a=6 b=7
    2025-02-07 13:23:20 [info     ] [4312228144 Decorator success: class_sync_add] [__main__] _function=class_sync_add _script=all_in_one.py duration=0.00189sec result=13
    2025-02-07 13:23:20 [info     ] [4312228528 Decorator start: class_async_add] [__main__] _function=class_async_add _script=all_in_one.py args=('self:AwesomeClass=<__main__.AwesomeClass object at 0x10310b110>', 'a:int=8', 'b:int=9', "c:dict={'dependency': <__main__.DependencyClass object at 0x10310af90>}") kwargs={}
    2025-02-07 13:23:20 [info     ] [4312228528 class_async_add called] [AwesomeLogger] a=8 b=9
    2025-02-07 13:23:20 [info     ] [4312228528 dependency class name:] [AwesomeLogger] c=DependencyClass
    2025-02-07 13:23:21 [info     ] [4312228528 class_async_add result] [AwesomeLogger] result=17
    2025-02-07 13:23:21 [info     ] [4312228528 Decorator success: class_async_add] [__main__] _function=class_async_add _script=all_in_one.py duration=1.00326sec result=17
    2025-02-07 13:23:21 [info     ] [4312229040 Decorator start: sample_function] [__main__] _function=sample_function _script=all_in_one.py args=('args:int=1', 'kwargs:int=2', 'name:str=Alice', 'age:int=30') kwargs={'name': 'Alice', 'age': 30}
    2025-02-07 13:23:21 [debug    ] [4312229040 Debugging sample_function] [__main__] args=(1, 2, 3) kwargs={'name': 'Alice', 'age': 30}
    2025-02-07 13:23:21 [info     ] [4312229040 Called with args]  [__main__] args=(1, 2, 3)
    2025-02-07 13:23:21 [info     ] [4312229040 Called with kwargs] [__main__] kwargs={'name': 'Alice', 'age': 30}
    2025-02-07 13:23:21 [info     ] [4312229040 Result]            [__main__] result={'sum_args': 6, 'name': 'Alice', 'age': 30}
    2025-02-07 13:23:21 [warning  ] [4312229040 Sum of arguments is greater than 5] [__main__] sum=6
    2025-02-07 13:23:21 [error    ] [4312229040 Division by zero error occurred during calculation. Check the input values] [__main__]
    2025-02-07 13:23:21 [info     ] [4312229040 Decorator success: sample_function] [__main__] _function=sample_function _script=all_in_one.py duration=0.00297sec result={'sum_args': 6, 'name': 'Alice', 'age': 30}
    2025-02-07 13:23:21 [info     ] [4312158640 Decorator start: sample_critical_function] [__main__] _function=sample_critical_function _script=all_in_one.py args=('args:int=10', 'kwargs:int=20') kwargs={}
    2025-02-07 13:23:21 [critical ] [4312158640 Critical issue in sample_critical_function] [__main__] args=(10, 20) kwargs={}
    2025-02-07 13:23:21 [error    ] ('[4312158640 Decorator error in sample_critical_function]',) [__main__] _function=sample_critical_function _script=all_in_one.py error='Simuliertes kritisches Problem'

Running Tests
=============

To run the tests for this package, simply execute:

.. code-block:: bash

    ./pytest

Credits
=======

This package was created using Cookiecutter_ and the
`risclog-solution/risclog-cookiecutter-pypackage`_ project template.

.. _Cookiecutter: https://github.com/audreyr/cookiecutter
.. _`risclog-solution/risclog-cookiecutter-pypackage`: https://github.com/risclog-solution/risclog-cookiecutter-pypackage

Additional Notes
================

- The legacy functions ``get_logger`` and the method ``decorator`` are deprecated and will be removed in version 1.3.0.
- For advanced configuration (custom processors, multiple handlers, etc.), please refer to the documentation.
- The package automatically configures loggers to filter out excessive log messages from libraries like Uvicorn and asyncio.
