"""Logging integration for NI IO Trace."""

import logging

from nitrace import NiTraceError, log_message

__all__ = ["IOTraceHandler"]


class IOTraceHandler(logging.Handler):
    """A logging handler that writes log records into the NI IO Trace log.

    Each log record is formatted and passed to :func:`nitrace.log_message`,
    making Python log entries appear in the IO Trace log alongside NI driver
    calls.
    """

    def emit(self, record: logging.LogRecord) -> None:
        try:
            log_message(self.format(record))
        except NiTraceError:
            self.handleError(record)
