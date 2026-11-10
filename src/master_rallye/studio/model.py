"""Versioned Course Studio project model and its portable on-disk form.

All positions are **game space** (the RaceTest XML / course DX frame: X, Y up,
Z). The Blender adapter maps game ``(x, y, z)`` to Blender ``(x, -z, y)``.
Triangles keep the authoring (Blender) winding: counter-clockwise seen from
the outward side. Writers apply the Retail cooker's winding per structure.

A project directory holds ``project.json`` (all settings, markers, routes,
materials, provenance; paths relative to the project or the resource root) and
``geometry.bin`` (all mesh arrays). No absolute install path is required: the
resource root is resolved at use time (see :func:`resolve_resource_root`).
"""
from __future__ import annotations

import json
import math
import os
import struct
import sys
import time
import uuid
from array import array
from dataclasses import asdict, dataclass, field
from pathlib import Path
from typing import Iterable, Sequence

from . import SCHEMA
from .materials import ALPHA_MODES, CLAMP_MODES, SHADERS, SURFACES, native_name

Vec3 = tuple[float, float, float]

ROLE_TERRAIN = "terrain"       # drawn + collision BSP + surface database ($bsp/$draw $landdb)
ROLE_COLLISION = "collision"   # collision BSP only, invisible ($bsp/$nodraw)
ROLE_VISUAL = "visual"         # drawn only ($objects)
ROLE_WATER = "water"           # drawn + surface database, never solid ($water $landdb)
ROLE_HIDDEN = "terrain_hidden" # surface database + collision BSP, not drawn (Retail "$landdb fill")
ROLES = (ROLE_TERRAIN, ROLE_COLLISION, ROLE_VISUAL, ROLE_WATER, ROLE_HIDDEN)
LAND_ROLES = (ROLE_TERRAIN, ROLE_HIDDEN)
ROLE_LABELS = {
    ROLE_TERRAIN: "Terrain (drivable, collides)",
    ROLE_COLLISION: "Collision only (invisible)",
    ROLE_VISUAL: "Visual only (no collision)",
    ROLE_WATER: "Water surface",
    ROLE_HIDDEN: "Invisible ground (collides, not drawn)",
}

GEOMETRY_MAGIC = b"MRSG"
GEOMETRY_VERSION = 1


class ProjectError(ValueError):
    pass


@dataclass
class Material:
    key: str
    label: str = ""
    shader: str = "ground"
    surface: str | None = "grass"
    textures: list = field(default_factory=lambda: [None, None, None])   # base, secondary (metal), unused
    noise: bool = True
    alpha: str = "opaque"
    clamp: str = ""
    mip: float = 1.0
    scroll: str | None = None
    native: str | None = None          # exact source name when imported and unchanged
    role_hint: str | None = None       # importer provenance only

    def validate(self) -> list[str]:
        problems = []
        if self.shader not in SHADERS:
            problems.append(f"unknown shader {self.shader}")
        if self.surface is not None and self.surface not in SURFACES:
            problems.append(f"unknown surface {self.surface}")
        if self.alpha not in ALPHA_MODES:
            problems.append(f"unknown alpha mode {self.alpha}")
        if self.clamp not in CLAMP_MODES:
            problems.append(f"unknown clamp {self.clamp}")
        if not (0.0 < self.mip <= 8.0):
            problems.append(f"mip bias {self.mip} outside (0, 8]")
        return problems

    def native_name(self) -> str:
        if self.native:
            return self.native
        return native_name(label=self.label or self.key, shader=self.shader, surface=self.surface,
                           alpha=self.alpha, clamp=self.clamp, mip=self.mip, scroll=self.scroll,
                           noise=self.has_noise())

    def has_noise(self) -> bool:
        return bool(self.noise and self.shader == "ground")

    def texture_slots(self) -> list[str | None]:
        base = self.textures[0] if self.textures else None
        secondary = self.textures[1] if len(self.textures) > 1 else None
        if self.shader == "metal" and secondary is None:
            from .materials import METAL_DEFAULT_SECONDARY
            secondary = METAL_DEFAULT_SECONDARY
        if self.shader != "metal":
            secondary = None
        from .materials import NOISE_TEXTURE
        return [base, secondary, NOISE_TEXTURE if self.has_noise() else None]


@dataclass
class Texture:
    key: str                          # native slot name, e.g. "road-tga" (file <key>.dxt)
    source: str | None = None         # project-relative image (PNG) authored by the user
    native: str | None = None         # resource-root-relative existing FEED texture
    width: int = 0
    height: int = 0
    has_alpha: bool = False


@dataclass
class Mesh:
    id: str
    name: str
    role: str
    positions: list = field(default_factory=list)       # flat x,y,z game space
    triangles: list = field(default_factory=list)       # flat i0,i1,i2 (authoring winding)
    materials: list = field(default_factory=list)       # material keys used by this mesh
    tri_material: list = field(default_factory=list)    # per triangle index into ``materials``
    uv: list | None = None                              # per corner u,v (6 floats per triangle)
    normals: list | None = None                         # per corner game-space normal (9 floats per triangle)
    colors: list | None = None                          # per corner RGBA bytes (12 per triangle)
    source: str = ""                                     # provenance: "authored", "imported:<path>", ...
    group: str = ""                                      # optional user group (terrain section, object kind)

    @property
    def vertex_count(self) -> int:
        return len(self.positions) // 3

    @property
    def triangle_count(self) -> int:
        return len(self.triangles) // 3

    def vertex(self, index: int) -> Vec3:
        return (self.positions[3 * index], self.positions[3 * index + 1], self.positions[3 * index + 2])

    def triangle(self, index: int) -> tuple[int, int, int]:
        return (self.triangles[3 * index], self.triangles[3 * index + 1], self.triangles[3 * index + 2])

    def triangle_points(self, index: int) -> tuple[Vec3, Vec3, Vec3]:
        a, b, c = self.triangle(index)
        return self.vertex(a), self.vertex(b), self.vertex(c)

    def material_of(self, index: int) -> str:
        return self.materials[self.tri_material[index]] if self.materials else ""

    def bounds(self) -> tuple[Vec3, Vec3] | None:
        if not self.positions:
            return None
        xs, ys, zs = self.positions[0::3], self.positions[1::3], self.positions[2::3]
        return (min(xs), min(ys), min(zs)), (max(xs), max(ys), max(zs))

    def validate_arrays(self) -> list[str]:
        problems = []
        n, t = self.vertex_count, self.triangle_count
        if len(self.positions) % 3:
            problems.append("position array is not a multiple of 3")
        if len(self.triangles) % 3:
            problems.append("triangle array is not a multiple of 3")
        if any(i < 0 or i >= n for i in self.triangles):
            problems.append("triangle index out of range")
        if len(self.tri_material) != t:
            problems.append(f"{len(self.tri_material)} material assignments for {t} triangles")
        elif self.tri_material and (min(self.tri_material) < 0 or max(self.tri_material) >= len(self.materials)):
            problems.append("material slot index out of range")
        if self.uv is not None and len(self.uv) != 6 * t:
            problems.append("UV array does not match the triangle count")
        if self.normals is not None and len(self.normals) != 9 * t:
            problems.append("normal array does not match the triangle count")
        if self.colors is not None and len(self.colors) != 12 * t:
            problems.append("colour array does not match the triangle count")
        if any(not math.isfinite(v) for v in self.positions):
            problems.append("non-finite vertex position")
        return problems


@dataclass
class Area:
    """StartArea / FinishArea: a native four-marker quad around ``center``."""
    center: Vec3 = (0.0, 0.0, 0.0)
    heading: float = 0.0          # degrees; 0 = +Z, 90 = +X (direction of travel)
    width: float = 24.0           # across the road
    depth: float = 12.0           # along the road
    corners: list | None = None   # explicit four corners when imported/edited freely

    def quad(self) -> list[Vec3]:
        if self.corners:
            return [tuple(c) for c in self.corners]
        h = math.radians(self.heading)
        fx, fz = math.sin(h), math.cos(h)
        rx, rz = fz, -fx
        hw, hd = self.width / 2, self.depth / 2
        cx, cy, cz = self.center
        out = []
        for sf, sr in ((-1, -1), (-1, 1), (1, 1), (1, -1)):
            out.append((cx + sf * hd * fx + sr * hw * rx, cy, cz + sf * hd * fz + sr * hw * rz))
        return out


@dataclass
class Checkpoint:
    """Native timed checkpoint: a gaRaceSplitTimeAI trigger sphere plus four boards."""
    uid: str
    center: Vec3 = (0.0, 0.0, 0.0)
    radius: float = 21.0
    extra_time: float = 60.0      # seconds added to the countdown when the gate is passed
    heading: float = 0.0          # direction of travel through the gate (degrees)
    boards: bool = True           # the four native misc\checkpoints\checkpoint boards
    board_spacing: float = 26.0   # distance between the two board pairs across the road
    name: str = ""


@dataclass
class PaceNote:
    uid: str
    position: Vec3 = (0.0, 0.0, 0.0)
    heading: float = 0.0
    note_id: int = 0              # Pace Note ID (Graphics to Display)
    distance: float = 20.0


@dataclass
class SoundAnchor:
    uid: str
    position: Vec3 = (0.0, 0.0, 0.0)
    template: str = ""            # Retail egg name the sound component is copied from (e.g. "river1")
    name: str = ""


@dataclass
class Route:
    """AI RaceLine. Points are game space, in driving order."""
    points: list = field(default_factory=list)
    spacing: float = 20.0         # native marker spacing used on export


@dataclass
class Limits:
    """gaLimitsAI reset lines. ``mode``: auto (from route), manual (four lists) or wide (open terrain)."""
    mode: str = "auto"
    inner: float = 9.0
    outer: float = 18.0
    lists: dict = field(default_factory=dict)   # LeftInnerLimit/LeftOuterLimit/RightInnerLimit/RightOuterLimit


@dataclass
class Environment:
    template: str = "France1"            # Retail scene providing sky, sound, physics, cameras, HUD
    time_to_first_checkpoint: float = 90.0
    percentage_time_change: float = 100.0
    replay_cameras: list = field(default_factory=list)
    keep_template_sounds: bool = False
    vertex_light: Vec3 = (0.35, 0.85, 0.40)   # baked lighting when a mesh has no colours (sun direction)


@dataclass
class BuildSettings:
    course_key: str = ""          # folder/file stem of the new course (ASCII, no spaces)
    title: str = ""               # menu caption
    output: str = "build"         # project-relative build directory
    catalog: str = ""             # accepted CAP2 courses.json (resource-root or absolute)
    menu_group: int = 0
    menu_position: int = -1       # -1: append after the group's entries
    modes: list = field(default_factory=lambda: ["QuickRace"])
    collision_skirt: bool = True  # close the open map edge for the solid-leaf collision tree
    pacenotes: str = "auto"       # auto | manual | none
    route_registry_id: int | None = None


@dataclass
class Provenance:
    kind: str = "new"             # new | retail | imported
    race: str = ""                # Retail scene stem when derived from a Retail course
    scene: str = ""               # resource-root-relative RaceTest
    model: str = ""               # resource-root-relative DX
    hashes: dict = field(default_factory=dict)
    notes: list = field(default_factory=list)


@dataclass
class CourseProject:
    name: str
    uid: str = field(default_factory=lambda: uuid.uuid4().hex)
    schema: str = SCHEMA
    created: float = field(default_factory=time.time)
    modified: float = field(default_factory=time.time)
    materials: dict = field(default_factory=dict)        # key -> Material
    textures: dict = field(default_factory=dict)         # key -> Texture
    meshes: list = field(default_factory=list)           # Mesh
    start: Area = field(default_factory=Area)
    finish: Area = field(default_factory=Area)
    checkpoints: list = field(default_factory=list)      # Checkpoint, in driving order
    route: Route = field(default_factory=Route)
    limits: Limits = field(default_factory=Limits)
    pacenotes: list = field(default_factory=list)
    sounds: list = field(default_factory=list)
    environment: Environment = field(default_factory=Environment)
    build: BuildSettings = field(default_factory=BuildSettings)
    provenance: Provenance = field(default_factory=Provenance)
    history: list = field(default_factory=list)          # audit of builder operations
    extras: dict = field(default_factory=dict)           # optional module data (PS2 assets, ...)
    blobs: dict = field(default_factory=dict)            # name -> bytes, saved as blob-<name>.bin next to project.json

    # ---------------------------------------------------------------- queries
    def mesh(self, mesh_id: str) -> Mesh:
        for item in self.meshes:
            if item.id == mesh_id:
                return item
        raise ProjectError(f"no mesh {mesh_id}")

    def meshes_with(self, *roles: str) -> list[Mesh]:
        return [m for m in self.meshes if m.role in roles]

    def course_key(self) -> str:
        return self.build.course_key or safe_key(self.name)

    def log(self, action: str, **details) -> None:
        self.history.append({"time": round(time.time(), 3), "action": action, **details})
        self.modified = time.time()

    def ensure_material(self, key: str, **values) -> Material:
        if key not in self.materials:
            self.materials[key] = Material(key=key, **values)
        return self.materials[key]


def safe_key(text: str) -> str:
    out = "".join(c if (c.isascii() and c.isalnum()) else "_" for c in text).strip("_")
    if not out:
        out = "Course"
    if out[0].isdigit():
        out = "C" + out
    return out[:24]


def new_uid(prefix: str = "") -> str:
    return prefix + uuid.uuid4().hex[:12]


# ---------------------------------------------------------------------- serialisation
_MESH_ARRAYS = (("positions", "f"), ("triangles", "I"), ("tri_material", "H"),
                ("uv", "f"), ("normals", "f"), ("colors", "B"))


def _encode_geometry(meshes: Sequence[Mesh]) -> tuple[bytes, list[dict]]:
    blob = bytearray(GEOMETRY_MAGIC + struct.pack("<II", GEOMETRY_VERSION, len(meshes)))
    index = []
    for mesh in meshes:
        entry = {}
        for name, code in _MESH_ARRAYS:
            values = getattr(mesh, name)
            if values is None:
                entry[name] = None
                continue
            data = array(code, values)
            if data.itemsize > 1 and sys.byteorder != "little":
                data.byteswap()
            while len(blob) % 4:
                blob.append(0)
            entry[name] = [len(blob), len(data)]
            blob.extend(data.tobytes())
        index.append(entry)
    return bytes(blob), index


def _decode_array(blob: bytes, spec, code: str):
    if spec is None:
        return None
    offset, count = spec
    data = array(code)
    size = data.itemsize * count
    if offset < 12 or offset + size > len(blob):
        raise ProjectError("geometry.bin is truncated or does not match project.json")
    data.frombytes(blob[offset:offset + size])
    if data.itemsize > 1 and sys.byteorder != "little":
        data.byteswap()
    return list(data)


def project_to_dict(project: CourseProject, geometry_index: list[dict] | None = None) -> dict:
    data = {
        "schema": project.schema, "uid": project.uid, "name": project.name,
        "created": project.created, "modified": project.modified,
        "materials": {k: asdict(v) for k, v in project.materials.items()},
        "textures": {k: asdict(v) for k, v in project.textures.items()},
        "meshes": [],
        "start": asdict(project.start), "finish": asdict(project.finish),
        "checkpoints": [asdict(c) for c in project.checkpoints],
        "route": asdict(project.route), "limits": asdict(project.limits),
        "pacenotes": [asdict(p) for p in project.pacenotes],
        "sounds": [asdict(s) for s in project.sounds],
        "environment": asdict(project.environment), "build": asdict(project.build),
        "provenance": asdict(project.provenance), "history": project.history[-2000:],
        "extras": project.extras, "blobs": sorted(project.blobs),
    }
    for i, mesh in enumerate(project.meshes):
        row = {"id": mesh.id, "name": mesh.name, "role": mesh.role, "materials": mesh.materials,
               "source": mesh.source, "group": mesh.group,
               "vertex_count": mesh.vertex_count, "triangle_count": mesh.triangle_count}
        if geometry_index is not None:
            row["arrays"] = geometry_index[i]
        data["meshes"].append(row)
    return data


def _tuple3(value) -> Vec3:
    return (float(value[0]), float(value[1]), float(value[2]))


def project_from_dict(data: dict, blob: bytes | None) -> CourseProject:
    schema = data.get("schema")
    if schema != SCHEMA:
        raise ProjectError(f"unsupported project schema {schema!r}; expected {SCHEMA}")
    project = CourseProject(name=data["name"], uid=data["uid"], created=data.get("created", 0.0),
                            modified=data.get("modified", 0.0))
    project.materials = {k: Material(**v) for k, v in data.get("materials", {}).items()}
    project.textures = {k: Texture(**v) for k, v in data.get("textures", {}).items()}
    if blob is not None and data.get("meshes"):
        if blob[:4] != GEOMETRY_MAGIC:
            raise ProjectError("geometry.bin has a wrong signature")
        version, count = struct.unpack_from("<II", blob, 4)
        if version != GEOMETRY_VERSION or count != len(data["meshes"]):
            raise ProjectError("geometry.bin version/mesh count mismatch")
    for row in data.get("meshes", []):
        mesh = Mesh(id=row["id"], name=row["name"], role=row["role"], materials=list(row["materials"]),
                    source=row.get("source", ""), group=row.get("group", ""))
        arrays = row.get("arrays")
        if arrays is not None and blob is not None:
            for name, code in _MESH_ARRAYS:
                setattr(mesh, name, _decode_array(blob, arrays.get(name), code))
            for name in ("positions", "triangles", "tri_material"):
                if getattr(mesh, name) is None:
                    setattr(mesh, name, [])
        project.meshes.append(mesh)
    s, f = data["start"], data["finish"]
    project.start = Area(center=_tuple3(s["center"]), heading=s["heading"], width=s["width"], depth=s["depth"],
                         corners=s.get("corners"))
    project.finish = Area(center=_tuple3(f["center"]), heading=f["heading"], width=f["width"], depth=f["depth"],
                          corners=f.get("corners"))
    project.checkpoints = [Checkpoint(**{**c, "center": _tuple3(c["center"])}) for c in data.get("checkpoints", [])]
    project.route = Route(**data.get("route", {}))
    project.limits = Limits(**data.get("limits", {}))
    project.pacenotes = [PaceNote(**{**p, "position": _tuple3(p["position"])}) for p in data.get("pacenotes", [])]
    project.sounds = [SoundAnchor(**{**s, "position": _tuple3(s["position"])}) for s in data.get("sounds", [])]
    env = dict(data.get("environment", {}))
    if "vertex_light" in env:
        env["vertex_light"] = _tuple3(env["vertex_light"])
    project.environment = Environment(**env)
    project.build = BuildSettings(**data.get("build", {}))
    project.provenance = Provenance(**data.get("provenance", {}))
    project.history = list(data.get("history", []))
    project.extras = dict(data.get("extras", {}))
    return project


def save_project(project: CourseProject, directory: Path) -> Path:
    """Write ``project.json`` + ``geometry.bin`` atomically into ``directory``."""
    directory = Path(directory)
    directory.mkdir(parents=True, exist_ok=True)
    for mesh in project.meshes:
        problems = mesh.validate_arrays()
        if problems:
            raise ProjectError(f"mesh {mesh.name}: {'; '.join(problems)}")
    project.modified = time.time()
    blob, index = _encode_geometry(project.meshes)
    data = project_to_dict(project, index)
    tmp_geo = directory / "geometry.bin.tmp"
    tmp_json = directory / "project.json.tmp"
    tmp_geo.write_bytes(blob)
    tmp_json.write_text(json.dumps(data, indent=1, sort_keys=False), encoding="utf-8")
    for name, data in project.blobs.items():
        tmp = directory / f"blob-{name}.bin.tmp"
        tmp.write_bytes(data)
        os.replace(tmp, directory / f"blob-{name}.bin")
    os.replace(tmp_geo, directory / "geometry.bin")
    os.replace(tmp_json, directory / "project.json")
    return directory / "project.json"


def load_project(path: Path) -> CourseProject:
    path = Path(path)
    if path.is_dir():
        path = path / "project.json"
    data = json.loads(path.read_text(encoding="utf-8"))
    geo = path.with_name("geometry.bin")
    blob = geo.read_bytes() if geo.exists() else None
    if data.get("meshes") and blob is None:
        raise ProjectError(f"{geo} is missing")
    project = project_from_dict(data, blob)
    for name in data.get("blobs", []):
        file = path.with_name(f"blob-{name}.bin")
        if not file.exists():
            raise ProjectError(f"{file} is missing")
        project.blobs[name] = file.read_bytes()
    return project


# ---------------------------------------------------------------------- resource root
def is_resource_root(path: Path) -> bool:
    path = Path(path)
    return (path / "DataScene").is_dir() and (path / "DataGx").is_dir()


def resolve_resource_root(hint: str | Path | None = None, *, extra: Iterable[Path] = ()) -> Path | None:
    """First directory holding DataGx + DataScene: hint, $MR_RESOURCE_ROOT, then ``extra`` candidates.

    A Retail install keeps courses in ``Data.sma``; an unpacked copy
    (``Data.sma_unpacked``) next to it is preferred because it is a plain tree.
    """
    candidates: list[Path] = []
    for value in (hint, os.environ.get("MR_RESOURCE_ROOT")):
        if value:
            candidates.append(Path(value))
    candidates.extend(Path(p) for p in extra)
    for candidate in candidates:
        for probe in (candidate / "Data.sma_unpacked", candidate):
            if is_resource_root(probe) and (probe / "DataScene" / "RaceTest").is_dir():
                if any((probe / "DataScene" / "RaceTest").glob("*.xml")):
                    return probe.resolve()
    return None
