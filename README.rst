===============
risclog.logging
===============

.. image:: https://github.com/risclog-solution/risclog.logging/actions/workflows/test.yml/badge.svg
     :target: https://github.com/risclog-solution/risclog.logging/actions/workflows/test.yml
     :alt: CI Status


.. image:: https://img.shields.io/pypi/v/risclog.logging.svg
        :target: https://pypi.python.org/pypi/risclog.logging


The risclog.logging package provides a comprehensive solution for structured logging in Python applications. Risclog.logging uses structlog and logging to generate detailed and formatted log entries. The package supports both synchronous and asynchronous log messages and provides options for automatic e-mail notification of exception errors.


* Free software: MIT license
* Documentation: https://risclog.logging.readthedocs.io.


Features
========


Creating a logger
-----------------

To create a logger, use the get_logger function. This function ensures that you get an instance of RiscLogger that is properly configured.

.. code-block:: python

    from risclog.logging import get_logger

    # create logger
    logger = get_logger(name='my_logger')


Configuration of the logger
---------------------------

The logger configuration takes place automatically when the logger instance is created using get_logger. The _configure_logger method sets up structlog and logging to provide logs with timestamps, context variables and formatting. You can customize the configuration as required.

The module is configured to automatically read the logging level from an environment variable. By default, the level is set to `INFO`. To adjust this, set the `LOG_LEVEL` environment variable:

.. code-block:: bash

    export LOG_LEVEL=DEBUG


Use the following methods to log messages with different log levels:

* Debug-message: logger.debug("This is a debug message")
* Info-message: logger.info("This is an info message")
* Warning-message: logger.warning("This is a warning message")
* Error-message: logger.error("This is an error message")
* Critical-message: logger.critical("This is a critical message")
* Fatal-message: logger.fatal("This is a fatal message")
* Exception-message: logger.exception("This is an exception message")


Asynchronous and synchronous log messages
-----------------------------------------

The risclog.logging package supports both synchronous and asynchronous log messages. If you are working in an asynchronous environment, use the asynchronous versions of the log methods:

* Asynchronous debug message: await logger.debug("Async debug message")
* Asynchronous info message: await logger.info("Async info message")
* And so on...


Decorator for logging
---------------------

The decorator decorator can be used to provide methods with automatic logging and optional e-mail notification of exceptions

.. code-block:: python

    from risclog.logging import get_logger

    logger = get_logger(name='my_logger')

    @logger.decorator(send_email=True)
    async def some_async_function(x, y):
        return x + y

.. code-block:: python

    from risclog.logging import get_logger

    logger = get_logger(name='my_logger')

    @logger.decorator
    def some_sync_function(x, y):
        return x + y


Error handling and e-mail notification
--------------------------------------

If you set the send_email parameter to True, an email notification is automatically sent in the event of an exception. The email is sent asynchronously via a ThreadPoolExecutor and contains the exception details.

**To be able to send e-mails, the following environment variables must be set!**

* 'logging_email_smtp_user'
* 'logging_email_smtp_password'
* 'logging_email_to'
* 'logging_email_smtp_server'


Example
-------

Here is a complete example showing how to use the risclog.logginng package in an application


.. code-block:: python

    import os
    import asyncio
    from risclog.logging import get_logger


    os.environ["LOG_LEVEL"] = "DEBUG"

    logger = get_logger("async_debug_example")


    @logger.decorator(send_email=True)
    async def fetch_data(url: str):
        await logger.debug(f"Start retrieving data from  {url}")
        await asyncio.sleep(2)  # Simulates a delay, such as a network request
        await logger.debug(f"Successfully retrieved data from {url}")
        return {"data": f"Sample data from {url}"}


    @logger.decorator
    async def main():
        url = "https://example.com"
        await logger.debug(f"Start main function with URL: {url}")
        data = await fetch_data(url)
        await logger.debug(f"Data received: {data}")


    if __name__ == "__main__":
        logger.info("Start main function")
        asyncio.run(main())


output:

.. code-block:: bash

    2024-08-05 11:38:51 [info     ] [async_debug_example] __id=4378622064 __sender=inline message=Start main function
    2024-08-05 11:38:51 [info     ] [async_debug_example] __id=4384943584 __sender=async_logging_decorator _function=main _script=example.py message=Method "main" called with no arguments.
    2024-08-05 11:38:51 [debug    ] [async_debug_example] __id=4378552584 __sender=inline _function=main _script=example.py message=Start main function with URL: https://example.com
    2024-08-05 11:38:51 [info     ] [async_debug_example] __id=4384943744 __sender=async_logging_decorator _function=fetch_data _script=example.py message=Method called: "fetch_data" with: "{'arg_0': 'https://example.com'}"
    2024-08-05 11:38:51 [debug    ] [async_debug_example] __id=4366292144 __sender=inline _function=fetch_data _script=example.py message=Start retrieving data from  https://example.com
    2024-08-05 11:38:53 [debug    ] [async_debug_example] __id=4366292144 __sender=inline _function=fetch_data _script=example.py message=Successfully retrieved data from https://example.com
    2024-08-05 11:38:53 [info     ] [async_debug_example] __id=4384943744 __sender=async_logging_decorator _function=fetch_data _script=example.py message=Method "fetch_data" returned: "{'data': 'Sample data from https://example.com'}"
    2024-08-05 11:38:53 [debug    ] [async_debug_example] __id=4378552584 __sender=inline message=Data received: {'data': 'Sample data from https://example.com'}
    2024-08-05 11:38:53 [info     ] [async_debug_example] __id=4384943584 __sender=async_logging_decorator message=Method "main" returned: "None"



Run tests::

    $ ./pytest


Credits
=======

This package was created with Cookiecutter_ and the `risclog-solution/risclog-cookiecutter-pypackage`_ project template.

.. _Cookiecutter: https://github.com/audreyr/cookiecutter
.. _`risclog-solution/risclog-cookiecutter-pypackage`: https://github.com/risclog-solution/risclog-cookiecutter-pypackage


This package uses AppEnv_ for running tests inside this package.

.. _AppEnv: https://github.com/flyingcircusio/appenv
