import argparse
import sys

import nitrace


def main(argv: list[str] | None = None) -> None:
    parser = argparse.ArgumentParser(
        prog="nitrace",
        description="Control NI IO Trace from the command line.",
    )
    subparsers = parser.add_subparsers(dest="command", required=True)

    # start
    start_parser = subparsers.add_parser("start", help="Start tracing driver calls.")
    start_parser.add_argument(
        "--log-format",
        choices=["none", "io-trace", "plain-text", "csv", "xml"],
        default="none",
        help="Log file format (default: none).",
    )
    start_parser.add_argument(
        "--file",
        default=None,
        help="Path to the log file.",
    )
    start_parser.add_argument(
        "--write-mode",
        choices=["create", "append", "overwrite"],
        default="create",
        help="File write mode (default: create).",
    )

    # stop
    stop_parser = subparsers.add_parser("stop", help="Stop tracing driver calls.")
    stop_parser.add_argument(
        "--close",
        action="store_true",
        help="Close NI IO Trace after stopping.",
    )

    args = parser.parse_args(argv)

    try:
        if args.command == "start":
            nitrace.launch_io_trace(window_state=nitrace.WindowState.MINIMIZED)
            log_format_map = {
                "none": nitrace.LogFileSetting.NO_FILE,
                "io-trace": nitrace.LogFileSetting.IO_TRACE,
                "plain-text": nitrace.LogFileSetting.PLAIN_TEXT,
                "csv": nitrace.LogFileSetting.COMMA_SEPARATED,
                "xml": nitrace.LogFileSetting.XML,
            }
            write_mode_map = {
                "create": nitrace.FileWriteMode.CREATE_ONLY,
                "append": nitrace.FileWriteMode.CREATE_OR_APPEND,
                "overwrite": nitrace.FileWriteMode.CREATE_OR_OVERWRITE,
            }
            nitrace.start_tracing(
                log_file_setting=log_format_map[args.log_format],
                file_path=args.file,
                file_write_mode=write_mode_map[args.write_mode],
            )
            print("Tracing started.")

        elif args.command == "stop":
            nitrace.stop_tracing()
            print("Tracing stopped.")
            if args.close:
                nitrace.close_io_trace()
                print("NI IO Trace closed.")

    except nitrace.NiTraceError as exc:
        print(f"Error: {exc}", file=sys.stderr)
        sys.exit(1)
