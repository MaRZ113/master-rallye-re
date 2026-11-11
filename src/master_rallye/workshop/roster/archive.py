"""Existing local-header archive reader used by Vehicle Manager."""
from pathlib import Path
import struct

def norm(name: str) -> str:
    return name.replace("\\", "/").lower()


def archive_index(path: Path):
    """Data.sma = ZIP local headers only (no central directory)."""
    data = path.read_bytes()
    out, at = {}, 0
    while at + 30 <= len(data):
        sig, _v, flags, method, _t, _d, _crc, cs, us, nl, xl = struct.unpack_from("<IHHHHHIIIHH", data, at)
        if sig != 0x04034B50:
            break
        if flags & 8:
            raise ValueError("Data.sma uses data descriptors; unsupported")
        start = at + 30 + nl + xl
        out[norm(data[at + 30:at + 30 + nl].decode("latin-1"))] = (method, start, cs, us)
        at = start + cs
    return data, out


