"""Tests that run in a pure Python environment without NI IO Trace installed.

These validate enums, error handling, the _check helper, and all public API
functions by mocking the NiSpyLog DLL — no real DLL is loaded.
"""

from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

import nitrace
from nitrace import (
    FileWriteMode,
    LogFileSetting,
    NiTraceError,
    StatusCode,
    WindowState,
    _check,
)

# -- Enum definitions --------------------------------------------------------


class TestLogFileSetting:
    def test_members_and_values(self):
        assert LogFileSetting.NO_FILE == -1
        assert LogFileSetting.IO_TRACE == 0
        assert LogFileSetting.PLAIN_TEXT == 1
        assert LogFileSetting.COMMA_SEPARATED == 2
        assert LogFileSetting.XML == 3

    def test_member_count(self):
        assert len(LogFileSetting) == 5

    def test_int_round_trip(self):
        for member in LogFileSetting:
            assert LogFileSetting(int(member)) is member


class TestFileWriteMode:
    def test_members_and_values(self):
        assert FileWriteMode.CREATE_ONLY == 0
        assert FileWriteMode.CREATE_OR_APPEND == 1
        assert FileWriteMode.CREATE_OR_OVERWRITE == 2

    def test_member_count(self):
        assert len(FileWriteMode) == 3

    def test_int_round_trip(self):
        for member in FileWriteMode:
            assert FileWriteMode(int(member)) is member


class TestWindowState:
    def test_members_and_values(self):
        assert WindowState.HIDDEN == 0
        assert WindowState.NORMAL == 1
        assert WindowState.MAXIMIZED == 2
        assert WindowState.MINIMIZED == 3

    def test_member_count(self):
        assert len(WindowState) == 4

    def test_int_round_trip(self):
        for member in WindowState:
            assert WindowState(int(member)) is member


class TestStatusCode:
    ALL_ERRORS = [
        (StatusCode.FAILED_NO_EXECUTE, -303200),
        (StatusCode.FAILED_INCOMPATIBLE_STATE, -303201),
        (StatusCode.FAILED_UNABLE_TO_OPEN_LOG_FILE, -303202),
        (StatusCode.FAILED_GUI_CLOSED, -303203),
        (StatusCode.FAILED_INVALID_SETTINGS, -303204),
        (StatusCode.FAILED_BAD_PARAMETER, -303205),
        (StatusCode.FAILED_INTERNAL_FAILURE, -303206),
        (StatusCode.FAILED_INVALID_FILE_EXTENSION, -303207),
        (StatusCode.FAILED_BUFFER_TOO_SMALL, -303208),
        (StatusCode.FAILED_FILE_ALREADY_EXISTS, -303209),
    ]

    def test_success_value(self):
        assert StatusCode.SUCCESS == 0

    @pytest.mark.parametrize("member, value", ALL_ERRORS)
    def test_error_values(self, member, value):
        assert member == value

    def test_member_count(self):
        assert len(StatusCode) == 11

    def test_invalid_code_raises_value_error(self):
        with pytest.raises(ValueError):
            StatusCode(999)


# -- NiTraceError ------------------------------------------------------------


class TestNiTraceError:
    def test_is_exception(self):
        assert issubclass(NiTraceError, Exception)

    def test_stores_status(self):
        err = NiTraceError(StatusCode.FAILED_GUI_CLOSED)
        assert err.status is StatusCode.FAILED_GUI_CLOSED

    def test_message_contains_name_and_value(self):
        err = NiTraceError(StatusCode.FAILED_BAD_PARAMETER)
        msg = str(err)
        assert "FAILED_BAD_PARAMETER" in msg
        assert "-303205" in msg

    @pytest.mark.parametrize("status", list(StatusCode))
    def test_all_status_codes_produce_valid_error(self, status):
        if status is StatusCode.SUCCESS:
            pytest.skip("SUCCESS is not an error")
        err = NiTraceError(status)
        assert err.status is status
        assert status.name in str(err)


# -- _check helper -----------------------------------------------------------


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

    def test_unknown_code_raises_value_error(self):
        with pytest.raises(ValueError):
            _check(42)


# -- Mock DLL fixture --------------------------------------------------------


@pytest.fixture()
def mock_dll():
    """Provide a MagicMock that stands in for NiSpyLog.dll and reset the global afterwards."""
    dll = MagicMock()
    dll.nispy_GetApplicationPath.return_value = 0
    dll.nispy_StartSpying.return_value = 0
    dll.nispy_StopSpying.return_value = 0
    dll.nispy_WriteTextEntry.return_value = 0
    dll.nispy_CloseSpy.return_value = 0

    with patch("nitrace._get_dll", return_value=dll):
        yield dll


# -- get_application_path ----------------------------------------------------


class TestGetApplicationPath:
    def test_returns_path(self, mock_dll):
        def fake_get_path(buf, size):
            path = b"C:\\Program Files\\NI IO Trace\\NIIOTrace.exe"
            buf.value = path
            return 0

        mock_dll.nispy_GetApplicationPath.side_effect = fake_get_path

        result = nitrace.get_application_path()
        assert isinstance(result, Path)
        assert result == Path("C:\\Program Files\\NI IO Trace\\NIIOTrace.exe")

    def test_raises_on_error(self, mock_dll):
        mock_dll.nispy_GetApplicationPath.return_value = StatusCode.FAILED_NO_EXECUTE
        with pytest.raises(NiTraceError) as exc_info:
            nitrace.get_application_path()
        assert exc_info.value.status == StatusCode.FAILED_NO_EXECUTE


# -- start_tracing -----------------------------------------------------------


class TestStartTracing:
    def test_defaults(self, mock_dll):
        nitrace.start_tracing()
        mock_dll.nispy_StartSpying.assert_called_once_with(-1, None, 0)

    def test_with_file(self, mock_dll):
        nitrace.start_tracing(
            log_file_setting=LogFileSetting.PLAIN_TEXT,
            file_path="trace.txt",
            file_write_mode=FileWriteMode.CREATE_OR_OVERWRITE,
        )
        mock_dll.nispy_StartSpying.assert_called_once_with(1, b"trace.txt", 2)

    def test_with_path_object(self, mock_dll):
        nitrace.start_tracing(
            log_file_setting=LogFileSetting.XML,
            file_path=Path("output/trace.xml"),
            file_write_mode=FileWriteMode.CREATE_ONLY,
        )
        args = mock_dll.nispy_StartSpying.call_args[0]
        assert args[0] == LogFileSetting.XML
        assert args[1] == str(Path("output/trace.xml")).encode()
        assert args[2] == FileWriteMode.CREATE_ONLY

    def test_raises_on_error(self, mock_dll):
        mock_dll.nispy_StartSpying.return_value = StatusCode.FAILED_INCOMPATIBLE_STATE
        with pytest.raises(NiTraceError) as exc_info:
            nitrace.start_tracing()
        assert exc_info.value.status == StatusCode.FAILED_INCOMPATIBLE_STATE


# -- stop_tracing ------------------------------------------------------------


class TestStopTracing:
    def test_success(self, mock_dll):
        nitrace.stop_tracing()
        mock_dll.nispy_StopSpying.assert_called_once()

    def test_raises_on_error(self, mock_dll):
        mock_dll.nispy_StopSpying.return_value = StatusCode.FAILED_INCOMPATIBLE_STATE
        with pytest.raises(NiTraceError) as exc_info:
            nitrace.stop_tracing()
        assert exc_info.value.status == StatusCode.FAILED_INCOMPATIBLE_STATE


# -- log_message -------------------------------------------------------------


class TestLogMessage:
    def test_encodes_and_sends(self, mock_dll):
        nitrace.log_message("hello world")
        mock_dll.nispy_WriteTextEntry.assert_called_once_with(b"hello world")

    def test_utf8_encoding(self, mock_dll):
        nitrace.log_message("café ☕")
        mock_dll.nispy_WriteTextEntry.assert_called_once_with("café ☕".encode())

    def test_raises_on_error(self, mock_dll):
        mock_dll.nispy_WriteTextEntry.return_value = StatusCode.FAILED_GUI_CLOSED
        with pytest.raises(NiTraceError) as exc_info:
            nitrace.log_message("msg")
        assert exc_info.value.status == StatusCode.FAILED_GUI_CLOSED


# -- close_io_trace ----------------------------------------------------------


class TestCloseIoTrace:
    def test_success(self, mock_dll):
        def fake_get_path(buf, size):
            buf.value = b"C:\\NIIOTrace.exe"
            return 0

        mock_dll.nispy_GetApplicationPath.side_effect = fake_get_path

        with patch("nitrace._wait_for_process_exit") as mock_wait:
            nitrace.close_io_trace()
            mock_dll.nispy_CloseSpy.assert_called_once()
            mock_wait.assert_called_once_with("NIIOTrace.exe", 10.0)

    def test_custom_timeout(self, mock_dll):
        def fake_get_path(buf, size):
            buf.value = b"C:\\NIIOTrace.exe"
            return 0

        mock_dll.nispy_GetApplicationPath.side_effect = fake_get_path

        with patch("nitrace._wait_for_process_exit") as mock_wait:
            nitrace.close_io_trace(timeout=5.0)
            mock_wait.assert_called_once_with("NIIOTrace.exe", 5.0)

    def test_raises_on_error(self, mock_dll):
        def fake_get_path(buf, size):
            buf.value = b"C:\\NIIOTrace.exe"
            return 0

        mock_dll.nispy_GetApplicationPath.side_effect = fake_get_path
        mock_dll.nispy_CloseSpy.return_value = StatusCode.FAILED_INCOMPATIBLE_STATE

        with pytest.raises(NiTraceError) as exc_info:
            nitrace.close_io_trace()
        assert exc_info.value.status == StatusCode.FAILED_INCOMPATIBLE_STATE


# -- launch_io_trace ---------------------------------------------------------


class TestLaunchIoTrace:
    def test_launches_process_and_verifies(self, mock_dll):
        def fake_get_path(buf, size):
            buf.value = b"C:\\NIIOTrace.exe"
            return 0

        mock_dll.nispy_GetApplicationPath.side_effect = fake_get_path
        mock_process = MagicMock()
        mock_process.poll.return_value = None

        with patch("nitrace.subprocess.Popen", return_value=mock_process) as mock_popen:
            result = nitrace.launch_io_trace()

        assert result is mock_process
        mock_popen.assert_called_once_with(["C:\\NIIOTrace.exe", "/minimized"])
        mock_dll.nispy_StartSpying.assert_called()
        mock_dll.nispy_StopSpying.assert_called()

    @pytest.mark.parametrize(
        "state, expected_args",
        [
            (WindowState.HIDDEN, ["/hidden"]),
            (WindowState.NORMAL, []),
            (WindowState.MAXIMIZED, ["/maximized"]),
            (WindowState.MINIMIZED, ["/minimized"]),
        ],
    )
    def test_window_state_args(self, mock_dll, state, expected_args):
        def fake_get_path(buf, size):
            buf.value = b"C:\\NIIOTrace.exe"
            return 0

        mock_dll.nispy_GetApplicationPath.side_effect = fake_get_path
        mock_process = MagicMock()
        mock_process.poll.return_value = None

        with patch("nitrace.subprocess.Popen", return_value=mock_process) as mock_popen:
            nitrace.launch_io_trace(window_state=state)

        mock_popen.assert_called_once_with(["C:\\NIIOTrace.exe", *expected_args])

    def test_raises_if_process_exits_immediately(self, mock_dll):
        def fake_get_path(buf, size):
            buf.value = b"C:\\NIIOTrace.exe"
            return 0

        mock_dll.nispy_GetApplicationPath.side_effect = fake_get_path
        mock_process = MagicMock()
        mock_process.poll.return_value = 1
        mock_process.returncode = 1

        with patch("nitrace.subprocess.Popen", return_value=mock_process):
            with pytest.raises(RuntimeError, match="exited immediately"):
                nitrace.launch_io_trace()

    def test_raises_if_app_never_responds(self, mock_dll):
        def fake_get_path(buf, size):
            buf.value = b"C:\\NIIOTrace.exe"
            return 0

        mock_dll.nispy_GetApplicationPath.side_effect = fake_get_path
        mock_dll.nispy_StartSpying.return_value = StatusCode.FAILED_INCOMPATIBLE_STATE
        mock_process = MagicMock()
        mock_process.poll.return_value = None

        with (
            patch("nitrace.subprocess.Popen", return_value=mock_process),
            patch("nitrace.time.sleep"),
        ):
            with pytest.raises(RuntimeError, match="failed to respond"):
                nitrace.launch_io_trace()


# -- _find_process_ids -------------------------------------------------------


class TestFindProcessIds:
    def test_parses_tasklist_output(self):
        fake_output = (
            '"NIIOTrace.exe","1234","Console","1","12,340 K"\n"NIIOTrace.exe","5678","Console","1","8,192 K"\n'
        )
        with patch("nitrace.subprocess.run") as mock_run:
            mock_run.return_value = MagicMock(stdout=fake_output)
            pids = nitrace._find_process_ids("NIIOTrace.exe")
        assert pids == [1234, 5678]

    def test_no_matching_processes(self):
        fake_output = "INFO: No tasks are running which match the specified criteria.\n"
        with patch("nitrace.subprocess.run") as mock_run:
            mock_run.return_value = MagicMock(stdout=fake_output)
            pids = nitrace._find_process_ids("NIIOTrace.exe")
        assert pids == []

    def test_case_insensitive_match(self):
        fake_output = '"niiotrace.exe","1234","Console","1","12,340 K"\n'
        with patch("nitrace.subprocess.run") as mock_run:
            mock_run.return_value = MagicMock(stdout=fake_output)
            pids = nitrace._find_process_ids("NIIOTrace.exe")
        assert pids == [1234]


# -- _wait_for_process_exit --------------------------------------------------


class TestWaitForProcessExit:
    def test_returns_when_process_exits(self):
        with patch("nitrace._find_process_ids", side_effect=[[1234], []]), patch("nitrace.time.sleep"):
            nitrace._wait_for_process_exit("NIIOTrace.exe", timeout=5.0)

    def test_raises_on_timeout(self):
        with (
            patch("nitrace._find_process_ids", return_value=[1234]),
            patch("nitrace.time.monotonic", side_effect=[0.0, 0.0, 6.0]),
            patch("nitrace.time.sleep"),
        ):
            with pytest.raises(RuntimeError, match="did not exit"):
                nitrace._wait_for_process_exit("NIIOTrace.exe", timeout=5.0)
