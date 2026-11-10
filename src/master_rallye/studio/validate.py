"""Project validator: errors block a build, warnings and advice do not.

Every finding carries a category, a stable reference (mesh id + triangle,
checkpoint uid, route point, material key, texture key) and, when it has one,
a game-space position, so the Blender UI can select the object and frame it.
"""
from __future__ import annotations

import math
from dataclasses import asdict, dataclass, field
from pathlib import Path

from .ai import route_issues
from .dx_build import DEGENERATE_AREA, MAX_LOCAL_VERTICES, triangle_area
from .materials import SURFACE_TABLE
from .model import ROLE_COLLISION, ROLE_TERRAIN, ROLE_VISUAL, ROLE_WATER, CourseProject

ERROR, WARNING, INFO = "error", "warning", "info"
# Retail limits observed by earlier course work (docs/course-new-entries.md)
TEXTURE_BUDGET = 250          # ~256 textures per scene crash threshold measured in E1
LAND_RECORD_BUDGET = 400_000  # bounded by the Retail parser limits; Retail courses use <= 45 k
DX_SIZE_BUDGET = 96 << 20     # model cache raised to 384 MB by the Invitation tool; Retail courses <= 24 MB


@dataclass
class Finding:
    severity: str
    category: str          # geometry | collision | gameplay | resources | materials
    message: str
    ref: dict = field(default_factory=dict)
    position: tuple | None = None
    hint: str = ""

    def to_dict(self):
        return asdict(self)


def validate_project(project: CourseProject, *, resource_root: Path | None = None, project_dir: Path | None = None,
                     collision_report=None) -> list[Finding]:
    out: list[Finding] = []
    add = out.append

    # ------------------------------------------------------------ geometry
    terrain = project.meshes_with(ROLE_TERRAIN)
    if not terrain:
        add(Finding(ERROR, "geometry", "the course has no terrain mesh", hint="Terrain > Add Terrain, or set a mesh role to Terrain"))
    drawn = project.meshes_with(ROLE_TERRAIN, ROLE_VISUAL, ROLE_WATER)
    total_tris = 0
    for mesh in project.meshes:
        for problem in mesh.validate_arrays():
            add(Finding(ERROR, "geometry", f"{mesh.name}: {problem}", {"mesh": mesh.id}))
        degenerate = 0
        for t in range(mesh.triangle_count):
            pts = mesh.triangle_points(t)
            if triangle_area(*pts) < DEGENERATE_AREA:
                degenerate += 1
                if degenerate <= 3:
                    add(Finding(WARNING, "geometry", f"{mesh.name}: zero-area triangle (dropped on export)",
                                {"mesh": mesh.id, "triangle": t}, pts[0]))
        if degenerate > 3:
            add(Finding(WARNING, "geometry", f"{mesh.name}: {degenerate} zero-area triangles in total", {"mesh": mesh.id}))
        if mesh.role in (ROLE_TERRAIN, ROLE_VISUAL, ROLE_WATER) and mesh.uv is None:
            add(Finding(WARNING, "geometry", f"{mesh.name}: no UV map; textures will be a single texel",
                        {"mesh": mesh.id}, hint="UV Editing: unwrap the mesh"))
        if mesh.role in (ROLE_TERRAIN, ROLE_VISUAL, ROLE_WATER) and mesh.uv is not None:
            if any(not math.isfinite(v) or abs(v) > 4096 for v in mesh.uv):
                add(Finding(ERROR, "geometry", f"{mesh.name}: UV values are not finite or exceed 4096",
                            {"mesh": mesh.id}))
        b = mesh.bounds()
        if b and any(abs(v) > 60000 for v in b[0] + b[1]):
            add(Finding(ERROR, "geometry", f"{mesh.name}: coordinates exceed +/-60 km", {"mesh": mesh.id}))
        if mesh.role in (ROLE_TERRAIN, ROLE_WATER) and mesh.triangle_count:
            down = 0
            for t in range(mesh.triangle_count):
                a, bb, c = mesh.triangle_points(t)
                n = ((bb[1] - a[1]) * (c[2] - a[2]) - (bb[2] - a[2]) * (c[1] - a[1]),
                     (bb[2] - a[2]) * (c[0] - a[0]) - (bb[0] - a[0]) * (c[2] - a[2]),
                     (bb[0] - a[0]) * (c[1] - a[1]) - (bb[1] - a[1]) * (c[0] - a[0]))
                length = math.sqrt(sum(v * v for v in n)) or 1.0
                if n[1] / length < -0.3:
                    down += 1
            if down > 0.4 * mesh.triangle_count:
                add(Finding(ERROR, "geometry", f"{mesh.name}: {down} of {mesh.triangle_count} faces point down "
                            "(inverted normals make the ground a ceiling)", {"mesh": mesh.id},
                            hint="Edit Mode > Mesh > Normals > Recalculate Outside"))
            elif down:
                add(Finding(INFO, "geometry", f"{mesh.name}: {down} downward faces (overhangs or flipped faces)",
                            {"mesh": mesh.id}))
        total_tris += mesh.triangle_count
    used_materials = {m.material_of(t) for m in drawn for t in range(m.triangle_count)}
    for key in sorted(used_materials):
        if key not in project.materials:
            add(Finding(ERROR, "materials", f"material {key!r} is used but not defined", {"material": key}))
    # per-material local vertex chunks are split automatically; report very large ones
    if total_tris > 1_500_000:
        add(Finding(WARNING, "geometry", f"{total_tris} triangles: expect long builds and high memory use"))

    # ------------------------------------------------------------ materials and surfaces
    for key, mat in project.materials.items():
        for problem in mat.validate():
            add(Finding(ERROR, "materials", f"{key}: {problem}", {"material": key}))
    for mesh in project.meshes_with(ROLE_TERRAIN):
        for slot in mesh.materials:
            mat = project.materials.get(slot)
            if mat is not None and mat.surface is None:
                add(Finding(WARNING, "materials", f"terrain material {slot} has no surface type "
                            "(physics falls back to 'No surface')", {"material": slot, "mesh": mesh.id},
                            hint="Materials: choose a surface type"))
            if mat is not None and mat.surface == "water":
                add(Finding(WARNING, "materials", f"terrain material {slot} is water: water is not solid "
                            "(Surface.xml Solid=False); use the Water role for water", {"material": slot}))
    for mesh in project.meshes_with(ROLE_WATER):
        for slot in mesh.materials:
            mat = project.materials.get(slot)
            if mat is not None and mat.surface != "water":
                add(Finding(WARNING, "materials", f"water mesh {mesh.name} uses {slot} without $surfacetype(water)",
                            {"material": slot, "mesh": mesh.id}))

    # ------------------------------------------------------------ resources
    textures = set()
    for key in used_materials:
        mat = project.materials.get(key)
        if mat:
            textures.update(t for t in mat.texture_slots() if t)
    if len(textures) > TEXTURE_BUDGET:
        add(Finding(ERROR, "resources", f"{len(textures)} textures; Retail scenes crash above about 256",
                    hint="reuse textures or merge materials"))
    for tk in sorted(textures):
        tex = project.textures.get(tk)
        if tk in ("noise-tga", "aluminium-tga") and (tex is None or not (tex.source or tex.native)):
            continue            # shared Retail detail/environment layers: resolved from the resources or generated
        if tex is None:
            add(Finding(ERROR, "resources", f"texture {tk} is not registered", {"texture": tk}))
            continue
        if tex.source:
            path = (project_dir / tex.source) if project_dir and not Path(tex.source).is_absolute() else Path(tex.source)
            if not path.exists():
                add(Finding(ERROR, "resources", f"texture image {tex.source} is missing", {"texture": tk},
                            hint="Materials > Relink Textures"))
        elif tex.native:
            if resource_root is None:
                add(Finding(WARNING, "resources", f"texture {tk} comes from the resource root, which is not set",
                            {"texture": tk}))
            elif not _ci_exists(resource_root, tex.native):
                add(Finding(ERROR, "resources", f"native texture {tex.native} not found under the resource root",
                            {"texture": tk}))
        else:
            add(Finding(ERROR, "resources", f"texture {tk} has no image", {"texture": tk}))
        if not tk.isascii() or any(c in tk for c in '\\/:*?"<>|[]'):
            add(Finding(ERROR, "resources", f"texture name {tk!r} has characters the HNT/DX string table cannot hold",
                        {"texture": tk}))
    key = project.course_key()
    if not key.isascii() or not key.replace("_", "").isalnum():
        add(Finding(ERROR, "resources", f"course key {key!r} must be ASCII letters/digits/underscore"))
    if resource_root is not None:
        tmpl = resource_root / "DataScene" / "RaceTest" / f"{project.environment.template}.xml"
        if not _ci_exists(resource_root, f"DataScene/RaceTest/{project.environment.template}.xml"):
            add(Finding(ERROR, "resources", f"environment template {tmpl.name} not found in the resource root"))
        for retail in ("DataGx/Course", "DataScene/RaceTest"):
            if _ci_exists(resource_root, f"{retail}/{key}") or _ci_exists(resource_root, f"{retail}/{key}.xml"):
                add(Finding(ERROR, "resources", f"course key {key} collides with an existing {retail} entry",
                            hint="Build: choose another course name"))

    # ------------------------------------------------------------ gameplay
    if len(project.route.points) < 2:
        add(Finding(ERROR, "gameplay", "no AI route", hint="Routes & AI > Draw AI Route"))
    else:
        heights = None
        if terrain:
            from .collision import HeightField, terrain_triangles
            hf = HeightField(terrain_triangles(project))
            heights = lambda x, z: hf.ground(x, z)
        for issue in route_issues(project, heights):
            add(Finding(issue.severity, "gameplay", issue.message, {"route_point": issue.index}, issue.position))
    for area, name in ((project.start, "start"), (project.finish, "finish")):
        if area.width <= 2 or area.depth <= 1:
            add(Finding(ERROR, "gameplay", f"{name} area is too small", {"area": name}, area.center))
    if math.dist(project.start.center, project.finish.center) < 50 and project.start.center != (0.0, 0.0, 0.0):
        add(Finding(WARNING, "gameplay", "start and finish are closer than 50 m (closed loops need a long route)",
                    {"area": "finish"}, project.finish.center))
    if not project.checkpoints:
        add(Finding(INFO, "gameplay", "no checkpoints: the race uses only the first-gate timer",
                    hint="Markers > Add Checkpoint or Place Checkpoints Along Route"))
    for i, cp in enumerate(project.checkpoints):
        if cp.radius < 4 or cp.radius > 80:
            add(Finding(WARNING, "gameplay", f"checkpoint {i + 1} radius {cp.radius:.0f} m is unusual (Retail 15-30)",
                        {"checkpoint": cp.uid}, cp.center))
        if cp.extra_time < 0:
            add(Finding(ERROR, "gameplay", f"checkpoint {i + 1} has negative extra time", {"checkpoint": cp.uid}, cp.center))
    if project.environment.time_to_first_checkpoint <= 5:
        add(Finding(ERROR, "gameplay", "time to the first checkpoint must be more than 5 s"))

    # ------------------------------------------------------------ collision probes
    if collision_report is not None:
        if collision_report.route_holes:
            add(Finding(ERROR, "collision", f"{collision_report.route_holes} terrain samples next to the AI route have "
                        "empty space under the surface (cars fall through)", {"collision": "holes"}))
        if collision_report.holes > collision_report.route_holes:
            add(Finding(WARNING, "collision", f"{collision_report.holes - collision_report.route_holes} terrain samples "
                        "away from the route have empty space under the surface", {"collision": "holes"}))
        if collision_report.route_blocked:
            add(Finding(ERROR, "collision", f"{collision_report.route_blocked} AI route samples hit solid collision",
                        {"collision": "route"}))
        if collision_report.phantoms:
            add(Finding(WARNING, "collision", f"{collision_report.phantoms} terrain samples have solid space "
                        "just above the surface", {"collision": "phantoms"}))
        for issue in collision_report.issues[:2000]:
            add(Finding(ERROR if issue.severity == "error" else WARNING, "collision", issue.detail,
                        {"collision": issue.kind}, issue.position))
    return out


def _ci_exists(root: Path, relative: str) -> bool:
    cur = Path(root)
    for part in Path(relative).parts:
        if not cur.is_dir():
            return False
        match = next((p for p in cur.iterdir() if p.name.lower() == part.lower()), None)
        if match is None:
            return False
        cur = match
    return True


def ci_path(root: Path, relative: str) -> Path | None:
    cur = Path(root)
    for part in Path(relative.replace("\\", "/")).parts:
        if not cur.is_dir():
            return None
        match = next((p for p in cur.iterdir() if p.name.lower() == part.lower()), None)
        if match is None:
            return None
        cur = match
    return cur


def summary(findings) -> dict:
    return {"errors": sum(f.severity == ERROR for f in findings), "warnings": sum(f.severity == WARNING for f in findings),
            "info": sum(f.severity == INFO for f in findings)}
