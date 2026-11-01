"""Receive YIMU CSV from USB, UDP9002 or .yim backup. No absolute heading/position."""
import argparse
import csv
import socket
import sys
import time
from imu_protocol import MixedDecoder
from receive_eeg import decode as decode_eeg

FIELDS = ["seq", "device_us", "origin_id", "flags", "quality", "roll_deg", "pitch_deg", "relative_yaw_deg",
          *[f"q_{n}" for n in "wxyz"], *[f"velocity_{n}_mps" for n in "xyz"], *[f"position_{n}_m" for n in "xyz"],
          *[f"gyro_{n}_dps" for n in "xyz"], *[f"accel_{n}_mps2" for n in "xyz"], "temperature_C",
          "trajectory_age_s", "eeg_seq", "eeg_us32", "missed", "rejected", "read_latency_us", "queue_drops", "rate_counter", "acc_counter"]


def csv_row(r):
    flat = dict(r)
    for prefix, key, axes, suffix in [("q", "quaternion", "wxyz", ""), ("velocity", "velocity_mps", "xyz", "_mps"),
                                    ("position", "position_m", "xyz", "_m"), ("gyro", "gyro_dps", "xyz", "_dps"), ("accel", "accel_mps2", "xyz", "_mps2")]:
        flat.update({f"{prefix}_{axis}{suffix}": value for axis, value in zip(axes, r[key])})
    return [flat[name] for name in FIELDS]


def main():
    p = argparse.ArgumentParser(description=__doc__)
    g = p.add_mutually_exclusive_group(required=True)
    g.add_argument("--serial"); g.add_argument("--udp", type=int); g.add_argument("--file")
    p.add_argument("--start", action="store_true", help="USB: request imu start; EEG must be stopped")
    p.add_argument("--align", action="store_true", help="USB: explicitly hold stationary; request alignment after valid data arrives")
    p.add_argument("--eeg-output", help="Optional separate CSV for multiplexed EEG records")
    a = p.parse_args()
    if (a.start or a.align) and not a.serial:
        p.error("--start/--align require USB serial; Wi-Fi uses send_eeg_command.py")
    if a.file:
        io = open(a.file, "rb"); read = lambda: io.read(4096)
    elif a.serial:
        import serial
        io = serial.Serial(a.serial, 921600, timeout=.1)
        if a.start: io.write(b"imu start\n")
        if a.align: print("Hold the device stationary through alignment (>=2s after request).", file=sys.stderr)
        read = lambda: io.read(4096)
    else:
        io = socket.socket(socket.AF_INET, socket.SOCK_DGRAM); io.bind(("0.0.0.0", a.udp)); io.settimeout(.2); read = lambda: io.recvfrom(65535)[0]
    decoder = MixedDecoder(decode_eeg); writer = csv.writer(sys.stdout); writer.writerow(FIELDS)
    eeg_file = open(a.eeg_output, "w", newline="", encoding="utf8") if a.eeg_output else None
    eeg_writer = csv.writer(eeg_file) if eeg_file else None
    if eeg_writer: eeg_writer.writerow(["seq", "device_us32", "missed", "mode", "gain", "flags", *[f"ch{i}_uV" for i in range(1, 9)]])
    first_valid = None; previous = None; last_motion = None; stale_noted = False
    try:
        while True:
            try: chunk = read()
            except socket.timeout: chunk = b""
            if a.file and not chunk: break
            if not a.file and last_motion is not None and time.monotonic()-last_motion > .5 and not stale_noted:
                print("IMU stream stale: latest record is historical; no current solution.", file=sys.stderr); stale_noted = True
            for kind, r in decoder.feed(chunk):
                if kind == "eeg":
                    if eeg_writer: eeg_writer.writerow([r[k] for k in ["seq", "device_us", "missed_drdy", "mode", "gain", "flags"]] + r["uV"])
                    continue
                if previous is not None and (r["seq"]-previous) & 0xffffffff != 1:
                    print(f"IMU transport sequence gap: {previous}->{r['seq']}", file=sys.stderr)
                previous = r["seq"]; writer.writerow(csv_row(r))
                last_motion = time.monotonic(); stale_noted = False
                if a.align and r["flags"] & 1:
                    if first_valid is None: first_valid = time.monotonic()
                    if time.monotonic() - first_valid >= 1:
                        io.write(b"imu align\n"); a.align = False
                        print("Alignment requested; remain stationary for >=2s.", file=sys.stderr)
    except KeyboardInterrupt:
        pass
    finally:
        io.close()
        if eeg_file: eeg_file.close()
        print(f"Malformed/CRC frames: {decoder.bad_crc}", file=sys.stderr)


if __name__ == "__main__": main()
