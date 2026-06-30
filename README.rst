===================
risclog.logging
===================

.. image:: https://github.com/risclog-solution/risclog.logging/actions/workflows/test.yml/badge.svg
   :target: https://github.com/risclog-solution/risclog.logging/actions/workflows/test.yml
   :alt: CI Status

.. image:: https://img.shields.io/pypi/v/risclog.logging.svg
   :target: https://pypi.python.org/pypi/risclog.logging

.. image:: https://img.shields.io/pypi/pyversions/risclog.logging.svg
   :target: https://pypi.python.org/pypi/risclog.logging
   :alt: Python Versions

.. image:: https://img.shields.io/badge/license-MIT-blue.svg
   :target: https://github.com/risclog-solution/risclog.logging/blob/main/LICENSE

**risclog.logging** is a comprehensive structured logging solution for Python applications. It combines Python's
built-in ``logging`` module with `structlog <https://www.structlog.org/>`_ to provide powerful, flexible logging
with support for both synchronous and asynchronous code.

**Key Features:**

- **`getLogger`** – Modern factory function for creating logger instances (legacy ``get_logger`` deprecated)
- **`log_decorator`** – Automatic function logging with execution time, arguments, return values, and exception handling
- **Structured logging** – Rich, contextual log entries with automatic JSON serialization
- **Async/Sync support** – Unified API for both synchronous and asynchronous code
- **File & Console output** – Flexible handler configuration
- **Email notifications** – Optional exception alerts via SMTP (with email configuration)
- **Enhanced tracebacks** – Beautiful, colored exception display via Rich

Features
========

- **Structured logging:** Combines standard logging with structlog for rich, contextual logs
- **Synchronous and asynchronous logging:** Unified API works seamlessly in both environments
- **Automatic function logging:** Use ``@log_decorator`` to automatically capture function execution details:

  - Function arguments and their types
  - Return values
  - Execution duration (in milliseconds)
  - Exception stack traces and details

- **Email notifications:** Optionally send SMTP email alerts when decorated functions raise exceptions
- **Rich tracebacks:** Enhanced exception display with colors and source code context
- **Flexible configuration:**

  - Set log levels per logger
  - Add file handlers with custom formatters
  - Configure via environment variables (``LOG_LEVEL``, ``LOG_EXCLUDED_LOGGERS``, etc.)
  - Auto-filters verbose library logs (uvicorn, watchfiles, etc.)

- **Production-ready:** Type hints, comprehensive tests, and battle-tested in production applications

Installation
============

Install via pip:

.. code-block:: bash

    pip install risclog.logging

Configuration and Usage
=======================

Quick Start
-----------

.. code-block:: python

    from risclog.logging import getLogger

    logger = getLogger(__name__)
    logger.set_level("DEBUG")

    # Log messages
    logger.info("Application started")
    logger.warning("Something might be wrong", user_id=42)
    logger.error("An error occurred", error_code=500)

Creating a Logger
-----------------

Use the ``getLogger`` function to obtain a logger instance:

.. code-block:: python

    from risclog.logging import getLogger

    logger = getLogger(__name__)

    # Set log level (accepts string or logging constant)
    logger.set_level("DEBUG")  # or logging.DEBUG

    # Add file handler
    logger.add_file_handler('app.log', level=logging.DEBUG)

Logging Messages
----------------

**Synchronous logging:**

.. code-block:: python

    logger.debug("Debug message")
    logger.info("Info message", user_id=42, action="login")
    logger.warning("Warning message", retry_count=3)
    logger.error("Error message", error_code=500)
    logger.critical("Critical failure", severity="high")

**Asynchronous logging:**

.. code-block:: python

    await logger.debug("Async debug message")
    await logger.info("Async info message", user_id=42)
    # All log methods support both sync and async calls

Automatic Function Logging with Decorators
--------------------------------------------

The ``@log_decorator`` automatically logs function execution with comprehensive details:

**Synchronous functions:**

.. code-block:: python

    from risclog.logging import log_decorator

    @log_decorator
    def calculate_sum(a: int, b: int) -> int:
        """Calculate sum of two numbers."""
        result = a + b
        return result

    result = calculate_sum(10, 20)
    # Logs: [Decorator start: calculate_sum]
    # Logs: [Decorator success: calculate_sum] duration=0.00123sec result=30

**Asynchronous functions:**

.. code-block:: python

    @log_decorator
    async def fetch_data(user_id: int) -> dict:
        """Fetch user data from API."""
        await asyncio.sleep(1)  # Simulate API call
        return {"id": user_id, "name": "Alice"}

    data = await fetch_data(123)
    # Logs: [Decorator start: fetch_data] args=('user_id:int=123',)
    # Logs: [Decorator success: fetch_data] duration=1.00234sec result={'id': 123, 'name': 'Alice'}

**Error handling with decorator:**

.. code-block:: python

    @log_decorator
    def risky_operation(value: int) -> float:
        """Operation that might fail."""
        return 100 / value  # Will raise ZeroDivisionError if value=0

    try:
        risky_operation(0)
    except ZeroDivisionError:
        pass
    # Logs: [Decorator error in risky_operation] error='division by zero'

**Sanitizing decorator values:**

Decorator logs sanitize ``args``, ``kwargs``, ``result`` and exception strings
before they are written. Sensitive field names such as ``password``, ``token``,
``api_key``, ``authorization``, ``cookie``, ``secret``, ``access_key`` and
``secret_key`` are replaced with ``***REDACTED***``. Secret values from matching
environment variables such as ``S3_SECRET_KEY`` or ``MINIO_ACCESS_KEY`` are also
redacted when they appear inside log strings. Long strings, large containers,
binary data, private key blocks and recursive structures are shortened
automatically.

The default limits can be adjusted via environment variables:

.. code-block:: bash

    export LOG_DECORATOR_MAX_STRING_LENGTH=500
    export LOG_DECORATOR_MAX_COLLECTION_ITEMS=20
    export LOG_DECORATOR_MAX_DEPTH=4
    export LOG_DECORATOR_MAX_EXCEPTION_LENGTH=8000
    export LOG_DECORATOR_MIN_SECRET_VALUE_LENGTH=8
    export LOG_DECORATOR_REDACT_KEYS="iban,customer_secret"
    export LOG_DECORATOR_REDACT_ENV_VARS="CUSTOM_S3_SECRET"

Using the Decorator in Classes
------------------------------

Use ``@log_decorator`` on class methods:

.. code-block:: python

    from risclog.logging import getLogger, log_decorator

    class UserService:
        def __init__(self):
            self.logger = getLogger(__name__)

        @log_decorator
        def get_user(self, user_id: int) -> dict:
            """Retrieve user by ID."""
            self.logger.info("Fetching user", user_id=user_id)
            # Simulate database lookup
            return {"id": user_id, "name": "John Doe", "email": "john@example.com"}

        @log_decorator
        async def update_user_async(self, user_id: int, name: str) -> dict:
            """Update user asynchronously."""
            await self.logger.info("Updating user", user_id=user_id, name=name)
            await asyncio.sleep(0.5)  # Simulate API call
            return {"id": user_id, "name": name, "updated": True}

    # Usage
    service = UserService()
    user = service.get_user(42)
    # Logs: [Decorator start: get_user] args=('self:UserService=...', 'user_id:int=42')
    # Logs: Fetching user (manual log)
    # Logs: [Decorator success: get_user] result={'id': 42, 'name': 'John Doe', 'email': 'john@example.com'}

Email Notification on Exceptions
---------------------------------

To send email alerts when a decorated function raises an exception, use ``send_email=True``.

**Required environment variables:**

.. code-block:: bash

    export logging_email_smtp_user="your-email@gmail.com"
    export logging_email_smtp_password="your-app-password"
    export logging_email_smtp_server="smtp.gmail.com"
    export logging_email_to="admin@example.com"

**Usage:**

.. code-block:: python

    @log_decorator(send_email=True)
    def critical_operation():
        """This function will send email on exception."""
        # Your code
        ...

When an exception occurs, the logger will automatically send an email notification
with the full error traceback.

Rich Traceback Integration
---------------------------

The package uses `Rich <https://rich.readthedocs.io/>`_ for beautiful exception display. Rich tracebacks
include syntax highlighting, source code context, and improved readability:

.. code-block:: python

    from rich import traceback
    traceback.install()  # Install the Rich traceback handler

    # Now all exceptions will be displayed with Rich formatting
    1 / 0  # Beautiful traceback with colors and context

Full Example
============

Here's a complete example demonstrating logging with both sync and async functions:

.. code-block:: python

    import asyncio
    import logging
    from risclog.logging import getLogger, log_decorator

    # Configure logger
    logger = getLogger(__name__)
    logger.set_level(logging.DEBUG)
    logger.add_file_handler('app.log', level=logging.DEBUG)

    # Simple sync function
    @log_decorator
    def calculate(a: int, b: int) -> int:
        logger.debug("Performing calculation", a=a, b=b)
        result = a + b
        return result

    # Simple async function
    @log_decorator
    async def fetch_user(user_id: int) -> dict:
        await logger.info("Fetching user from API", user_id=user_id)
        await asyncio.sleep(1)  # Simulate API latency
        return {"id": user_id, "name": "John"}

    # Class-based logging
    class DataProcessor:
        def __init__(self):
            self.logger = getLogger(__name__)

        @log_decorator
        def process(self, data: list) -> int:
            self.logger.info("Processing data", count=len(data))
            total = sum(data)
            self.logger.info("Processing complete", total=total)
            return total

        @log_decorator
        async def process_async(self, data: list) -> int:
            await self.logger.info("Async processing", count=len(data))
            await asyncio.sleep(0.5)
            total = sum(data)
            return total

    # Main execution
    async def main():
        # Sync calls
        logger.info("Application started")
        result = calculate(5, 10)
        logger.info("Calculation result", result=result)

        # Async calls
        user = await fetch_user(123)
        logger.info("User fetched", user=user)

        # Class-based calls
        processor = DataProcessor()
        total = processor.process([1, 2, 3, 4, 5])
        logger.info("Processing complete", total=total)

        total_async = await processor.process_async([10, 20, 30])
        logger.info("Async processing complete", total=total_async)

    if __name__ == "__main__":
        asyncio.run(main())

Example Output
==============

When running the example above, you'll see output similar to this:

.. code-block:: bash

    2026-01-16 12:16:13 [info] Application started
    2026-01-16 12:16:13 [info] [4301639536 Decorator start: calculate] _function=calculate _script=example.py args=('a:int=5', 'b:int=10') kwargs={}
    2026-01-16 12:16:13 [debug] Performing calculation a=5 b=10
    2026-01-16 12:16:13 [info] [4301639536 Decorator success: calculate] _function=calculate result=15 duration=0.00123sec
    2026-01-16 12:16:13 [info] Calculation result result=15
    2026-01-16 12:16:13 [info] [4311754480 Decorator start: fetch_user] _function=fetch_user args=('user_id:int=123',)
    2026-01-16 12:16:13 [info] Fetching user from API user_id=123
    2026-01-16 12:16:14 [info] [4311754480 Decorator success: fetch_user] _function=fetch_user result={'id': 123, 'name': 'John'} duration=1.00234sec
    2026-01-16 12:16:14 [info] User fetched user={'id': 123, 'name': 'John'}
    2026-01-16 12:16:14 [info] [4312228144 Decorator start: process] _function=process args=('self:DataProcessor=...', 'data:list=[1, 2, 3, 4, 5]')
    2026-01-16 12:16:14 [info] Processing data count=5
    2026-01-16 12:16:14 [info] Processing complete total=15
    2026-01-16 12:16:14 [info] [4312228144 Decorator success: process] _function=process result=15 duration=0.00098sec
    2026-01-16 12:16:14 [info] Processing complete total=15

Running Tests
=============

To run the tests for this package, execute:

.. code-block:: bash

    pytest

Or with verbose output:

.. code-block:: bash

    pytest -v

Development
===========

To set up a development environment, clone the repository and install in editable mode:

.. code-block:: bash

    git clone https://github.com/risclog-solution/risclog.logging
    cd risclog.logging
    pip install -e .[dev]
    pytest

Troubleshooting
===============

**Logs not showing in console:**

If you see logs written to files but not in the console, ensure you've added a console handler:

.. code-block:: python

    import logging

    # Add console output
    console_handler = logging.StreamHandler()
    console_handler.setLevel(logging.DEBUG)
    formatter = logging.Formatter('%(asctime)s [%(levelname)s] %(message)s')
    console_handler.setFormatter(formatter)
    logging.getLogger().addHandler(console_handler)

**Email notifications not working:**

Verify all required environment variables are set:

.. code-block:: bash

    echo $logging_email_smtp_user
    echo $logging_email_smtp_password
    echo $logging_email_smtp_server
    echo $logging_email_to

**Performance considerations:**

- The ``@log_decorator`` adds minimal overhead (typically < 1ms)
- File I/O is buffered by Python's logging module
- For high-throughput applications, consider using async logging

Migration from Old API
======================

If you're using the old ``get_logger`` function (deprecated), migrate to the new ``getLogger``:

**Old code:**

.. code-block:: python

    from risclog.logging import get_logger  # Deprecated
    logger = get_logger(__name__)

**New code:**

.. code-block:: python

    from risclog.logging import getLogger  # Current
    logger = getLogger(__name__)

The functionality is the same, but ``getLogger`` is the recommended approach.

Credits
=======

This package was created using `Cookiecutter <https://github.com/audreyr/cookiecutter>`_ and the
`risclog-solution/risclog-cookiecutter-pypackage <https://github.com/risclog-solution/risclog-cookiecutter-pypackage>`_ project template.

License
=======

This project is licensed under the MIT License. See the LICENSE file for details.

Contributing
============

Contributions are welcome! Please see CONTRIBUTING.rst for guidelines.

Support
=======

For issues, questions, or feature requests, please open an issue on
`GitHub <https://github.com/risclog-solution/risclog.logging/issues>`_.

Changelog
=========

See CHANGES.rst for version history and updates.
