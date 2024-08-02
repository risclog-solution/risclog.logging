===============
risclog.logging
===============

.. image:: https://github.com/risclog-solution/risclog.logging/workflows/Test/badge.svg?branch=master
     :target: https://github.com/risclog-solution/risclog.logging/actions?workflow=Test
     :alt: CI Status


.. image:: https://img.shields.io/pypi/v/risclog.logging.svg
        :target: https://pypi.python.org/pypi/risclog.logging

.. image:: https://img.shields.io/travis/risclog-solution/risclog.logging.svg
        :target: https://travis-ci.com/risclog-solution/risclog.logging

.. image:: https://readthedocs.org/projects/risclog.logging/badge/?version=latest
        :target: https://risclog.logging.readthedocs.io/en/latest/?version=latest
        :alt: Documentation Status

The risclog.logging package provides a comprehensive solution for structured logging in Python applications. Risclog.logging uses structlog and logging to generate detailed and formatted log entries. The package supports both synchronous and asynchronous log messages and provides options for automatic e-mail notification of exception errors.


* Free software: MIT license
* Documentation: https://risclog.logging.readthedocs.io.


Installation
------------
	$ pip install structlog


Features
--------


Creating a logger
^^^^^^^^^^^^^^^^^
Um einen Logger zu erstellen, verwenden Sie die get_logger-Funktion. Diese Funktion stellt sicher, dass Sie eine Instanz von RiscLogger erhalten, die ordnungsgemäß konfiguriert ist::

    from risclog.logging import get_logger

	# create logger
	logger = get_logger(name='my_logger')


Configuration of the logger
^^^^^^^^^^^^^^^^^^^^^^^^^^^
The logger configuration takes place automatically when the logger instance is created using get_logger. The _configure_logger method sets up structlog and logging to provide logs with timestamps, context variables and formatting. You can customize the configuration as required.

Log messages
^^^^^^^^^^^^

Use the following methods to log messages with different log levels:

* Debug-message: logger.debug("This is a debug message")
* Info-message: logger.info("This is an info message")
* Warning-message: logger.warning("This is a warning message")
* Error-message: logger.error("This is an error message")
* Critical-message: logger.critical("This is a critical message")
* Fatal-message: logger.fatal("This is a fatal message")
* Exception-message: logger.exception("This is an exception message")


Asynchronous and synchronous log messages
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

The risclog.logging package supports both synchronous and asynchronous log messages. If you are working in an asynchronous environment, use the asynchronous versions of the log methods:

* Asynchronous debug message: await logger.debug("Async debug message")
* Asynchronous info message: await logger.info("Async info message")
* And so on...

Decorator for logging
^^^^^^^^^^^^^^^^^^^^^

The logging_decorator decorator can be used to provide methods with automatic logging and optional e-mail notification of exceptions

.. code-block:: python

	from risclog.logging import get_logger

	logger = get_logger(name='my_logger')

	@logger.logging_decorator(send_email=True)
	async def some_async_function(x, y):
    		return x + y

.. code-block:: python

	from risclog.logging import get_logger

	logger = get_logger(name='my_logger')

	@logger.logging_decorator()
	def some_sync_function(x, y):
    		return x + y


Error handling and e-mail notification
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

If you set the send_email parameter to True, an email notification is automatically sent in the event of an exception. The email is sent asynchronously via a ThreadPoolExecutor and contains the exception details.

**To be able to send e-mails, the following environment variables must be set!**

* 'logging_email_smtp_user'
* 'logging_email_smtp_password'
* 'logging_email_to'
* 'logging_email_smtp_server'


Example
^^^^^^^

Here is a complete example showing how to use the risclog.logginng package in an application


.. code-block:: python

	from risclog.logging import get_logger

	# create Logger
	logger = get_logger(name='my_application')

	# use Logger-Methods
	logger.info("Application started")

	@logger.logging_decorator(send_email=True)
	async def process_data(x, y):
    	if x < 0:
        	raise ValueError("x cannot be negative")
	    return x + y

	# Asynchron Logging
	result = await process_data(5, 10)
	logger.info(f"Processing result: {result}")

Run tests::

    $ ./pytest




Credits
-------

This package was created with Cookiecutter_ and the `risclog-solution/risclog-cookiecutter-pypackage`_ project template.

.. _Cookiecutter: https://github.com/audreyr/cookiecutter
.. _`risclog-solution/risclog-cookiecutter-pypackage`: https://github.com/risclog-solution/risclog-cookiecutter-pypackage


This package uses AppEnv_ for running tests inside this package.

.. _AppEnv: https://github.com/flyingcircusio/appenv
