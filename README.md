# niiotrace

A Python library for controlling [NI IO Trace](https://www.ni.com/docs/en-US/bundle/ni-io-trace/page/overview.html) programmatically. Launch the application, start and stop tracing, write log messages, and close IO Trace — all from Python.

## Requirements

- Windows
- Python 3.13+
- NI IO Trace installed (part of NI software distributions)
  - [Where Can I Download NI I/O Trace?](https://knowledge.ni.com/KnowledgeArticleDetails?id=kA00Z000000kJcQSAU)

## Installation

Install directly from GitHub:

```
pip install git+https://github.com/kvanzwol/niiotrace.git
```

Or with [uv](https://docs.astral.sh/uv/):

```
uv add git+https://github.com/kvanzwol/niiotrace.git
```

## Quick Start

```python
import niiotrace

# Launch the application (minimized by default)
niiotrace.launch_io_trace()

# Start tracing to a plain-text log file
niiotrace.start_tracing(
    log_file_setting=niiotrace.LogFileSetting.PLAIN_TEXT,
    file_path="trace.txt",
    file_write_mode=niiotrace.FileWriteMode.CREATE_OR_OVERWRITE,
)

# Insert a marker into the trace log
niiotrace.log_message("Test started")

# ... run your NI driver calls ...

# Stop tracing and close the application
niiotrace.stop_tracing()
niiotrace.close_io_trace()
```

## CLI

A command-line interface is included:

```
# Launch IO Trace and start tracing to a CSV file
niiotrace start --launch --log-format csv --file trace.csv --write-mode overwrite

# Stop tracing and close the application
niiotrace stop --close
```

### `niiotrace start`

| Option | Description |
|---|---|
| `--launch` | Launch NI IO Trace before starting. |
| `--log-format` | Log file format: `none`, `io-trace`, `plain-text`, `csv`, `xml` (default: `none`). |
| `--file` | Path to the log file. |
| `--write-mode` | File write mode: `create`, `append`, `overwrite` (default: `create`). |

### `niiotrace stop`

| Option | Description |
|---|---|
| `--close` | Close NI IO Trace after stopping. |

## API Reference

- **Functions:** [`get_application_path`](#get_application_path---path) · [`launch_io_trace`](#launch_io_tracewindow_statewindowstateminimized---subprocesspopen) · [`start_tracing`](#start_tracinglog_file_settinglogfilesettingno_file-file_pathnone-file_write_modefilewritemodecreate_only---none) · [`stop_tracing`](#stop_tracing---none) · [`log_message`](#log_messagemessage-str---none) · [`close_io_trace`](#close_io_tracetimeout-float--100---none)
- **Enums:** [`LogFileSetting`](#logfilesetting) · [`FileWriteMode`](#filewritemode) · [`WindowState`](#windowstate) · [`StatusCode`](#statuscode)
- **Exceptions:** [`NiIOTraceError`](#niiotraceerror)

### Functions

#### `get_application_path() -> Path`

Return the filesystem path to the NI IO Trace executable.

**Raises:** `NiIOTraceError` if NI IO Trace is not installed.

---

#### `launch_io_trace(window_state=WindowState.MINIMIZED) -> subprocess.Popen`

Launch the NI IO Trace application and return the process handle. The application must be running before calling `start_tracing`, `stop_tracing`, `log_message`, or `close_io_trace`.

| Parameter | Type | Default | Description |
|---|---|---|---|
| `window_state` | `WindowState` | `MINIMIZED` | Initial window state of the application. |

**Raises:** `RuntimeError` if the process exits immediately. `NiIOTraceError` if the application path cannot be resolved.

---

#### `start_tracing(log_file_setting=LogFileSetting.NO_FILE, file_path=None, file_write_mode=FileWriteMode.CREATE_ONLY) -> None`

Start tracing NI driver calls. NI IO Trace must already be running.

| Parameter | Type | Default | Description |
|---|---|---|---|
| `log_file_setting` | `LogFileSetting` | `NO_FILE` | Format of the log file. |
| `file_path` | `str \| Path \| None` | `None` | Path to the log file. Required when `log_file_setting` is not `NO_FILE`. |
| `file_write_mode` | `FileWriteMode` | `CREATE_ONLY` | How to handle an existing file. |

**Raises:** `NiIOTraceError` if IO Trace is not running, the file already exists with `CREATE_ONLY`, or the settings are invalid.

---

#### `stop_tracing() -> None`

Stop tracing NI driver calls. The application remains open and tracing can be restarted.

**Raises:** `NiIOTraceError` if tracing was not active.

---

#### `log_message(message: str) -> None`

Write a custom text entry into the active trace log. Useful for inserting markers to correlate driver calls with application events.

| Parameter | Type | Description |
|---|---|---|
| `message` | `str` | The text to write. |

**Raises:** `NiIOTraceError` if the IO Trace application has been closed.

---

#### `close_io_trace(timeout: float = 10.0) -> None`

Close the NI IO Trace application and wait for the process to exit. The application does not need to have been launched by `launch_io_trace` — it may have been started manually.

| Parameter | Type | Default | Description |
|---|---|---|---|
| `timeout` | `float` | `10.0` | Maximum seconds to wait for the process to exit. |

**Raises:** `NiIOTraceError` if the close command fails. `RuntimeError` if the process does not exit within the timeout.

### Enums

#### `LogFileSetting`

| Member | Value | Description |
|---|---|---|
| `NO_FILE` | -1 | No log file; trace data visible only in the GUI. |
| `IO_TRACE` | 0 | NI IO Trace binary format (`.iotrace`). |
| `PLAIN_TEXT` | 1 | Human-readable plain-text file. |
| `COMMA_SEPARATED` | 2 | Comma-separated values (CSV) file. |
| `XML` | 3 | XML-formatted file. |

#### `FileWriteMode`

| Member | Value | Description |
|---|---|---|
| `CREATE_ONLY` | 0 | Create a new file. Raises `NiIOTraceError` if the file exists. |
| `CREATE_OR_APPEND` | 1 | Append to an existing file or create a new one. |
| `CREATE_OR_OVERWRITE` | 2 | Overwrite an existing file or create a new one. |

#### `WindowState`

| Member | Value | Description |
|---|---|---|
| `HIDDEN` | 0 | No visible window. |
| `NORMAL` | 1 | Default (restored) window state. |
| `MAXIMIZED` | 2 | Window maximized. |
| `MINIMIZED` | 3 | Window minimized. |

#### `StatusCode`

| Member | Value | Description |
|---|---|---|
| `SUCCESS` | 0 | Call completed successfully. |
| `FAILED_NO_EXECUTE` | -303200 | Command could not be executed. |
| `FAILED_INCOMPATIBLE_STATE` | -303201 | Operation not valid in the current state. |
| `FAILED_UNABLE_TO_OPEN_LOG_FILE` | -303202 | Could not open the specified log file. |
| `FAILED_GUI_CLOSED` | -303203 | The IO Trace application is not running. |
| `FAILED_INVALID_SETTINGS` | -303204 | Invalid tracing settings. |
| `FAILED_BAD_PARAMETER` | -303205 | A parameter value is invalid. |
| `FAILED_INTERNAL_FAILURE` | -303206 | An internal error occurred. |
| `FAILED_INVALID_FILE_EXTENSION` | -303207 | The log file extension does not match the format. |
| `FAILED_BUFFER_TOO_SMALL` | -303208 | The provided buffer is too small. |
| `FAILED_FILE_ALREADY_EXISTS` | -303209 | The file already exists (with `CREATE_ONLY` mode). |

### Exceptions

#### `NiIOTraceError`

Raised when an API call returns a non-success status.

| Attribute | Type | Description |
|---|---|---|
| `status` | `StatusCode` | The status code that triggered the error. |

## License

This project is licensed under the [MIT License](LICENSE).