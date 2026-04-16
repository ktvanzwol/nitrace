import argparse
import sys

import niiotrace


def main(argv: list[str] | None = None) -> None:
    parser = argparse.ArgumentParser(
        prog="niiotrace",
        description="Control NI IO Trace from the command line.",
    )
    subparsers = parser.add_subparsers(dest="command", required=True)

    # start
    start_parser = subparsers.add_parser("start", help="Start tracing driver calls.")
    start_parser.add_argument(
        "--launch",
        action="store_true",
        help="Launch NI IO Trace before starting.",
    )
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
            if args.launch:
                niiotrace.launch_io_trace()
                print("NI IO Trace launched.")
            log_format_map = {
                "none": niiotrace.LogFileSetting.NO_FILE,
                "io-trace": niiotrace.LogFileSetting.IO_TRACE,
                "plain-text": niiotrace.LogFileSetting.PLAIN_TEXT,
                "csv": niiotrace.LogFileSetting.COMMA_SEPARATED,
                "xml": niiotrace.LogFileSetting.XML,
            }
            write_mode_map = {
                "create": niiotrace.FileWriteMode.CREATE_ONLY,
                "append": niiotrace.FileWriteMode.CREATE_OR_APPEND,
                "overwrite": niiotrace.FileWriteMode.CREATE_OR_OVERWRITE,
            }
            niiotrace.start_tracing(
                log_file_setting=log_format_map[args.log_format],
                file_path=args.file,
                file_write_mode=write_mode_map[args.write_mode],
            )
            print("Tracing started.")

        elif args.command == "stop":
            niiotrace.stop_tracing()
            print("Tracing stopped.")
            if args.close:
                niiotrace.close_io_trace()
                print("NI IO Trace closed.")

    except niiotrace.NiIOTraceError as exc:
        print(f"Error: {exc}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()
