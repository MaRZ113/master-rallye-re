"""Independent canonical PE mapping check for compact REA instruction evidence."""
import argparse
import hashlib
import json
from pathlib import Path
import struct

HERE = Path(__file__).parent
EXE = Path(r"D:/Game/Master Rallye Pristine/MRallye.exe")
SHA = "bf8aef32407eb6552c05045b8abef149f32983cedd9503b865069b444c5f96b4"


def file_offset(data, address, size):
    if data[:2] != b"MZ":
        raise ValueError("Missing original MZ header")
    pe = struct.unpack_from("<I", data, 0x3c)[0]
    if data[pe:pe+4] != b"PE\0\0":
        raise ValueError("Missing original PE header")
    count = struct.unpack_from("<H", data, pe+6)[0]
    optsize = struct.unpack_from("<H", data, pe+20)[0]
    opt = pe + 24
    if struct.unpack_from("<H", data, opt)[0] != 0x10b:
        raise ValueError("PE32 required")
    base = struct.unpack_from("<I", data, opt+28)[0]
    rva = address - base
    matches = []
    for n in range(count):
        start = opt + optsize + n*40
        _, virtual, rawsize, raw = struct.unpack_from("<IIII", data, start+8)
        if virtual <= rva and rva+size <= virtual+rawsize:
            matches.append(raw+rva-virtual)
    if len(matches) != 1:
        raise ValueError("Original initialized PE mapping not unique")
    return matches[0]


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--exe", type=Path, default=EXE)
    args = parser.parse_args()
    data = args.exe.read_bytes()
    if hashlib.sha256(data).hexdigest() != SHA:
        raise ValueError("Canonical original PC executable SHA mismatch")
    evidence = json.loads((HERE / "native-owner-evidence.json").read_text(encoding="utf8"))
    windows = []
    for instruction in evidence["callback"]["instruction_window"]:
        original = bytes.fromhex(instruction["bytes"])
        address = int(instruction["address"], 16)
        offset = file_offset(data, address, len(original))
        if data[offset:offset+len(original)] != original:
            raise ValueError("Original instruction-byte mismatch at " + hex(address))
        windows.append({"address": hex(address), "file_offset": offset,
                        "size": len(original), "bytes_hex": original.hex()})
    # Original vtable proves callback entry independently of Ghidra boundaries.
    offset = file_offset(data, 0x69020c+0x10, 4)
    if struct.unpack_from("<I", data, offset)[0] != 0x44c4c0:
        raise ValueError("Original CarMover vtable callback mismatch")
    report = {"schema_version": 1, "exe_sha256": SHA,
              "instruction_windows_checked": len(windows), "windows": windows,
              "original_vtable_callback": {"table": "0x69020c", "slot_offset": "0x10",
                                           "target": "0x44c4c0", "file_offset": offset},
              "result": "PASS", "live_runtime_identity": "NOT_PERFORMED"}
    (HERE / "native-byte-validation.json").write_text(json.dumps(report, indent=2)+"\n", encoding="utf8")
    print("PASS: original PE SHA and", len(windows), "instruction windows; vtable callback verified")


if __name__ == "__main__":
    main()
