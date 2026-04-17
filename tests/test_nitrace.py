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


class TestCheck:
    def test_success_does_not_raise(self):
        _check(0)

    @pytest.mark.parametrize(
        "code, expected_status",
        [
            (-303200, StatusCode.FAILED_NO_EXECUTE),
            (-303201, StatusCode.FAILED_INCOMPATIBLE_STATE),
            (-303202, StatusCode.FAILED_UNABLE_TO_OPEN_LOG_FILE),
            (-303203, StatusCode.FAILED_GUI_CLOSED),
            (-303204, StatusCode.FAILED_INVALID_SETTINGS),
            (-303205, StatusCode.FAILED_BAD_PARAMETER),
            (-303206, StatusCode.FAILED_INTERNAL_FAILURE),
            (-303207, StatusCode.FAILED_INVALID_FILE_EXTENSION),
            (-303208, StatusCode.FAILED_BUFFER_TOO_SMALL),
            (-303209, StatusCode.FAILED_FILE_ALREADY_EXISTS),
        ],
    )
    def test_error_codes_raise(self, code, expected_status):
        with pytest.raises(NiTraceError) as exc_info:
            _check(code)
        assert exc_info.value.status == expected_status
        assert expected_status.name in str(exc_info.value)


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
