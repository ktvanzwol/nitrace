from unittest.mock import MagicMock, patch

import pytest

from niiotrace import CommandStatus, FileWriteMode, LogFileSetting, NiIOTraceError
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
    def test_start_defaults(self, mock_api, capsys):
        main(["start"])
        mock_api["launch"].assert_not_called()
        mock_api["start"].assert_called_once_with(
            log_file_setting=LogFileSetting.NO_FILE,
            file_path=None,
            file_write_mode=FileWriteMode.CREATE_ONLY,
        )
        assert "started" in capsys.readouterr().out.lower()

    def test_start_with_launch(self, mock_api, capsys):
        main(["start", "--launch"])
        mock_api["launch"].assert_called_once()
        mock_api["start"].assert_called_once()
        out = capsys.readouterr().out.lower()
        assert "launched" in out
        assert "started" in out

    def test_start_with_all_options(self, mock_api, capsys):
        main(
            [
                "start",
                "--launch",
                "--log-format",
                "xml",
                "--file",
                "C:\\logs\\trace.xml",
                "--write-mode",
                "overwrite",
            ]
        )
        mock_api["launch"].assert_called_once()
        mock_api["start"].assert_called_once_with(
            log_file_setting=LogFileSetting.XML,
            file_path="C:\\logs\\trace.xml",
            file_write_mode=FileWriteMode.CREATE_OR_OVERWRITE,
        )

    @pytest.mark.parametrize(
        "fmt, expected",
        [
            ("none", LogFileSetting.NO_FILE),
            ("io-trace", LogFileSetting.IO_TRACE),
            ("plain-text", LogFileSetting.PLAIN_TEXT),
            ("csv", LogFileSetting.COMMA_SEPARATED),
            ("xml", LogFileSetting.XML),
        ],
    )
    def test_log_format_mapping(self, mock_api, fmt, expected):
        main(["start", "--log-format", fmt])
        assert mock_api["start"].call_args.kwargs["log_file_setting"] == expected

    @pytest.mark.parametrize(
        "mode, expected",
        [
            ("create", FileWriteMode.CREATE_ONLY),
            ("append", FileWriteMode.CREATE_OR_APPEND),
            ("overwrite", FileWriteMode.CREATE_OR_OVERWRITE),
        ],
    )
    def test_write_mode_mapping(self, mock_api, mode, expected):
        main(["start", "--write-mode", mode])
        assert mock_api["start"].call_args.kwargs["file_write_mode"] == expected


class TestCLIStop:
    def test_stop(self, mock_api, capsys):
        main(["stop"])
        mock_api["stop"].assert_called_once()
        mock_api["close"].assert_not_called()
        assert "stopped" in capsys.readouterr().out.lower()

    def test_stop_with_close(self, mock_api, capsys):
        main(["stop", "--close"])
        mock_api["stop"].assert_called_once()
        mock_api["close"].assert_called_once()
        out = capsys.readouterr().out.lower()
        assert "stopped" in out
        assert "closed" in out


class TestCLIErrorHandling:
    def test_api_error_prints_to_stderr_and_exits(self, mock_api, capsys):
        mock_api["stop"].side_effect = NiIOTraceError(CommandStatus.FAILED_INCOMPATIBLE_STATE)
        with pytest.raises(SystemExit, match="1"):
            main(["stop"])
        assert "Error" in capsys.readouterr().err

    def test_missing_command_exits(self):
        with pytest.raises(SystemExit):
            main([])
