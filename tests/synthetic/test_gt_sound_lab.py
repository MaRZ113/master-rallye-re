"""Generated fixtures only; no proprietary bank, database or executable bytes."""
import json
from pathlib import Path
import struct
import sys
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "tools"))
import gt_sound_lab as lab
from gt4_audio_extract import parse_engn, extract


def table(rows, size, flags=0):
    return (struct.pack("<4sHHII", b"GTDB", flags, 8, len(rows), size)
            + b"".join(struct.pack("<II", rid, i * size) for i, (rid, raw) in enumerate(rows))
            + b"".join(raw for rid, raw in rows))


def labels(rows):
    strings = bytearray(); records = []
    for name, rid in rows:
        encoded = name.encode() + b"\0"
        records.append(struct.pack("<II", len(strings), rid))
        strings += struct.pack("<H", len(encoded)) + encoded
    return struct.pack("<4sIII", b"GTID", len(rows), 0, 0) + b"".join(records) + strings


def strings(rows):
    payload = bytearray(); offsets = []
    for name in rows:
        text = name.encode() + b"\0"; offsets.append(len(payload))
        payload += struct.pack("<H", len(text)) + text
    return struct.pack("<4sIII", b"GTST", len(rows), 1, 0) + struct.pack("<" + "I" * len(rows), *offsets) + payload


def fixture(root):
    folder = root / "specdb/GT4_PREMIUM_US2560"; folder.mkdir(parents=True)
    ge = bytearray(24); struct.pack_into("<ii", ge, 0, 17, 36)
    parts = bytearray(b"\xff" * 208)
    struct.pack_into("<ii", parts, 88, 82, 12)
    struct.pack_into("<ii", parts, 104, 91, 14)
    struct.pack_into("<ii", parts, 152, 92, 20)
    engine = bytearray(113); struct.pack_into("<H", engine, 24, 9876)
    turbo = bytearray(18); turbo[9] = 12
    muffler = bytearray(7); muffler[6] = 3
    for name, rid, raw in (("GENERIC_CAR", 3, ge), ("DEFAULT_PARTS", 17, parts),
                           ("ENGINE", 82, engine), ("NATUNE", 90, bytes(11)),
                           ("TURBINEKIT", 91, turbo), ("MUFFLER", 92, muffler)):
        (folder / (name + ".dbt")).write_bytes(table([(rid, raw)], len(raw)))
    (folder / "GENERIC_CAR.idi").write_bytes(labels([("synthetic_car", 3)]))
    for name, tid in {"DEFAULT_PARTS": 36, "ENGINE": 12, "NATUNE": 13, "TURBINEKIT": 14, "MUFFLER": 20}.items():
        raw = bytearray(labels([("synthetic_part", 1)])); struct.pack_into("<I", raw, 12, tid)
        (folder / (name + ".idi")).write_bytes(raw)
    (folder / "CAR_VARIATION_american.dbt").write_bytes(table([(3, struct.pack("<ii", 8, 42))], 8, 2))
    variation = bytes(52)
    (folder / "VARIATIONamerican.dbt").write_bytes(table([(8, variation), (8, variation)], 52, 2))
    (folder / "american_StrDB.sdb").write_bytes(strings(["testmodel"]))
    (folder / "CARS").mkdir()
    (folder / "CARS/0000000000000003").write_bytes(struct.pack("<II", 3, 0) + struct.pack("<12i", 82, 12, 0, 0, 91, 14, 0, 0, 92, 20, 3, 0))
    bank = root / "carsound/turbo3/9876"; bank.parent.mkdir(parents=True); bank.write_bytes(b"synthetic placeholder")
    return folder


class LabTests(unittest.TestCase):
    def test_raw_key_chain_model_variations_and_default_candidate(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp); folder = fixture(root)
            report = lab.gt4_catalog(root); v = lab.select_vehicle(report, "testmodel")
            self.assertEqual(report["counts"], {"vehicles": 1, "banks": 1, "sound_ids": 1})
            self.assertEqual((v["vehicle_id"], v["sound_id"]), ("synthetic_car", 9876))
            self.assertEqual(v["model_codes"], ["testmodel"])
            self.assertEqual(v["default_tuning"]["MUFFLER"]["default_parts_field_offset"], 152)
            self.assertEqual(v["default_native_bank_candidate"]["variant"], "turbo3")
            self.assertFalse(v["default_native_bank_candidate"]["runtime_confirmed"])
            self.assertEqual(len(v["source_rows"]["VARIATIONamerican"]), 2)
            self.assertEqual([x["status"] for x in v["tuning_options"]], ["SOURCE_PART_KEY_VERIFIED"] * 3)
            # The original flags and duplicate IDs were never written back.
            raw = (folder / "VARIATIONamerican.dbt").read_bytes()
            self.assertEqual(struct.unpack_from("<H", raw, 4)[0], 2)
            self.assertEqual(struct.unpack_from("<I", raw, 24)[0], 8)

    def test_invalid_reference_and_category_preserved(self):
        with tempfile.TemporaryDirectory() as temp:
            folder = fixture(Path(temp))
            raw = bytearray((folder / "DEFAULT_PARTS.dbt").read_bytes())
            struct.pack_into("<i", raw, 24 + 92, 99)
            (folder / "DEFAULT_PARTS.dbt").write_bytes(raw)
            with self.assertRaisesRegex(ValueError, "Engine reference"):
                lab.gt4_catalog(Path(temp))
            tables = {"MUFFLER": lab.SourceTable(folder / "MUFFLER.dbt", 7)}
            records = struct.pack("<II12i", 3, 0, 92, 20, 1, 0, 999, 20, 1, 0, -1, -1, 2, 0)
            got = lab.car_parts(records, tables)
            self.assertEqual([r["status"] for r in got], ["SOURCE_CATEGORY_DISAGREEMENT", "UNRESOLVED_SOURCE_ROW", "ABSENT_SOURCE_KEY"])

    def test_bounded_strings_and_unknown_table_flags(self):
        good = labels([("one", 2), ("two", 3)])
        self.assertEqual(lab.label_records(good)[1]["row_id"], 3)
        self.assertEqual(lab.source_strings(strings(["model", "paint"])), ["model", "paint"])
        for raw in (good[:-1], b"", labels([("same", 1), ("same", 2)])):
            with self.assertRaises(ValueError): lab.label_records(raw)
        with tempfile.TemporaryDirectory() as temp:
            f = Path(temp) / "bad.dbt"; f.write_bytes(table([(1, b"x")], 1, 4))
            with self.assertRaises(ValueError): lab.SourceTable(f, 1, grouped=True)

    def test_originals_destination_overwrite_and_bank_escape_rejected(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp); source = root / "source"; source.mkdir()
            with self.assertRaisesRegex(ValueError, "original source"):
                lab.save_json(source / "never.json", {}, [source])
            output = root / "private.json"; lab.save_json(output, {"ok": True}, [source])
            self.assertTrue(json.loads(output.read_text())["ok"])
            with self.assertRaisesRegex(ValueError, "overwrite"):
                lab.save_json(output, {}, [source])
            for bank in ("../outside", "carsound/engine/../1", "C:/file", "sound_gt/sound/../../x.ins"):
                with self.assertRaises(ValueError): lab.gt4_bank(source, bank)

    def test_same_sample_two_rpm_records_preserved_and_exported(self):
        body = bytes([12, 6]) + bytes([0x21]) * 14 + bytes([12, 3]) + bytes([0x21]) * 14
        header = struct.pack("<4s11I", b"ENGN", 0, 80, 0, len(body), 80, 2, 48, 0, 0, 127, 127)
        raw = header + struct.pack("<4hII", 1000, 0, 1000, 12000, 1024, 0) + struct.pack("<4hII", 4000, 4000, 32767, 16000, 4096, 0) + body
        report = parse_engn(raw)
        self.assertEqual(len(report["entries"]), 2)
        self.assertEqual(report["entries"][0]["encoded_sha256"], report["entries"][1]["encoded_sha256"])
        self.assertEqual(report["entries"][0]["shared_sample_entries"], [{"table": 0, "index": 1}])
        with tempfile.TemporaryDirectory() as temp:
            source = Path(temp) / "synthetic"; source.write_bytes(raw)
            got = extract(source, Path(temp) / "audition", 24000)
            self.assertEqual(len(got["entries"]), 2)
            self.assertEqual(source.read_bytes(), raw)

    def test_comparison_and_ambiguous_selector(self):
        a = {"sha256": "a", "entries": [{"entry_id": "0", "encoded_sha256": "same"}, {"entry_id": "1", "encoded_sha256": "same"}]}
        b = {"sha256": "b", "entries": [{"entry_id": "4", "encoded_sha256": "same"}]}
        report = lab.compare_banks(a, b)
        self.assertFalse(report["same_bank_bytes"])
        self.assertEqual(report["shared_encoded_samples"][0]["entries_a"], ["0", "1"])
        with self.assertRaises(ValueError):
            lab.select_vehicle({"vehicles": [{"vehicle_id": "a", "model_codes": ["shared"]}, {"vehicle_id": "b", "model_codes": ["shared"]}]}, "shared")


if __name__ == "__main__": unittest.main()
