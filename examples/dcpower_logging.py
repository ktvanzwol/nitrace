from pathlib import Path

import hightime
import nidcpower

import nitrace
from nitrace import FileWriteMode, LogFileSetting

# This example demonstrates how to use NI Trace to log NI-DCPower driver calls to a NI Trace log file.
log_file_setting = LogFileSetting.IO_TRACE
file_path = Path.cwd() / "dcpower_trace.nitrace"

# NI-DCPower session configuration parameters
resource_name = "PXI1Slot2"
options = "Simulate=1, DriverSetup=Model:4139; BoardType:PXIe"
voltage1 = 2.0
voltage2 = 4.0
delay = 0.5


def main():
    timeout = hightime.timedelta(seconds=(delay + 1.0))

    with nidcpower.Session(resource_name=resource_name, options=options) as session:
        # Configure the session.
        session.source_mode = nidcpower.SourceMode.SINGLE_POINT
        session.output_function = nidcpower.OutputFunction.DC_VOLTAGE
        session.current_limit = 0.06
        session.voltage_level_range = 5.0
        session.current_limit_range = 0.06
        session.source_delay = hightime.timedelta(seconds=delay)
        session.measure_when = nidcpower.MeasureWhen.AUTOMATICALLY_AFTER_SOURCE_COMPLETE
        session.voltage_level = voltage1

        nitrace.log_message("[Python] NI-DCPower session configured. Starting measurements...")
        with session.initiate():
            channel_indices = f"0-{session.channel_count - 1}"
            channels = session.get_channel_names(channel_indices)
            for channel_name in channels:
                nitrace.log_message(f"[Python] Starting measurements for voltage {voltage1} on channel {channel_name}")
                print(f"Channel: {channel_name}")
                print("---------------------------------")
                print("Voltage 1:")
                print_fetched_measurements(session.channels[channel_name].fetch_multiple(count=1, timeout=timeout))
                session.voltage_level = voltage2  # on-the-fly set
                nitrace.log_message(f"[Python] Starting measurements for voltage {voltage2} on channel {channel_name}")
                print("Voltage 2:")
                print_fetched_measurements(session.channels[channel_name].fetch_multiple(count=1, timeout=timeout))
                session.output_enabled = False
                print("")

        nitrace.log_message("[Python] NI-DCPower session completed.")


def print_fetched_measurements(measurements):
    print(f"             Voltage : {measurements[0].voltage:f} V")
    print(f"              Current: {measurements[0].current:f} A")
    print(f"        In compliance: {measurements[0].in_compliance}")


if __name__ == "__main__":
    nitrace.launch_io_trace()
    nitrace.start_tracing(
        log_file_setting=log_file_setting,
        file_path=file_path,
        file_write_mode=FileWriteMode.CREATE_OR_OVERWRITE,
    )

    main()

    nitrace.stop_tracing()
    print("Trace complete. Log file saved to:", file_path)

    # Optionally, close the NI Trace application if you are done inspecting the log.
    # nitrace.close_io_trace()
