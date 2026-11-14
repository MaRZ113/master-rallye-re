"""4x4 Evolution 2 (PC) track reader: one race = one WORLD/<name>.SIT plus the level files it names.

Formats (see docs/evo2-tracks/EVO2_TRACK_FORMAT.md):
  POD2 archive      <track>.pod, members ART/ DATA/ LEVELS/ MODELS/ SCRIPTS/ WORLD/ MISSIONS/
  LEVELS/*.LVL      text: heightmap/colour/texture-list names, water height and colour, light vector
  DATA/*.RAW        256x256 little-endian u16 heights; height_ft = value / 32; cell = 32 ft; row = z, column = x
  DATA/*.CLR        256x256 u16 per-cell ground texture index (low 12 bits) into the TEX list
  DATA/*.SDW        256x256 u16 per-cell baked shadow texture index into the same list (0x8000 / 0x4000 = none)
  DATA/*.TEX        text: textureCount,shadowTextureCount then "<terrainType>,<scrubDensity>,<name>.RAW"
  DATA/*.RTD        ray-cast acceleration data (not needed)
  WORLD/*.SIT       text: race header, start vehicles, boxes (objects, checkpoints), course segments, paths
  ART/*.RAW+.ACT    8-bit indexed texture + 768-byte RGB palette (+ optional .OPA 8-bit opacity), square
  ART/*.TIF         classic TIFF (palette or RGB)
  MODELS/*.SMF      C3DModel text meshes (feet, Y up)

The 4x42.exe loader semantics were read from the symbolised GameCube build (4x4.elf, CGround::load), which keeps the
same files with big-endian words. Units are feet; the world is left-handed with Y up like Master Rallye (identity axes).
"""
from __future__ import annotations

import math
import re
import struct
from dataclasses import dataclass, field
from pathlib import Path

from evo2_formats import pod2_members, member_bytes, parse_smf, decode_classic_tiff

FT = 0.3048
GRID = 256
CELL_FT = 32.0
HEIGHT_DIV = 32.0
NO_SHADOW = (0x8000, 0x4000)

# TEX first field: terrain class = value // 100 (GC 4x4.elf string table after "Default"); 13 = water (getTypeActions)
TERRAIN_CLASSES = {0: "default", 1: "cement", 2: "dirt", 3: "mud", 4: "sand", 5: "grass", 6: "gravel", 7: "ice",
                   8: "snow", 9: "metal", 10: "wood", 11: "rock", 12: "rock", 13: "water"}
# Evo class -> Master Rallye DataGame/Surface.xml row (no sand/ice/snow/wood rows in MR)
MR_SURFACE = {"default": "harddirt", "cement": "tarmac", "dirt": "harddirt", "mud": "mud", "sand": "gravel",
              "grass": "grass", "gravel": "gravel", "ice": "harddirt", "snow": "gravel", "metal": "metal",
              "wood": "harddirt", "rock": "rock", "water": "mud"}
RACE_TYPES = {2: "race", 3: "hillclimb", 6: "mission"}


class Pod:
    """Case-insensitive member access to one POD2 archive."""

    def __init__(self, path: Path):
        self.path = Path(path)
        self.data = self.path.read_bytes()
        self.members = {m.name.casefold(): m for m in pod2_members(self.data)}

    def names(self, prefix: str = "", suffix: str = ""):
        return sorted(m.name for k, m in self.members.items() if k.startswith(prefix.casefold()) and k.endswith(suffix.casefold()))

    def has(self, name: str) -> bool:
        return name.replace("\\", "/").casefold() in self.members

    def read(self, name: str) -> bytes:
        m = self.members.get(name.replace("\\", "/").casefold())
        if m is None:
            raise KeyError(f"{self.path.name}: no member {name}")
        return member_bytes(self.data, m)

    def find(self, basename: str, folders=("ART", "MODELS", "DATA", "WORLD")) -> str | None:
        for folder in folders:
            key = f"{folder}/{basename}".casefold()
            if key in self.members:
                return self.members[key].name
        return None


def _lines(raw: bytes) -> list[str]:
    return raw.decode("latin-1").replace("\r", "").split("\n")


def _floats(text: str) -> list[float]:
    return [float(v) for v in text.replace(" ", "").split(",") if v != ""]


# ----------------------------------------------------------------------------------------------- level files
@dataclass
class Level:
    heightmap: str
    colormap: str
    texlist: str
    sky: str
    water_height_ft: float
    water_rgba: tuple
    detail_texture: str
    light_vector: tuple
    veg_texture: str


def parse_lvl(raw: bytes) -> Level:
    ls = [l.strip() for l in _lines(raw)]
    body = [l for l in ls if l and not l.startswith("//")]
    # version, flag, heightmap, clr, tex, sky, wav, then labelled pairs
    def after(label_prefix):
        for i, l in enumerate(ls):
            if l.startswith(label_prefix):
                return ls[i + 1]
        return ""
    water = _floats(after("!waterHeight"))
    rgba = tuple(int(v) for v in _floats(after("@waterR"))) or (0, 0, 0, 0)
    light = tuple(_floats(after("$lightSource")) or (0.35, -0.87, 0.35))
    return Level(heightmap=body[2], colormap=body[3], texlist=body[4], sky=body[5],
                 water_height_ft=water[0] if water else -1e9, water_rgba=rgba,
                 detail_texture=after("#detailTexture"), light_vector=light, veg_texture=after("%vegTexture"))


@dataclass
class TexEntry:
    terrain: int
    scrub: int
    name: str

    @property
    def terrain_class(self) -> str:
        return TERRAIN_CLASSES.get(self.terrain // 100, "default")


def parse_tex(raw: bytes) -> tuple[list[TexEntry], int, int]:
    ls = [l.strip() for l in _lines(raw) if l.strip()]
    counts = [int(v) for v in ls[3].split(",")]
    entries = []
    for l in ls[4:]:
        parts = l.split(",")
        if len(parts) == 3:
            entries.append(TexEntry(int(parts[0]), int(parts[1]), parts[2].strip()))
    return entries, counts[0], counts[1]


def u16_grid(raw: bytes) -> list[int]:
    if len(raw) != GRID * GRID * 2:
        raise ValueError(f"expected {GRID}x{GRID} u16 grid, got {len(raw)} bytes")
    return list(struct.unpack(f"<{GRID * GRID}H", raw))


# ----------------------------------------------------------------------------------------------- SIT (situation)
@dataclass
class Box:
    index: int
    kind: str
    name: str
    model: str
    size: tuple          # ft, full extents x,y,z
    pos: tuple           # ft
    orient: tuple        # radians (pitch, yaw, roll) as stored
    fields: dict = field(default_factory=dict)


@dataclass
class Situation:
    name: str
    race_type: int
    track_length_ft: float
    vehicles: list       # [(pos, orient, trk)]
    boxes: list
    course: list         # [(start, end, width_ft)]
    paths: list          # [[(pos, flags dict)]]
    backdrop: str
    header: dict


_BOX_RE = re.compile(r"\{ (\d+) (\w+)\n(.*?)\n\} \2", re.S)


def parse_sit(raw: bytes) -> Situation:
    text = raw.decode("latin-1").replace("\r", "")
    ls = text.split("\n")
    header = {}
    for i in range(0, min(len(ls), 40) - 1):
        k = ls[i].strip()
        if k and not ls[i + 1].startswith("***"):
            header.setdefault(k.lstrip("!@#$%&"), ls[i + 1].strip())
    name = header.get("Race Track Name", "")
    race_type = int(header.get("Track Race Type", "0") or 0)
    amb = _floats(header.get("ambient sound,track length,weather mask", "0,0,0"))
    track_len = amb[1] if len(amb) > 1 else 0.0

    vehicles = []
    for m in re.finditer(r"Vehicle \d+ of \d+ -+\nstaticName\n(.*?)\nwPos\n(.*?)\nbvel\n.*?\nwOrient\n(.*?)\n", text):
        vehicles.append((tuple(_floats(m[2])), tuple(_floats(m[3])), m[1].strip()))

    boxes = []
    for m in _BOX_RE.finditer(text):
        vals = {}
        for line in m[3].split("\n"):
            if "//" in line:
                v, k = line.split("//", 1)
                vals[k.strip()] = v.strip().strip('"')
        def vec(key, default=(0.0, 0.0, 0.0)):
            try:
                return tuple(_floats(vals[key]))
            except (KeyError, ValueError):
                return default
        boxes.append(Box(int(m[1]), m[2], vals.get("name", ""), vals.get("staticName", ""), vec("size"), vec("wPos"),
                         vec("wOrient"), vals))

    course = []
    cpos = text.find("*** Course ***")
    if cpos >= 0:
        seg_re = re.compile(r"cstart\n(.*?)\ncend\n(.*?)\ncdec_point,cspeed,lastentry\n.*?\n&cSpeedLimit,cTrackWidth\n(.*?)\n")
        for m in seg_re.finditer(text, cpos):
            sl = _floats(m[3])
            course.append((tuple(_floats(m[1])), tuple(_floats(m[2])), sl[1] if len(sl) > 1 else 0.0))

    paths = []
    for m in re.finditer(r"Path \d+ of \d+ -+\n(.*?)(?=\nPath \d+ of|\n\*\*\* Stadium)", text, re.S):
        pts = [tuple(_floats(p)) for p in re.findall(r"Point \d+ of \d+ -+\nwPos\n(.*?)\n", m[1])]
        ai = re.findall(r"AIFlag\n(\d+)", m[1])
        if pts:
            paths.append({"points": pts, "ai": [int(a) for a in ai]})
    bd = re.search(r"backdropModelName\n(.*?)\n", text)
    return Situation(name, race_type, track_len, vehicles, boxes, course, paths, bd[1].strip() if bd else "", header)


# ----------------------------------------------------------------------------------------------- textures
def decode_raw(raw: bytes, act: bytes | None, opa: bytes | None = None) -> tuple[int, int, bytes]:
    n = len(raw)
    side = int(math.isqrt(n))
    if side * side == n:
        w = h = side
    elif n % 256 == 0:
        w, h = 256, n // 256
    else:
        raise ValueError(f"unsupported RAW size {n}")
    from PIL import Image
    pal = act[:768] if act and len(act) >= 768 else bytes(i // 3 for i in range(768))
    im = Image.frombytes("P", (w, h), raw)
    im.putpalette(pal)
    im = im.convert("RGBA")
    if opa and len(opa) == n:
        im.putalpha(Image.frombytes("L", (w, h), opa))
    return w, h, im.tobytes()


def load_texture(pod: Pod, name: str) -> tuple[int, int, bytes] | None:
    """Any Evo texture reference (RAW/TIF, with or without extension) -> RGBA, or None when absent."""
    stem = name.rsplit(".", 1)[0]
    raw_name = pod.find(stem + ".RAW")
    if raw_name:
        act = pod.find(stem + ".ACT")
        opa = pod.find(stem + ".OPA")
        return decode_raw(pod.read(raw_name), pod.read(act) if act else None, pod.read(opa) if opa else None)
    tif = pod.find(stem + ".TIF")
    if tif:
        meta, rgba, _s, _p = decode_classic_tiff(pod.read(tif))
        return meta["width"], meta["height"], rgba
    return None


# ----------------------------------------------------------------------------------------------- one race
@dataclass
class Track:
    pod: Pod
    key: str                 # SIT stem, e.g. DVALLEY
    sit: Situation
    level: Level
    heights_ft: list         # 256*256 floats
    cell_tex: list           # 256*256 texture-list index (ground)
    cell_shadow: list        # 256*256 texture-list index or -1
    tex: list                # TexEntry
    tex_count: int
    shadow_count: int

    def height(self, x_ft: float, z_ft: float) -> float:
        """Bilinear ground height in feet at a world position (wraps like CGround::groundHeight masks)."""
        gx, gz = x_ft / CELL_FT, z_ft / CELL_FT
        i0, j0 = math.floor(gx), math.floor(gz)
        fx, fz = gx - i0, gz - j0
        def h(i, j):
            return self.heights_ft[(j % GRID) * GRID + (i % GRID)]
        a = h(i0, j0) * (1 - fx) + h(i0 + 1, j0) * fx
        b = h(i0, j0 + 1) * (1 - fx) + h(i0 + 1, j0 + 1) * fx
        return a * (1 - fz) + b * fz

    def checkpoints(self):
        return [b for b in self.sit.boxes if b.kind == "CCheckpoint"]


def list_races(pod: Pod) -> list[str]:
    return [n.split("/")[-1].rsplit(".", 1)[0] for n in pod.names("WORLD/", ".SIT")]


def load_track(pod_path: Path, sit_stem: str | None = None) -> Track:
    pod = Pod(pod_path)
    stems = list_races(pod)
    if not stems:
        raise ValueError(f"{pod_path}: no WORLD/*.SIT")
    stem = sit_stem or stems[0]
    sit = parse_sit(pod.read(f"WORLD/{stem}.SIT"))
    lvl_name = sit.header.get("version") and None
    lvl_member = pod.find(stem + ".LVL", ("LEVELS",)) or pod.names("LEVELS/", ".LVL")[0]
    level = parse_lvl(pod.read(lvl_member))
    base = level.heightmap.rsplit(".", 1)[0]
    heights = [v / HEIGHT_DIV for v in u16_grid(pod.read(f"DATA/{base}.RAW"))]
    clr = u16_grid(pod.read(f"DATA/{level.colormap.rsplit('.', 1)[0]}.CLR"))
    tex, tcount, scount = parse_tex(pod.read(f"DATA/{level.texlist.rsplit('.', 1)[0]}.TEX"))
    shadow = [-1] * (GRID * GRID)
    sdw_name = f"DATA/{base}.SDW"
    if pod.has(sdw_name):
        for i, v in enumerate(u16_grid(pod.read(sdw_name))):
            if v not in NO_SHADOW and v < len(tex):
                shadow[i] = v
    cell_tex = [(v & 0xFFF) if (v & 0xFFF) < len(tex) else 0 for v in clr]
    return Track(pod, stem, sit, level, heights, cell_tex, shadow, tex, tcount, scount)
