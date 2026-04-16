"""System tests that call the real NiSpyLog.dll.

These tests require NI IO Trace to be installed on the machine.
Run with:  pytest -m system
Skip with: pytest -m "not system"  (default)
"""

import time
from pathlib import Path

import pytest

import niiotrace
from niiotrace import FileWriteMode, LogFileSetting

pytestmark = pytest.mark.system


@pytest.fixture()
def _ensure_closed():
    """Guarantee IO Trace is shut down after each test."""
    yield
    try:
        niiotrace.stop_tracing()
    except niiotrace.NiIOTraceError:
        pass
    try:
        niiotrace.close_io_trace()
    except niiotrace.NiIOTraceError:
        pass


@pytest.fixture()
def log_file(tmp_path):
    """Provide a temporary log file path and clean it up afterwards."""
    return tmp_path / "trace.txt"


class TestGetApplicationPath:
    def test_returns_existing_executable(self):
        result = niiotrace.get_application_path()
        assert isinstance(result, Path)
        assert result.exists(), f"Expected executable at {result}"
        assert result.suffix.lower() == ".exe"


class TestTracingLifecycle:
    """Full start → log → stop → close cycle using the real DLL."""

    def test_start_and_stop_without_log_file(self, _ensure_closed):
        niiotrace.launch_io_trace()
        time.sleep(1)

        niiotrace.start_tracing()
        niiotrace.stop_tracing()
        niiotrace.close_io_trace()

    def test_log_message_appears_in_plain_text_file(self, _ensure_closed, log_file):
        niiotrace.launch_io_trace()
        time.sleep(1)

        niiotrace.start_tracing(
            log_file_setting=LogFileSetting.PLAIN_TEXT,
            file_path=log_file,
            file_write_mode=FileWriteMode.CREATE_OR_OVERWRITE,
        )

        marker = "niiotrace-system-test-marker"
        niiotrace.log_message(marker)
        niiotrace.stop_tracing()
        niiotrace.close_io_trace()

        assert log_file.exists(), f"Log file was not created at {log_file}"
        contents = log_file.read_text(encoding="utf-8", errors="replace")
        assert marker in contents, f"Marker not found in log:\n{contents[:500]}"

    def test_log_message_appears_in_csv_file(self, _ensure_closed, tmp_path):
        csv_file = tmp_path / "trace.csv"

        niiotrace.launch_io_trace()
        time.sleep(1)

        niiotrace.start_tracing(
            log_file_setting=LogFileSetting.COMMA_SEPARATED,
            file_path=csv_file,
            file_write_mode=FileWriteMode.CREATE_OR_OVERWRITE,
        )

        marker = "niiotrace-csv-test-marker"
        niiotrace.log_message(marker)
        niiotrace.stop_tracing()
        niiotrace.close_io_trace()

        assert csv_file.exists(), f"CSV file was not created at {csv_file}"
        contents = csv_file.read_text(encoding="utf-8", errors="replace")
        assert marker in contents, f"Marker not found in CSV:\n{contents[:500]}"

    def test_create_only_fails_when_file_exists(self, _ensure_closed, log_file):
        log_file.write_text("pre-existing content")

        niiotrace.launch_io_trace()
        time.sleep(1)

        with pytest.raises(niiotrace.NiIOTraceError) as exc_info:
            niiotrace.start_tracing(
                log_file_setting=LogFileSetting.PLAIN_TEXT,
                file_path=log_file,
                file_write_mode=FileWriteMode.CREATE_ONLY,
            )
        assert exc_info.value.status == niiotrace.CommandStatus.FAILED_FILE_ALREADY_EXISTS


class TestErrorConditions:
    def test_stop_without_start_raises(self, _ensure_closed):
        niiotrace.launch_io_trace()
        time.sleep(1)

        with pytest.raises(niiotrace.NiIOTraceError):
            niiotrace.stop_tracing()

    def test_start_without_launch_raises(self):
        with pytest.raises(niiotrace.NiIOTraceError):
            niiotrace.start_tracing()
