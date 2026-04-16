from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

import niiotrace
from niiotrace import (
    CommandStatus,
    FileWriteMode,
    LogFileSetting,
    NiIOTraceError,
    _check,
)


@pytest.fixture(autouse=True)
def _mock_dll():
    """Replace the DLL singleton with a mock for every test."""
    mock = MagicMock()
    with patch.object(niiotrace, "_dll", mock):
        # Make _get_dll() return the mock directly (already cached via _dll)
        with patch.object(niiotrace, "_get_dll", return_value=mock):
            yield mock


# --- _check / error handling ---


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
    def test_error_codes_raise_niiotrace_error(self, code, expected_status):
        with pytest.raises(NiIOTraceError) as exc_info:
            _check(code)
        assert exc_info.value.status == expected_status

    def test_error_message_contains_name(self):
        with pytest.raises(NiIOTraceError, match="FAILED_BAD_PARAMETER"):
            _check(-303205)


# --- get_application_path ---


class TestGetApplicationPath:
    def test_returns_path(self, _mock_dll):
        def fake_get_app_path(buf, size):
            path = b"C:\\Program Files\\NI IO Trace\\niotrace.exe"
            buf.value = path
            return 0

        _mock_dll.nispy_GetApplicationPath.side_effect = fake_get_app_path

        result = niiotrace.get_application_path()
        assert isinstance(result, Path)
        assert result == Path("C:\\Program Files\\NI IO Trace\\niotrace.exe")

    def test_raises_on_failure(self, _mock_dll):
        _mock_dll.nispy_GetApplicationPath.return_value = -303200
        with pytest.raises(NiIOTraceError):
            niiotrace.get_application_path()


# --- launch_io_trace ---


class TestLaunchIOTrace:
    def test_launches_application(self, _mock_dll):
        def fake_get_app_path(buf, size):
            buf.value = b"C:\\Program Files\\NI IO Trace\\niotrace.exe"
            return 0

        _mock_dll.nispy_GetApplicationPath.side_effect = fake_get_app_path

        with patch("niiotrace.subprocess.Popen") as mock_popen:
            result = niiotrace.launch_io_trace()
            mock_popen.assert_called_once_with(["C:\\Program Files\\NI IO Trace\\niotrace.exe"])
            assert result is mock_popen.return_value

    def test_propagates_api_error(self, _mock_dll):
        _mock_dll.nispy_GetApplicationPath.return_value = -303200
        with pytest.raises(NiIOTraceError):
            niiotrace.launch_io_trace()


# --- start_tracing ---


class TestStartTracing:
    def test_default_args(self, _mock_dll):
        _mock_dll.nispy_StartSpying.return_value = 0

        niiotrace.start_tracing()

        _mock_dll.nispy_StartSpying.assert_called_once_with(
            int(LogFileSetting.NO_FILE), None, int(FileWriteMode.CREATE_ONLY)
        )

    def test_with_all_args(self, _mock_dll):
        _mock_dll.nispy_StartSpying.return_value = 0

        niiotrace.start_tracing(
            log_file_setting=LogFileSetting.PLAIN_TEXT,
            file_path="C:\\logs\\trace.txt",
            file_write_mode=FileWriteMode.CREATE_OR_OVERWRITE,
        )

        _mock_dll.nispy_StartSpying.assert_called_once_with(
            int(LogFileSetting.PLAIN_TEXT),
            b"C:\\logs\\trace.txt",
            int(FileWriteMode.CREATE_OR_OVERWRITE),
        )

    def test_with_path_object(self, _mock_dll):
        _mock_dll.nispy_StartSpying.return_value = 0

        niiotrace.start_tracing(
            log_file_setting=LogFileSetting.XML,
            file_path=Path("C:/logs/trace.xml"),
        )

        args = _mock_dll.nispy_StartSpying.call_args[0]
        assert args[0] == int(LogFileSetting.XML)
        assert isinstance(args[1], bytes)

    def test_raises_on_failure(self, _mock_dll):
        _mock_dll.nispy_StartSpying.return_value = -303204
        with pytest.raises(NiIOTraceError) as exc_info:
            niiotrace.start_tracing()
        assert exc_info.value.status == CommandStatus.FAILED_INVALID_SETTINGS


# --- stop_spying ---


class TestStopTracing:
    def test_success(self, _mock_dll):
        _mock_dll.nispy_StopSpying.return_value = 0
        niiotrace.stop_tracing()
        _mock_dll.nispy_StopSpying.assert_called_once()

    def test_raises_on_failure(self, _mock_dll):
        _mock_dll.nispy_StopSpying.return_value = -303201
        with pytest.raises(NiIOTraceError) as exc_info:
            niiotrace.stop_tracing()
        assert exc_info.value.status == CommandStatus.FAILED_INCOMPATIBLE_STATE


# --- write_text_entry ---


class TestLogMessage:
    def test_encodes_message(self, _mock_dll):
        _mock_dll.nispy_WriteTextEntry.return_value = 0

        niiotrace.log_message("hello world")

        _mock_dll.nispy_WriteTextEntry.assert_called_once_with(b"hello world")

    def test_raises_on_failure(self, _mock_dll):
        _mock_dll.nispy_WriteTextEntry.return_value = -303203
        with pytest.raises(NiIOTraceError) as exc_info:
            niiotrace.log_message("test")
        assert exc_info.value.status == CommandStatus.FAILED_GUI_CLOSED


# --- close_spy ---


class TestCloseIOTrace:
    def test_success(self, _mock_dll):
        _mock_dll.nispy_CloseSpy.return_value = 0
        niiotrace.close_io_trace()
        _mock_dll.nispy_CloseSpy.assert_called_once()

    def test_raises_on_failure(self, _mock_dll):
        _mock_dll.nispy_CloseSpy.return_value = -303206
        with pytest.raises(NiIOTraceError) as exc_info:
            niiotrace.close_io_trace()
        assert exc_info.value.status == CommandStatus.FAILED_INTERNAL_FAILURE


# --- enums ---


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
