"""Con DEBUG=true el log raíz va en DEBUG, pero aiosqlite no: registraba cada
sentencia SQL con sus parámetros. En los tests que cargan el corpus, pytest
retenía ese texto (cientos de MB por test) y la suite moría por memoria."""

from __future__ import annotations

import logging

import pytest

from app.core.logging import configure_logging


@pytest.fixture
def restore_logging():
    root = logging.getLogger()
    handlers, level = root.handlers[:], root.level
    aio = logging.getLogger("aiosqlite").level
    yield
    root.handlers[:] = handlers
    root.setLevel(level)
    logging.getLogger("aiosqlite").setLevel(aio)


def test_debug_mode_does_not_log_every_sql_statement(restore_logging):
    configure_logging(logging.DEBUG)
    assert logging.getLogger().level == logging.DEBUG
    assert not logging.getLogger("aiosqlite").isEnabledFor(logging.DEBUG)
    assert logging.getLogger("aiosqlite").isEnabledFor(logging.INFO)


def test_a_stricter_level_still_applies(restore_logging):
    configure_logging(logging.WARNING)
    assert not logging.getLogger("aiosqlite").isEnabledFor(logging.INFO)
