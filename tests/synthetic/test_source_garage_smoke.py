"""Asset-independent corruption and read-only-boundary checks."""
import importlib.util
import struct
import sys
import tempfile
import unittest
from unittest import mock
from pathlib import Path

SPEC = importlib.util.spec_from_file_location("source_garage_smoke", Path(__file__).resolve().parents[2] / "tools/source_garage_smoke.py")
smoke = importlib.util.module_from_spec(SPEC)
sys.modules[SPEC.name] = smoke
SPEC.loader.exec_module(smoke)


def pod(name=b"MODELS/test.SMF\0", blob=b"model"):
    header = bytearray(96)
    header[:4] = b"POD2"
    struct.pack_into("<II", header, 88, 1, 0)
    offset = 116 + len(name)
    return bytes(header) + struct.pack("<5I", 0, len(blob), offset, 0, 0) + name + blob


def smf(face="0,1,2", vertex="0,0,0,0,1,0,0,0"):
    return ("C3DModel\r\r\n4\r\r\n1\r\r\n0,50\r\r\nBody\r\r\n1\r\r\n1\r\r\n3,1,1,0\r\r\n"
            "1,1,64,0,1,test.RAW\r\r\n" + "\r\r\n".join([vertex] * 3) + "\r\r\n" + face + "\r\r\n").encode()


class SourceGarageSmokeTests(unittest.TestCase):
    def test_pod_member_range_and_path(self):
        data = pod()
        entries = smoke.pod2_members(data)
        self.assertEqual(smoke.member_bytes(data, entries[0]), b"model")
        self.assertEqual(entries[0].name, "MODELS/test.SMF")

    def test_pod_rejects_traversal_absolute_and_drive_names(self):
        for name in (b"../escape\0", b"C:/escape\0", b"/absolute\0", b"x\\..\\escape\0"):
            with self.subTest(name=name), self.assertRaises(smoke.InspectionError):
                smoke.pod2_members(pod(name))

    def test_pod_rejects_truncated_payload_name_and_count(self):
        for data in (pod()[:-1], pod(b"unterminated"), b"POD2", b"POD3" + bytes(100)):
            with self.subTest(length=len(data)), self.assertRaises(smoke.InspectionError):
                smoke.pod2_members(data)
        data = bytearray(pod())
        struct.pack_into("<I", data, 88, smoke.MAX_ENTRIES + 1)
        with self.assertRaises(smoke.InspectionError):
            smoke.pod2_members(data)

    def test_smf_retains_source_values_uvs_and_crcrlf(self):
        parsed = smoke.parse_smf(smf())
        self.assertEqual(parsed["triangles"], 1)
        self.assertEqual(parsed["objects"][0]["vertices_by_frame"][0][0], [0, 0, 0, 0, 1, 0, 0, 0])
        self.assertEqual(parsed["objects"][0]["material_raw"][5], "test.RAW")

    def test_smf_rejects_index_nonfinite_truncation_and_tail(self):
        for data in (smf(face="0,1,3"), smf(vertex="nan,0,0,0,1,0,0,0"), smf()[:-12], smf() + b"unknown\n"):
            with self.subTest(data=data[-25:]), self.assertRaises(smoke.InspectionError):
                smoke.parse_smf(data)

    def test_smf_rejects_declared_allocation_bomb_before_reading_vertices(self):
        data = smf().replace(b"3,1,1,0", b"999999999,1,1,0")
        with self.assertRaises(smoke.InspectionError):
            smoke.parse_smf(data)

    def test_raw_indexed_palette_and_explicit_opacity(self):
        palette = bytes([10, 20, 30, 40, 50, 60]) + bytes(762)
        width, pixels = smoke.raw_rgba(bytes([0, 1, 1, 0]), palette, bytes([0, 32, 128, 255]))
        self.assertEqual(width, 2)
        self.assertEqual(pixels[:8], bytes([10, 20, 30, 0, 40, 50, 60, 32]))

    def test_raw_rejects_partial_palette_nonsquare_and_alpha_loss(self):
        for raw, palette, opacity in ((b"abc", bytes(768), None), (b"aaaa", bytes(767), None),
                                      (b"aaaa", bytes(768), b"x"), (b"", bytes(768), None)):
            with self.subTest(raw=raw), self.assertRaises(smoke.InspectionError):
                smoke.raw_rgba(raw, palette, opacity)

    def test_cod_directory_bounds_and_actual_magic_length(self):
        name = b"Vehicles/Pajero/body.4x4\0".ljust(128, b".")
        data = b"->Unique Pc HUNGARY<-\0\0\0" + struct.pack("<I", 136) + name + struct.pack("<II", 164, 4) + b"mesh"
        self.assertEqual(smoke.cod_members(data)[0]["name"], "Vehicles/Pajero/body.4x4")
        with self.assertRaises(smoke.InspectionError):
            smoke.cod_members(data[:-1])
        invalid = bytearray(data)
        struct.pack_into("<I", invalid, 24, 135)
        with self.assertRaises(smoke.InspectionError):
            smoke.cod_members(invalid)

    def test_output_is_disjoint_and_never_reused(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            source = root / "source"
            source.mkdir()
            original = source / "original"
            original.write_bytes(b"immutable")
            for output in (source / "inside", root):
                with self.assertRaises(smoke.InspectionError):
                    smoke.destination(output, [source])
            output = root / "private-output"
            smoke.destination(output, [source])
            with self.assertRaises(smoke.InspectionError):
                smoke.destination(output, [source])
            self.assertEqual(original.read_bytes(), b"immutable")

    def test_sr2_rejects_wrong_layout_and_out_of_bounds_root(self):
        for data in (b"", bytes(192), struct.pack("<8I", 192, 32, 1, 0, 0, 0, 0, 0) + bytes(160)):
            with self.subTest(length=len(data)), self.assertRaises(smoke.InspectionError):
                smoke.sr2_root_mesh(data)

    def test_screamer_complete_streams_and_rejects_silent_uv_loss(self):
        streams = {"verticle.dat": struct.pack("<H9f", 3, 0, 0, 0, 1, 0, 0, 0, 1, 0),
                   "faces.dat": struct.pack("<4H", 1, 0, 1, 2), "mapcoord.dat": struct.pack("<6f", 0, 0, 1, 0, 0, 1),
                   "norms.dat": struct.pack("<9f", *([0, 0, 1] * 3)), "textures.dat": struct.pack("<H", 2)}
        self.assertEqual(smoke.screamer_mesh(streams)["material_ids"], [2])
        for broken in ({k: v for k, v in streams.items() if k != "mapcoord.dat"},
                       {**streams, "faces.dat": struct.pack("<4H", 1, 0, 1, 3)},
                       {**streams, "textures.dat": b""}):
            with self.assertRaises(smoke.InspectionError):
                smoke.screamer_mesh(broken)

    def test_read_probe_preserves_contents_size_mtime_and_directory(self):
        with tempfile.TemporaryDirectory() as temp:
            source = Path(temp) / "original.pod"
            source.write_bytes(pod())
            before = (source.read_bytes(), source.stat().st_size, source.stat().st_mtime_ns, list(Path(temp).iterdir()))
            smoke.pod2_members(smoke.read_bounded(source))
            after = (source.read_bytes(), source.stat().st_size, source.stat().st_mtime_ns, list(Path(temp).iterdir()))
            self.assertEqual(before, after)

    def test_read_probe_rejects_input_changed_during_read(self):
        with tempfile.TemporaryDirectory() as temp:
            source = Path(temp) / "original"
            source.write_bytes(b"before")
            original_open = Path.open

            class ChangedReader:
                def __enter__(self):
                    self.handle = original_open(source, "rb")
                    return self

                def read(self, size):
                    data = self.handle.read(size)
                    self.handle.close()
                    with original_open(source, "wb") as output:
                        output.write(b"changed-longer")
                    return data

                def __exit__(self, *args):
                    self.handle.close()

            with mock.patch.object(Path, "open", return_value=ChangedReader()), self.assertRaises(smoke.InspectionError):
                smoke.read_bounded(source)

    def test_linked_ancestor_is_rejected_before_reading(self):
        with tempfile.TemporaryDirectory() as temp:
            parent = Path(temp)
            path = parent / "file"
            path.write_bytes(b"immutable")
            original_is_symlink = Path.is_symlink
            with mock.patch.object(Path, "is_symlink", lambda part: part == parent or original_is_symlink(part)):
                with self.assertRaises(smoke.InspectionError):
                    smoke.read_bounded(path)


if __name__ == "__main__":
    unittest.main()
