from unittest.mock import patch

import pytest

from niiotrace import FileWriteMode, LogFileSetting, NiIOTraceError, StatusCode
from niiotrace.__cli__ import main


@pytest.fixture()
def mock_api():
    """Patch all niiotrace API functions used by the CLI."""
    with (
        patch("niiotrace.launch_io_trace") as launch,
        patch("niiotrace.start_tracing") as start,
        patch("niiotrace.stop_tracing") as stop,
        patch("niiotrace.close_io_trace") as close,
    ):
        yield {
            "launch": launch,
            "start": start,
            "stop": stop,
            "close": close,
        }


class TestCLIStart:
    def test_defaults(self, mock_api):
        main(["start"])
        mock_api["launch"].assert_not_called()
        mock_api["start"].assert_called_once_with(
            log_file_setting=LogFileSetting.NO_FILE,
            file_path=None,
            file_write_mode=FileWriteMode.CREATE_ONLY,
        )

    def test_all_options(self, mock_api):
        main(["start", "--launch", "--log-format", "xml", "--file", "trace.xml", "--write-mode", "overwrite"])
        mock_api["launch"].assert_called_once()
        mock_api["start"].assert_called_once_with(
            log_file_setting=LogFileSetting.XML,
            file_path="trace.xml",
            file_write_mode=FileWriteMode.CREATE_OR_OVERWRITE,
        )


class TestCLIStop:
    def test_stop_with_close(self, mock_api):
        main(["stop", "--close"])
        mock_api["stop"].assert_called_once()
        mock_api["close"].assert_called_once()


class TestCLIErrorHandling:
    def test_api_error_exits(self, mock_api, capsys):
        mock_api["stop"].side_effect = NiIOTraceError(StatusCode.FAILED_INCOMPATIBLE_STATE)
        with pytest.raises(SystemExit, match="1"):
            main(["stop"])
        assert "Error" in capsys.readouterr().err
