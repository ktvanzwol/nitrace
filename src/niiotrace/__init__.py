import ctypes
import ctypes.wintypes
import enum
import subprocess
from pathlib import Path


class LogFileSetting(enum.IntEnum):
    """Controls log file format."""

    NO_FILE = -1
    IO_TRACE = 0
    PLAIN_TEXT = 1
    COMMA_SEPARATED = 2
    XML = 3


class FileWriteMode(enum.IntEnum):
    """Controls file creation behavior."""

    CREATE_ONLY = 0
    CREATE_OR_APPEND = 1
    CREATE_OR_OVERWRITE = 2


class CommandStatus(enum.IntEnum):
    """Error codes returned by NI IO Trace API calls."""

    SUCCESS = 0
    FAILED_NO_EXECUTE = -303200
    FAILED_INCOMPATIBLE_STATE = -303201
    FAILED_UNABLE_TO_OPEN_LOG_FILE = -303202
    FAILED_GUI_CLOSED = -303203
    FAILED_INVALID_SETTINGS = -303204
    FAILED_BAD_PARAMETER = -303205
    FAILED_INTERNAL_FAILURE = -303206
    FAILED_INVALID_FILE_EXTENSION = -303207
    FAILED_BUFFER_TOO_SMALL = -303208
    FAILED_FILE_ALREADY_EXISTS = -303209


class NiIOTraceError(Exception):
    """Raised when an NI IO Trace API call returns a non-success status."""

    def __init__(self, status: CommandStatus) -> None:
        self.status = status
        super().__init__(f"NI IO Trace API error: {status.name} ({status.value})")


def _check(status_code: int) -> None:
    status = CommandStatus(status_code)
    if status != CommandStatus.SUCCESS:
        raise NiIOTraceError(status)


def _load_dll() -> ctypes.WinDLL:
    dll = ctypes.WinDLL("NiSpyLog")

    # nispy_GetApplicationPath(char*, size_t) -> int
    dll.nispy_GetApplicationPath.argtypes = [ctypes.c_char_p, ctypes.c_size_t]
    dll.nispy_GetApplicationPath.restype = ctypes.c_int

    # nispy_StartSpying(int, const char*, int) -> int
    dll.nispy_StartSpying.argtypes = [ctypes.c_int, ctypes.c_char_p, ctypes.c_int]
    dll.nispy_StartSpying.restype = ctypes.c_int

    # nispy_StopSpying(void) -> int
    dll.nispy_StopSpying.argtypes = []
    dll.nispy_StopSpying.restype = ctypes.c_int

    # nispy_WriteTextEntry(const char*) -> int
    dll.nispy_WriteTextEntry.argtypes = [ctypes.c_char_p]
    dll.nispy_WriteTextEntry.restype = ctypes.c_int

    # nispy_CloseSpy(void) -> int
    dll.nispy_CloseSpy.argtypes = []
    dll.nispy_CloseSpy.restype = ctypes.c_int

    return dll


_dll: ctypes.WinDLL | None = None


def _get_dll() -> ctypes.WinDLL:
    global _dll
    if _dll is None:
        _dll = _load_dll()
    return _dll


def get_application_path() -> Path:
    """Return the path to the NI IO Trace application executable."""
    buf_size = 1024
    buf = ctypes.create_string_buffer(buf_size)
    _check(_get_dll().nispy_GetApplicationPath(buf, buf_size))
    return Path(buf.value.decode())


def launch_io_trace() -> subprocess.Popen:
    """Launch the NI IO Trace application and return the process handle."""
    app_path = get_application_path()
    return subprocess.Popen([str(app_path)])


def start_tracing(
    log_file_setting: LogFileSetting = LogFileSetting.NO_FILE,
    file_path: str | Path | None = None,
    file_write_mode: FileWriteMode = FileWriteMode.CREATE_ONLY,
) -> None:
    """Start tracing driver calls.

    NI IO Trace must already be launched before calling this function.
    """
    path_bytes = str(file_path).encode() if file_path is not None else None
    _check(_get_dll().nispy_StartSpying(int(log_file_setting), path_bytes, int(file_write_mode)))


def stop_tracing() -> None:
    """Stop tracing driver calls."""
    _check(_get_dll().nispy_StopSpying())


def log_message(message: str) -> None:
    """Write a debug message into the current NI IO Trace log."""
    _check(_get_dll().nispy_WriteTextEntry(message.encode()))


def close_io_trace() -> None:
    """Close the NI IO Trace application.

    Tracing is halted and the application must be relaunched for further use.
    """
    _check(_get_dll().nispy_CloseSpy())
