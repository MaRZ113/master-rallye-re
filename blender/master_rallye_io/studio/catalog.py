"""Retail course list with readable names and top-down map previews."""
from __future__ import annotations

import hashlib
import re
import struct
import tempfile
from pathlib import Path

import bpy
import bpy.utils.previews

_PREVIEWS = None
_CACHE: dict = {}
COUNTRIES = {"france": "France", "italy": "Italy", "spain": "Spain", "turkey": "Turkey"}
SKIP = {"template", "templatenew", "testfrance1", "multi", "smash"}


def readable(stem: str) -> str:
    """``FranceS1Flip`` -> ``France - Special stage 1 (reverse)``; no Race IDs are shown."""
    low = stem.lower()
    country = next((v for k, v in COUNTRIES.items() if low.startswith(k)), None)
    if country is None:
        return stem
    rest = stem[len(country):]
    reverse = rest.lower().endswith("flip")
    if reverse:
        rest = rest[:-4]
    m = re.fullmatch(r"(\d)", rest)
    if m:
        kind = f"Stage {m.group(1)}"
    elif re.fullmatch(r"[Ss](\d)", rest):
        kind = f"Special stage {rest[1]}"
    elif re.fullmatch(r"[Ww](\d?)", rest):
        kind = ("Wide stage " + rest[1:]).strip()
    elif re.fullmatch(r"[Mm](\d?)", rest):
        kind = ("Master stage " + rest[1:]).strip()
    else:
        kind = rest or "Stage"
    return f"{country} - {kind}" + (" (reverse)" if reverse else "")


def retail_scenes(root: Path | None) -> list[tuple[str, str]]:
    if root is None:
        return []
    key = str(root)
    if key in _CACHE:
        return _CACHE[key]
    folder = None
    for p in (root / "DataScene").iterdir():
        if p.name.lower() == "racetest":
            folder = p
    out = []
    if folder is not None:
        for xml in sorted(folder.glob("*.xml")):
            if xml.stem.lower() in SKIP:
                continue
            out.append((xml.stem, readable(xml.stem)))
    out.sort(key=lambda kv: kv[1])
    _CACHE[key] = out
    return out


_ENUM_ITEMS: list = []


def scene_enum_items(context):
    from .convert import resource_root
    global _ENUM_ITEMS
    try:
        root = resource_root(context)
    except Exception:
        root = None
    items = [(stem, name, f"{name}  [{stem}]") for stem, name in retail_scenes(root)]
    if not items:
        items = [("France1", "France - Stage 1", "Retail France1 (resource root not found yet)")]
    _ENUM_ITEMS = items
    return _ENUM_ITEMS


def preview_icon(root: Path, stem: str) -> int:
    """Icon id of a 128 px top-down map of the course land database (cached on disk)."""
    global _PREVIEWS
    if _PREVIEWS is None:
        _PREVIEWS = bpy.utils.previews.new()
    if stem in _PREVIEWS:
        return _PREVIEWS[stem].icon_id
    try:
        path = _render_map(root, stem)
    except Exception:
        return 0
    if path is None:
        return 0
    return _PREVIEWS.load(stem, str(path), "IMAGE").icon_id


def _render_map(root: Path, stem: str, size: int = 128) -> Path | None:
    import numpy as np
    from .core.race import read_scene
    from .core.textures import encode_png
    from .core.validate import ci_path
    scene_path = ci_path(root, f"DataScene/RaceTest/{stem}.xml")
    if scene_path is None:
        return None
    scene = read_scene(scene_path)
    if not scene["landscape"]:
        return None
    dx = ci_path(root, "DataGx/" + scene["landscape"][0].replace("\\", "/") + ".dx")
    if dx is None:
        return None
    digest = hashlib.sha1(f"{dx}:{dx.stat().st_size}".encode()).hexdigest()[:12]
    out = Path(tempfile.gettempdir()) / "mr-course-studio-previews" / f"{stem}-{digest}.png"
    if out.exists():
        return out
    data = dx.read_bytes()
    at = data.rfind(struct.pack("<If", 1400, 20.0))
    if at < 0:
        return None
    _, cell, d0, d1, x0, y0, z0, x1, y1, z1 = struct.unpack_from("<IfII3f3f", data, at)
    off = at + 40
    for _ in range(d0 * d1):
        (n,) = struct.unpack_from("<I", data, off)
        off += 4 + 4 * n
    (ns,) = struct.unpack_from("<I", data, off)
    off += 4
    for _ in range(ns):
        (n,) = struct.unpack_from("<I", data, off)
        off += 4 + n
    (nr,) = struct.unpack_from("<I", data, off)
    off += 4
    recs = np.frombuffer(data, dtype="<f4", count=nr * 14, offset=off).reshape(nr, 14)
    cx = recs[:, [0, 3, 6]].mean(axis=1)
    cy = recs[:, [1, 4, 7]].mean(axis=1)
    cz = recs[:, [2, 5, 8]].mean(axis=1)
    span = max(x1 - x0, z1 - z0) or 1.0
    ix = ((cx - x0) / span * (size - 1)).astype(int).clip(0, size - 1)
    iz = ((cz - z0) / span * (size - 1)).astype(int).clip(0, size - 1)
    height = np.full((size, size), np.nan)
    for a, b, h in zip(ix, iz, cy):
        if np.isnan(height[b, a]) or h > height[b, a]:
            height[b, a] = h
    lo, hi = np.nanmin(height), np.nanmax(height)
    img = np.zeros((size, size, 4), dtype=np.uint8)
    t = np.nan_to_num((height - lo) / max(hi - lo, 1e-6))
    mask = ~np.isnan(height)
    img[..., 0] = (60 + 150 * t).astype(np.uint8)
    img[..., 1] = (110 + 110 * t).astype(np.uint8)
    img[..., 2] = (50 + 60 * t).astype(np.uint8)
    img[..., 3] = np.where(mask, 255, 0)
    route = scene["raceline"]
    for p in route:
        a = int((p[0] - x0) / span * (size - 1))
        b = int((p[2] - z0) / span * (size - 1))
        if 0 <= a < size and 0 <= b < size:
            img[b, a] = (230, 40, 40, 255)
    img = img[::-1]
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_bytes(encode_png(size, size, img.tobytes()))
    return out



def unregister():
    global _PREVIEWS
    if _PREVIEWS is not None:
        bpy.utils.previews.remove(_PREVIEWS)
        _PREVIEWS = None
