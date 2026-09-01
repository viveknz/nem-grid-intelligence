"""Unit tests for nem.logging_config."""

import logging

from nem.logging_config import get_logger


def test_get_logger_returns_configured_logger():
    logger = get_logger("test.module")
    assert isinstance(logger, logging.Logger)
    assert logger.level == logging.INFO
    assert len(logger.handlers) == 1


def test_get_logger_is_idempotent():
    """Calling get_logger twice for the same name must not stack handlers.

    Databricks re-runs notebook cells, which re-imports and re-calls
    get_logger — without this guard, handler count grows on every re-run
    and log lines start duplicating.
    """
    first = get_logger("test.idempotent")
    second = get_logger("test.idempotent")
    assert first is second
    assert len(second.handlers) == 1


def test_get_logger_different_names_are_independent():
    a = get_logger("test.module_a")
    b = get_logger("test.module_b")
    assert a is not b
    assert a.name != b.name
