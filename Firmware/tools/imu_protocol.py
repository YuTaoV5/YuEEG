"""YuEEG YIMU v1/128 decoder and atomic EEG/IMU USB demultiplexer."""
import binascii
import math
import struct

FRAME_SIZE = 128
FLAGS = {1: "sensor_valid", 2: "attitude_valid", 4: "trajectory_valid", 8: "warmup",
         16: "yaw_unreferenced", 32: "position_relative", 64: "sample_gap", 128: "aligning",
         256: "window_expired", 512: "sensor_fault", 1024: "eeg_active", 2048: "align_rejected",
         4096: "stopped", 8192: "hardware_unverified", 16384: "tilt_feedback"}


def decode_imu(frame):
    if len(frame) != FRAME_SIZE or frame[:6] != b"YIMU\x01\x80":
        raise ValueError("IMU frame/version/length")
    if binascii.crc_hqx(frame[:126], 0xffff) != int.from_bytes(frame[126:], "little"):
        raise ValueError("IMU CRC")
    flags, seq, us, eeg_seq, eeg_us, missed, rejected = struct.unpack_from("<HIQIIII", frame, 6)
    values = struct.unpack_from("<18f", frame, 36)
    gyro, accel, q, velocity, position = values[:3], values[3:6], values[6:10], values[10:13], values[13:16]
    temp, age = values[16:]
    if flags & 0x8000 or flags & 48 != 48:
        raise ValueError("IMU frame must identify relative position and unreferenced yaw")
    if flags & 1 and (not all(map(math.isfinite, (*gyro, *accel, temp))) or frame[108] > 15 or frame[109] > 15):
        raise ValueError("IMU invalid sensor fields")
    if flags & 2:
        if not all(map(math.isfinite, q)) or abs(sum(v*v for v in q) - 1) > .02:
            raise ValueError("IMU invalid quaternion")
    elif not all(map(math.isnan, q)):
        raise ValueError("IMU invalid attitude must be NaN")
    if flags & 4:
        if not flags & 2 or flags & (64 | 128 | 256 | 512 | 2048 | 4096) or not 0 <= age <= 3.00001:
            raise ValueError("IMU invalid trajectory state")
        if not all(map(math.isfinite, (*velocity, *position))):
            raise ValueError("IMU invalid trajectory fields")
    elif not all(map(math.isnan, (*velocity, *position))):
        raise ValueError("IMU invalid trajectory must be NaN")
    if flags & 4096 and flags & (1 | 2 | 4 | 128):
        raise ValueError("IMU stopped state contradicts validity")
    if flags & 2:
        w, x, y, z = q
        roll = math.degrees(math.atan2(2*(w*x+y*z), 1-2*(x*x+y*y)))
        pitch = math.degrees(math.asin(max(-1, min(1, 2*(w*y-z*x)))))
        yaw = math.degrees(math.atan2(2*(w*z+x*y), 1-2*(y*y+z*z)))
    else:
        roll = pitch = yaw = math.nan
    origin, latency, drops = struct.unpack_from("<III", frame, 112)
    return dict(seq=seq, device_us=us, flags=flags, quality="|".join(name for mask, name in FLAGS.items() if flags & mask),
                eeg_seq=eeg_seq, eeg_us32=eeg_us, missed=missed, rejected=rejected, gyro_dps=gyro,
                accel_mps2=accel, quaternion=q, velocity_mps=velocity, position_m=position,
                temperature_C=temp, trajectory_age_s=age, origin_id=origin, read_latency_us=latency,
                queue_drops=drops, rate_counter=frame[108], acc_counter=frame[109],
                roll_deg=roll, pitch_deg=pitch, relative_yaw_deg=yaw)


class MixedDecoder:
    """Consume validated whole records; never interpret magic inside their payloads."""
    def __init__(self, eeg_decode):
        self.eeg_decode = eeg_decode
        self.buffer = bytearray()
        self.bad_crc = 0  # retained legacy name: includes other malformed records

    def feed(self, data):
        self.buffer.extend(data)
        out = []
        while True:
            starts = [(self.buffer.find(magic), magic) for magic in (b"YEEG", b"YIMU")]
            starts = [(pos, magic) for pos, magic in starts if pos >= 0]
            if not starts:
                self.buffer = self.buffer[-3:]
                break
            pos, magic = min(starts)
            if pos:
                del self.buffer[:pos]
            if len(self.buffer) < 6:
                break
            size = 50 if magic == b"YEEG" else FRAME_SIZE
            if self.buffer[4] != 1 or (magic == b"YIMU" and self.buffer[5] != FRAME_SIZE):
                self.bad_crc += 1
                del self.buffer[0]
                continue
            if len(self.buffer) < size:
                break
            try:
                frame = bytes(self.buffer[:size])
                result = self.eeg_decode(frame) if magic == b"YEEG" else decode_imu(frame)
            except ValueError:
                self.bad_crc += 1
                del self.buffer[0]
                continue
            out.append(("eeg" if magic == b"YEEG" else "imu", result))
            del self.buffer[:size]
        return out
