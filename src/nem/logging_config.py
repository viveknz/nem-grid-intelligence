"""Shared logging configuration, imported by every notebook and module.

Per docs/04_engineering_standards.md section 5: one configuration, never
print(). Logs to stdout so output shows in the Databricks notebook cell
and in job run logs identically.
"""

import logging
import sys


def get_logger(name: str) -> logging.Logger:
    """Return a configured logger for `name`, idempotent across repeat calls.

    Databricks re-executes notebook cells on re-run, which would otherwise
    stack duplicate handlers on the same logger — the `logger.handlers`
    check guards against that.
    """
    logger = logging.getLogger(name)
    if logger.handlers:
        return logger
    handler = logging.StreamHandler(sys.stdout)
    handler.setFormatter(
        logging.Formatter("%(asctime)s | %(levelname)-8s | %(name)s | %(message)s")
    )
    logger.addHandler(handler)
    logger.setLevel(logging.INFO)
    logger.propagate = False
    return logger
