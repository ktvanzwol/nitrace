from pathlib import Path

import nitrace

# Launch the application (minimized by default)
nitrace.launch_io_trace()

# Start tracing to a plain-text log file
nitrace.start_tracing(
    log_file_setting=nitrace.LogFileSetting.IO_TRACE,
    file_path=Path.cwd() / "trace.nitrace",
    file_write_mode=nitrace.FileWriteMode.CREATE_OR_OVERWRITE,
)

# Insert a marker into the trace log
nitrace.log_message("Test started")

# ... run your NI driver calls ...

# Stop tracing and leave the application running to inspect the log.
nitrace.stop_tracing()

print("Trace complete. Log file saved to:", Path.cwd() / "trace.nitrace")
