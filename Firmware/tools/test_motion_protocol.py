import binascii
import csv
import io
import math
import struct
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path
from imu_protocol import decode_imu, MixedDecoder
from receive_eeg import decode as decode_eeg, Decoder as EegDecoder
from receive_motion import csv_row, FIELDS
from test_protocol import frame as eeg_frame

HERE = Path(__file__).resolve().parent


def fixture(name="motion_v1"):
    return bytearray.fromhex((HERE / "fixtures" / f"{name}.hex").read_text(encoding="ascii"))


def seal(data):
    data[-2:] = binascii.crc_hqx(data[:-2], 0xffff).to_bytes(2, "little")
    return bytes(data)


class MotionProtocolTest(unittest.TestCase):
    def test_actual_cpp_encoder_fixture(self):
        r = decode_imu(fixture())
        self.assertEqual(r["seq"], 7)
        self.assertEqual(r["gyro_dps"], (1, 2, 3))
        self.assertAlmostEqual(r["position_m"][0], 1.4995, places=3)
        self.assertAlmostEqual(r["velocity_mps"][0], 1, places=3)
        self.assertEqual(r["rate_counter"], 15)
        self.assertEqual(r["acc_counter"], 0)  # distinct group offsets are permitted
        self.assertTrue(r["flags"] & 8192)

    def test_actual_cpp_invalid_state_fixture(self):
        r = decode_imu(fixture("motion_invalid_v1"))
        self.assertTrue(r["flags"] & 512)
        self.assertFalse(r["flags"] & (1 | 2 | 4))
        self.assertTrue(all(map(math.isnan, (*r["quaternion"], *r["position_m"], *r["velocity_mps"]))))

    def test_timestamp_and_coordinate_epoch(self):
        p = fixture(); struct.pack_into("<Q", p, 12, 2**40+123); struct.pack_into("<I", p, 112, 0xffffffff)
        r = decode_imu(seal(p)); self.assertEqual(r["device_us"], 2**40+123); self.assertEqual(r["origin_id"], 0xffffffff)

    def test_fragmented_multiplexed_usb(self):
        d = MixedDecoder(decode_eeg); out = []
        for byte in b"# ready\n" + eeg_frame([0]*8) + fixture() + fixture("motion_invalid_v1"):
            out += d.feed(bytes([byte]))
        self.assertEqual([kind for kind, _ in out], ["eeg", "imu", "imu"])
        self.assertEqual(d.bad_crc, 0)

    def test_valid_eeg_record_inside_valid_imu_is_not_another_record(self):
        p = fixture("motion_invalid_v1"); p[8:58] = eeg_frame([0]*8, seq=77); seal(p)
        d = MixedDecoder(decode_eeg); out = d.feed(seal(p) + eeg_frame([1]*8, seq=88))
        self.assertEqual([kind for kind, _ in out], ["imu", "eeg"])
        self.assertEqual(out[1][1]["seq"], 88)
        legacy = EegDecoder(); rows = legacy.feed(seal(p) + eeg_frame([1]*8, seq=88))
        self.assertEqual([r["seq"] for r in rows], [88]); self.assertEqual(legacy.imu_discarded, 1)

    def test_corruption_and_bad_length_resynchronize(self):
        p = fixture(); p[50] ^= 1
        d = MixedDecoder(decode_eeg); rows = d.feed(p + b"YIMU\x01\x7f" + fixture())
        self.assertEqual(len(rows), 1); self.assertGreater(d.bad_crc, 0)

    def test_quality_cannot_claim_absolute_yaw(self):
        p = fixture(); flags = int.from_bytes(p[6:8], "little") & ~16; struct.pack_into("<H", p, 6, flags)
        with self.assertRaises(ValueError): decode_imu(seal(p))

    def test_expired_or_stopped_cannot_have_valid_trajectory(self):
        for extra in [256, 4096, 64, 128]:
            p = fixture(); struct.pack_into("<H", p, 6, int.from_bytes(p[6:8], "little") | extra)
            with self.assertRaises(ValueError): decode_imu(seal(p))
        p = fixture(); struct.pack_into("<f", p, 104, 3.1)
        with self.assertRaises(ValueError): decode_imu(seal(p))

    def test_nan_not_silently_exported_as_valid_position(self):
        p = fixture(); struct.pack_into("<f", p, 88, math.nan)
        with self.assertRaises(ValueError): decode_imu(seal(p))

    def test_csv_layout_and_eof(self):
        self.assertEqual(len(csv_row(decode_imu(fixture()))), len(FIELDS))
        with tempfile.TemporaryDirectory(dir=HERE) as folder:
            p = Path(folder)/"motion.yim"; p.write_bytes(fixture() + fixture("motion_invalid_v1"))
            run = subprocess.run([sys.executable, str(HERE/"receive_motion.py"), "--file", str(p)], text=True, capture_output=True, check=True, timeout=10)
        rows = list(csv.DictReader(io.StringIO(run.stdout)))
        self.assertEqual(len(rows), 2); self.assertEqual(rows[1]["position_x_m"], "nan")
        self.assertIn("sample_gap", rows[1]["quality"])


if __name__ == "__main__": unittest.main()
