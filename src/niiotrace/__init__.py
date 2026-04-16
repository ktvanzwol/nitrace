import ctypes
import ctypes.wintypes
import enum
import subprocess
import time
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


class WindowState(enum.IntEnum):
    """Controls the window state when launching the application."""

    HIDDEN = 0
    NORMAL = 1
    MAXIMIZED = 3
    MINIMIZED = 6


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


_WINDOW_STATE_ARGS: dict[WindowState, list[str]] = {
    WindowState.HIDDEN: ["/hidden"],
    WindowState.NORMAL: [],
    WindowState.MAXIMIZED: ["/maximized"],
    WindowState.MINIMIZED: ["/minimized"],
}


def launch_io_trace(
    window_state: WindowState = WindowState.MINIMIZED,
) -> subprocess.Popen:
    """Launch the NI IO Trace application and return the process handle.

    Raises ``RuntimeError`` if the process exits immediately.
    """
    app_path = get_application_path()
    cmd = [str(app_path), *_WINDOW_STATE_ARGS[window_state]]
    process = subprocess.Popen(cmd)

    if process.poll() is not None:
        raise RuntimeError(f"NI IO Trace exited immediately with code {process.returncode}")
    return process


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


def _find_process_ids(exe_name: str) -> list[int]:
    """Return PIDs of all running processes matching *exe_name*."""
    result = subprocess.run(
        ["tasklist", "/FI", f"IMAGENAME eq {exe_name}", "/FO", "CSV", "/NH"],
        capture_output=True,
        text=True,
    )
    pids: list[int] = []
    for line in result.stdout.splitlines():
        parts = line.strip().strip('"').split('","')
        if len(parts) >= 2 and parts[0].lower() == exe_name.lower():
            pids.append(int(parts[1]))
    return pids


def _wait_for_process_exit(exe_name: str, timeout: float) -> None:
    """Block until no processes named *exe_name* are running, or *timeout* expires."""
    deadline = time.monotonic() + timeout
    while time.monotonic() < deadline:
        if not _find_process_ids(exe_name):
            return
        time.sleep(0.25)
    raise RuntimeError(f"{exe_name} did not exit within {timeout} seconds")


def close_io_trace(timeout: float = 10.0) -> None:
    """Close the NI IO Trace application and wait for the process to exit.

    Tracing is halted and the application must be relaunched for further use.
    Raises ``RuntimeError`` if the process does not exit within *timeout* seconds.
    """
    exe_name = get_application_path().name
    _check(_get_dll().nispy_CloseSpy())
    _wait_for_process_exit(exe_name, timeout)
