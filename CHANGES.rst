==============================
Change log for risclog.logging
==============================


2.0.1 (unreleased)
==================

- Use ``JSONRenderer`` for logging to journal so that log entries are
  structured and can be parsed by log management systems.


2.0.0 (2026-01-19)
==================

- Add comprehensive type hints to core logging modules for better IDE support and type safety

- Improve mypy configuration to exclude examples, scripts, and docs folders

- Update and expand README.rst with detailed usage examples, troubleshooting guide, and migration instructions

- Add executable example scripts (test_logger.py, api.py) demonstrating logger functionality

- Fix RST formatting issues (backticks) in CHANGES.rst and CONTRIBUTING.rst

- Enhance .pre-commit-config.yaml to properly exclude non-source files from mypy checks



1.3.3 (2025-12-04)
==================

- fix: wrapper async


1.3.2 (2025-10-15)
==================

- remove pretty logging with rich


1.3.1 (2025-09-08)
==================

- Unify default log level and set it from DEBUG to WARNING.


1.3.0 (2025-02-06)
==================

- added ``add_file_handler`` method to add a file handler to a logger

- added ``set_level`` method to set the level of a logger

- Fix log decorator mixed async sync Problem

- old ``decorator`` function is now deprecated

- old ``get_logger`` function is now deprecated


1.2.1 (2024-09-20)
==================

- forward exceptions


1.2.0 (2024-09-19)
==================

- rename email environments


1.1.0 (2024-08-27)
==================

- Allow logging with multiple loggers in a single module.


1.0.2 (2024-08-06)
==================

- Fix CI status badge.


1.0.1 (2024-08-06)
==================

- Fix ``classifiers`` and README structure.


1.0 (2024-08-06)
================

* initial release
