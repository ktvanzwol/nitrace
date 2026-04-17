import logging
from unittest.mock import patch

import pytest

from nitrace import NiTraceError, StatusCode
from nitrace.logging import IOTraceHandler


@pytest.fixture()
def handler():
    return IOTraceHandler()


@pytest.fixture()
def logger(handler):
    log = logging.getLogger("test_iotrace_handler")
    log.setLevel(logging.DEBUG)
    log.addHandler(handler)
    yield log
    log.removeHandler(handler)


class TestIOTraceHandler:
    @patch("nitrace.logging.log_message")
    def test_emit_calls_log_message(self, mock_log_message, logger):
        logger.info("hello")
        mock_log_message.assert_called_once()
        assert "hello" in mock_log_message.call_args[0][0]

    @patch("nitrace.logging.log_message")
    def test_emit_formats_record(self, mock_log_message, handler, logger):
        handler.setFormatter(logging.Formatter("[%(levelname)s] %(message)s"))
        logger.warning("test warning")
        mock_log_message.assert_called_once_with("[WARNING] test warning")

    @patch("nitrace.logging.log_message")
    def test_emit_handles_error_on_nitrace_error(self, mock_log_message, logger, handler):
        mock_log_message.side_effect = NiTraceError(StatusCode.FAILED_GUI_CLOSED)
        with patch.object(handler, "handleError") as mock_handle_error:
            logger.error("should fail")
            mock_handle_error.assert_called_once()

    @patch("nitrace.logging.log_message")
    def test_emit_multiple_messages(self, mock_log_message, logger):
        logger.info("first")
        logger.debug("second")
        assert mock_log_message.call_count == 2
