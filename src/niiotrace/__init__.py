import ctypes
import enum
import subprocess
import time
from pathlib import Path


class LogFileSetting(enum.IntEnum):
    """Controls the log file format used when tracing.

    Members:
        NO_FILE: Do not write a log file. Trace data is only visible in the
            NI IO Trace GUI.
        IO_TRACE: Write an NI IO Trace binary log file (``.iotrace``).
        PLAIN_TEXT: Write a human-readable plain-text log file.
        COMMA_SEPARATED: Write a comma-separated values (CSV) log file.
        XML: Write an XML-formatted log file.
    """

    NO_FILE = -1
    IO_TRACE = 0
    PLAIN_TEXT = 1
    COMMA_SEPARATED = 2
    XML = 3


class FileWriteMode(enum.IntEnum):
    """Controls how the log file is created or opened.

    Members:
        CREATE_ONLY: Create a new file. Raises :class:`NiIOTraceError` if the
            file already exists.
        CREATE_OR_APPEND: Open an existing file and append to it, or create a
            new file if it does not exist.
        CREATE_OR_OVERWRITE: Overwrite an existing file, or create a new file
            if it does not exist.
    """

    CREATE_ONLY = 0
    CREATE_OR_APPEND = 1
    CREATE_OR_OVERWRITE = 2


class WindowState(enum.IntEnum):
    """Controls the window state of the NI IO Trace application at launch.

    Members:
        HIDDEN: Launch the application with no visible window.
        NORMAL: Launch the application in its default (restored) window state.
        MAXIMIZED: Launch the application with the window maximized.
        MINIMIZED: Launch the application with the window minimized.
    """

    HIDDEN = 0
    NORMAL = 1
    MAXIMIZED = 2
    MINIMIZED = 3


class CommandStatus(enum.IntEnum):
    """Status codes returned by NI IO Trace API calls.

    ``SUCCESS`` indicates the call completed without error. All other members
    represent error conditions and are used to populate
    :attr:`NiIOTraceError.status`.
    """

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
    """Raised when an NI IO Trace API call returns a non-success status.

    Attributes:
        status: The :class:`CommandStatus` that triggered the error.
    """

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
    """Return the filesystem path to the NI IO Trace executable.

    Returns:
        A :class:`~pathlib.Path` pointing to the executable.

    Raises:
        NiIOTraceError: If NI IO Trace is not installed.
    """
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

    The application must be running before calls to :func:`start_tracing`,
    :func:`stop_tracing`, :func:`log_message`, or :func:`close_io_trace` can
    succeed.

    Args:
        window_state: The initial window state of the application. Defaults to
            :attr:`WindowState.MINIMIZED`.

    Returns:
        The :class:`~subprocess.Popen` instance for the launched process.

    Raises:
        RuntimeError: If the process exits immediately after being started.
        NiIOTraceError: If the application path cannot be resolved.
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
    """Start tracing NI driver calls.

    NI IO Trace must already be running (see :func:`launch_io_trace`) before
    calling this function.

    Args:
        log_file_setting: The format of the log file to write. Use
            :attr:`LogFileSetting.NO_FILE` to trace without writing a file.
        file_path: The path to the log file. Required when *log_file_setting*
            is not :attr:`LogFileSetting.NO_FILE`. Can be a string or
            :class:`~pathlib.Path`.
        file_write_mode: How to handle an existing file at *file_path*.

    Raises:
        NiIOTraceError: If the call fails (e.g. IO Trace is not running,
            the file already exists with :attr:`FileWriteMode.CREATE_ONLY`,
            or the settings are invalid).
    """
    path_bytes = str(file_path).encode() if file_path is not None else None
    _check(_get_dll().nispy_StartSpying(int(log_file_setting), path_bytes, int(file_write_mode)))


def stop_tracing() -> None:
    """Stop tracing NI driver calls.

    Tracing must have been started with :func:`start_tracing` before calling
    this function. The NI IO Trace application remains open and can be
    restarted with another call to :func:`start_tracing`.

    Raises:
        NiIOTraceError: If tracing was not active.
    """
    _check(_get_dll().nispy_StopSpying())


def log_message(message: str) -> None:
    """Write a custom text entry into the active NI IO Trace log.

    This is useful for inserting markers or annotations into a trace session
    to correlate driver calls with application-level events.

    Args:
        message: The text to write. Will be UTF-8 encoded.

    Raises:
        NiIOTraceError: If the IO Trace application has been closed.
    """
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

    Sends the close command and then polls until the NI IO Trace process is
    no longer running. The application does not need to have been launched by
    :func:`launch_io_trace` — it may have been started manually.

    After this call, the application must be relaunched before any further
    tracing can occur.

    Args:
        timeout: Maximum number of seconds to wait for the process to exit.

    Raises:
        NiIOTraceError: If the close command fails.
        RuntimeError: If the process does not exit within *timeout* seconds.
    """
    exe_name = get_application_path().name
    _check(_get_dll().nispy_CloseSpy())
    _wait_for_process_exit(exe_name, timeout)
