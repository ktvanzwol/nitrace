"""Forward Python logging to NI IO Trace.

Demonstrates using nitrace.logging.IOTraceHandler to include Python log
entries in the IO Trace log alongside NI driver calls.
"""

import logging

import nitrace
from nitrace.logging import IOTraceHandler

logger = logging.getLogger("my_app")


def configure_logger():
    # Set logger based log level
    logger.setLevel(logging.DEBUG)

    # Configure IOTraceHandler to forward log messages to NI IO Trace
    handler = IOTraceHandler()
    # Set IOTraceHandler log level to INFO to avoid cluttering the IO Trace log with debug messages
    handler.setLevel(logging.INFO)
    # Note: No need to include timestamps in the log format since IO Trace already timestamps each log entry.
    handler.setFormatter(logging.Formatter("[PYTHON] [%(levelname)s] %(name)s: %(message)s"))
    logger.addHandler(handler)

    # Optionally, add other handlers (e.g. console) if you want logs to also appear elsewhere
    console_handler = logging.StreamHandler()
    console_handler.setFormatter(logging.Formatter("[%(asctime)s] [%(levelname)s] %(name)s: %(message)s"))
    logger.addHandler(console_handler)


def main() -> None:
    # Launch IO Trace and start tracing
    nitrace.launch_io_trace()
    nitrace.start_tracing()

    # Log messages now appear in the IO Trace log
    logger.info("Starting measurement")
    # ... run your NI driver calls ...
    logger.warning("Measurement value out of expected range")
    # ... more NI driver calls ...
    logger.error("Measurement failed")
    # ... even more NI driver calls ...
    logger.debug("This debug message will not appear in IO Trace due to handler log level")

    # Stop logging and leave IO Trace running to inspect the log
    nitrace.stop_tracing()


if __name__ == "__main__":
    configure_logger()
    main()
