"""Tests for bounded, private and secret-redacting application logging."""

import logging

from src.utils.logger import Logger


def _flush(logger: Logger) -> None:
    for handler in logger.logger.handlers:
        handler.flush()


def test_logger_redacts_secrets_and_does_not_propagate(tmp_path):
    logger = Logger(
        level="debug",
        filename="test.log",
        console=False,
        log_dir=tmp_path,
    )
    try:
        logger.info("password=super-secret token:abc123 connected")
        _flush(logger)
        content = (tmp_path / "test.log").read_text(encoding="utf-8")

        assert "super-secret" not in content
        assert "abc123" not in content
        assert content.count("<redacted>") == 2
        assert logger.logger.propagate is False
        assert logger.logger.name == "streamdeck_control"
    finally:
        logger.shutdown()


def test_logger_reconfiguration_replaces_handlers_without_duplicates(tmp_path):
    logger = Logger(
        level="info",
        filename="test.log",
        console=False,
        log_dir=tmp_path,
    )
    try:
        logger.reconfigure(
            level="warning",
            file_enabled=True,
            console_enabled=True,
            max_files=2,
        )
        first_handlers = list(logger.logger.handlers)
        logger.reconfigure(
            level="error",
            file_enabled=True,
            console_enabled=False,
            max_files=3,
        )

        assert logger.logger.level == logging.ERROR
        assert len(logger.logger.handlers) == 1
        assert all(handler not in logger.logger.handlers for handler in first_handlers)
    finally:
        logger.shutdown()


def test_logger_can_run_with_all_outputs_disabled(tmp_path):
    logger = Logger(
        level="info",
        file_enabled=False,
        console=False,
        log_dir=tmp_path,
    )
    try:
        assert len(logger.logger.handlers) == 1
        assert isinstance(logger.logger.handlers[0], logging.NullHandler)
        logger.info("quiet")
        assert not list(tmp_path.iterdir())
    finally:
        logger.shutdown()
