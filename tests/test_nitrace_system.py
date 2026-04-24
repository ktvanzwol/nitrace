from pathlib import Path

import pytest

import nitrace
from nitrace import (
    FileWriteMode,
    LogFileSetting,
    NiTraceError,
    StatusCode,
    _check,
)

pytestmark = pytest.mark.system


@pytest.fixture()
def _ensure_closed():
    """Guarantee IO Trace is not running and shut down after each test."""
    try:
        nitrace.close_io_trace()
    except NiTraceError:
        pass
    yield
    try:
        nitrace.stop_tracing()
    except NiTraceError:
        pass
    try:
        nitrace.close_io_trace()
    except NiTraceError:
        pass


class TestGetApplicationPath:
    def test_returns_existing_executable(self):
        result = nitrace.get_application_path()
        assert isinstance(result, Path)
        assert result.exists()
        assert result.suffix.lower() == ".exe"


class TestTracingLifecycle:
    def test_start_stop_close(self, _ensure_closed):
        nitrace.launch_io_trace()

        nitrace.start_tracing()
        nitrace.stop_tracing()
        nitrace.close_io_trace()

    def test_log_message_written_to_file(self, _ensure_closed, tmp_path):
        log_file = tmp_path / "trace.txt"

        nitrace.launch_io_trace()

        nitrace.start_tracing(
            log_file_setting=LogFileSetting.PLAIN_TEXT,
            file_path=log_file,
            file_write_mode=FileWriteMode.CREATE_OR_OVERWRITE,
        )

        marker = "nitrace-test-marker"
        nitrace.log_message(marker)
        nitrace.stop_tracing()
        nitrace.close_io_trace()

        contents = log_file.read_text(encoding="utf-8", errors="replace")
        assert marker in contents

    def test_create_only_rejects_existing_file(self, _ensure_closed, tmp_path):
        log_file = tmp_path / "trace.txt"
        log_file.write_text("existing")

        nitrace.launch_io_trace()

        with pytest.raises(NiTraceError) as exc_info:
            nitrace.start_tracing(
                log_file_setting=LogFileSetting.PLAIN_TEXT,
                file_path=log_file,
                file_write_mode=FileWriteMode.CREATE_ONLY,
            )
        assert exc_info.value.status == StatusCode.FAILED_FILE_ALREADY_EXISTS

    def test_rejects_invalid_file(self, _ensure_closed):
        log_file = "none_existing.txt"

        nitrace.launch_io_trace()

        with pytest.raises(NiTraceError) as exc_info:
            nitrace.start_tracing(
                log_file_setting=LogFileSetting.PLAIN_TEXT,
                file_path=log_file,
                file_write_mode=FileWriteMode.CREATE_ONLY,
            )
        assert exc_info.value.status == StatusCode.FAILED_UNABLE_TO_OPEN_LOG_FILE
