from pathlib import Path

import pytest

import niiotrace
from niiotrace import (
    CommandStatus,
    FileWriteMode,
    LogFileSetting,
    NiIOTraceError,
    _check,
)


@pytest.fixture()
def _ensure_closed():
    """Guarantee IO Trace is shut down after each test."""
    yield
    try:
        niiotrace.stop_tracing()
    except NiIOTraceError:
        pass
    try:
        niiotrace.close_io_trace()
    except NiIOTraceError:
        pass


class TestCheck:
    def test_success_does_not_raise(self):
        _check(0)

    @pytest.mark.parametrize(
        "code, expected_status",
        [
            (-303200, CommandStatus.FAILED_NO_EXECUTE),
            (-303201, CommandStatus.FAILED_INCOMPATIBLE_STATE),
            (-303202, CommandStatus.FAILED_UNABLE_TO_OPEN_LOG_FILE),
            (-303203, CommandStatus.FAILED_GUI_CLOSED),
            (-303204, CommandStatus.FAILED_INVALID_SETTINGS),
            (-303205, CommandStatus.FAILED_BAD_PARAMETER),
            (-303206, CommandStatus.FAILED_INTERNAL_FAILURE),
            (-303207, CommandStatus.FAILED_INVALID_FILE_EXTENSION),
            (-303208, CommandStatus.FAILED_BUFFER_TOO_SMALL),
            (-303209, CommandStatus.FAILED_FILE_ALREADY_EXISTS),
        ],
    )
    def test_error_codes_raise(self, code, expected_status):
        with pytest.raises(NiIOTraceError) as exc_info:
            _check(code)
        assert exc_info.value.status == expected_status
        assert expected_status.name in str(exc_info.value)


class TestGetApplicationPath:
    def test_returns_existing_executable(self):
        result = niiotrace.get_application_path()
        assert isinstance(result, Path)
        assert result.exists()
        assert result.suffix.lower() == ".exe"


class TestTracingLifecycle:
    def test_start_stop_close(self, _ensure_closed):
        niiotrace.launch_io_trace()

        niiotrace.start_tracing()
        niiotrace.stop_tracing()
        niiotrace.close_io_trace()

    def test_log_message_written_to_file(self, _ensure_closed, tmp_path):
        log_file = tmp_path / "trace.txt"

        niiotrace.launch_io_trace()

        niiotrace.start_tracing(
            log_file_setting=LogFileSetting.PLAIN_TEXT,
            file_path=log_file,
            file_write_mode=FileWriteMode.CREATE_OR_OVERWRITE,
        )

        marker = "niiotrace-test-marker"
        niiotrace.log_message(marker)
        niiotrace.stop_tracing()
        niiotrace.close_io_trace()

        contents = log_file.read_text(encoding="utf-8", errors="replace")
        assert marker in contents

    def test_create_only_rejects_existing_file(self, _ensure_closed, tmp_path):
        log_file = tmp_path / "trace.txt"
        log_file.write_text("existing")

        niiotrace.launch_io_trace()

        with pytest.raises(NiIOTraceError) as exc_info:
            niiotrace.start_tracing(
                log_file_setting=LogFileSetting.PLAIN_TEXT,
                file_path=log_file,
                file_write_mode=FileWriteMode.CREATE_ONLY,
            )
        assert exc_info.value.status == CommandStatus.FAILED_FILE_ALREADY_EXISTS


class TestEnums:
    def test_log_file_setting_values(self):
        assert LogFileSetting.NO_FILE == -1
        assert LogFileSetting.IO_TRACE == 0
        assert LogFileSetting.PLAIN_TEXT == 1
        assert LogFileSetting.COMMA_SEPARATED == 2
        assert LogFileSetting.XML == 3

    def test_file_write_mode_values(self):
        assert FileWriteMode.CREATE_ONLY == 0
        assert FileWriteMode.CREATE_OR_APPEND == 1
        assert FileWriteMode.CREATE_OR_OVERWRITE == 2

    def test_command_status_values(self):
        assert CommandStatus.SUCCESS == 0
        assert CommandStatus.FAILED_NO_EXECUTE == -303200
