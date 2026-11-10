"""Starting points for a course created from scratch (no Retail geometry required).

:func:`new_project` creates an empty, valid-to-edit project with the default
materials. :func:`valley_course` additionally generates a small landscape:
a rolling height field with a road carved along a closed-form curve, road and
verge materials assigned per face, one building with its collision proxy,
the AI route, start/finish areas and checkpoints. It is the "Valley" preset of
the New Course wizard and the example project.
"""
from __future__ import annotations

import math

from .ai import place_along
from .collision import box_proxy
from .materials import PRESETS
from .model import (ROLE_COLLISION, ROLE_TERRAIN, ROLE_VISUAL, Area, Checkpoint, CourseProject, Material, Mesh,
                    Texture, new_uid, safe_key)

# Retail textures used when a resource root is available (copied into the new course folder on build).
RETAIL_TEXTURES = {
    "road": ("road-tga", "DataGx/Course/France1/road-tga.dxt"),
    "grass": ("grass-tga", "DataGx/Course/France1/grass-tga.dxt"),
    "verge": ("grass_left-tga", "DataGx/Course/France1/grass_left-tga.dxt"),
    "rock": ("rock-tga", "DataGx/Course/France1/rock-tga.dxt"),
    "wall": ("wall-tga", "DataGx/Course/France1/wall-tga.dxt"),
}


def default_materials(project: CourseProject, *, retail: bool = True) -> None:
    def tex(role):
        key, native = RETAIL_TEXTURES[role]
        if key not in project.textures:
            project.textures[key] = Texture(key=key, native=native if retail else None)
        return key
    project.materials.setdefault("road", Material("road", "Road", **PRESETS["Tarmac road"], textures=[tex("road"), None, None]))
    project.materials.setdefault("grass", Material("grass", "Grass", **PRESETS["Grass"], textures=[tex("grass"), None, None]))
    project.materials.setdefault("verge", Material("verge", "Verge", **PRESETS["Gravel road"], textures=[tex("verge"), None, None]))
    project.materials.setdefault("rock", Material("rock", "Rock", **PRESETS["Rock face"], textures=[tex("rock"), None, None]))
    project.materials.setdefault("building", Material("building", "Building", **PRESETS["Building / object"],
                                                      textures=[tex("wall"), None, None]))
    project.materials.setdefault("collision", Material("collision", "Collision", shader="object", surface="rock",
                                                       noise=False, textures=[None, None, None]))


def new_project(name: str, *, title: str = "", template: str = "France1", retail_textures: bool = True) -> CourseProject:
    project = CourseProject(name=name)
    project.build.course_key = safe_key(name)
    project.build.title = title or name
    project.environment.template = template
    default_materials(project, retail=retail_textures)
    project.log("new_project", name=name, template=template)
    return project


def _road_curve(t: float, size: float):
    """Closed-form S-curve across the square, t in [0, 1]."""
    x = -0.42 * size + 0.84 * size * t
    z = 0.28 * size * math.sin(2.2 * math.pi * t) * (0.6 + 0.4 * t)
    return x, z


def valley_course(name: str = "StudioValley", *, size: float = 700.0, cell: float = 6.0, road_width: float = 9.0,
                  seed: int = 7, retail_textures: bool = True, title: str = "Studio Valley") -> CourseProject:
    project = new_project(name, title=title, retail_textures=retail_textures)
    samples = [_road_curve(i / 400, size) for i in range(401)]

    def road_distance(x, z):
        best = 1e9
        for i in range(0, len(samples) - 1, 2):
            ax, az = samples[i]
            bx, bz = samples[min(i + 2, len(samples) - 1)]
            dx, dz = bx - ax, bz - az
            length2 = dx * dx + dz * dz or 1.0
            t = max(0.0, min(1.0, ((x - ax) * dx + (z - az) * dz) / length2))
            px, pz = ax + dx * t, az + dz * t
            best = min(best, (x - px) ** 2 + (z - pz) ** 2)
        return math.sqrt(best)

    def base_height(x, z):
        return (14.0 * math.sin(x / 97.0 + seed) * math.cos(z / 83.0) + 6.0 * math.sin(x / 31.0 + z / 47.0)
                + 0.00004 * (x * x + z * z) * 9.0)

    def road_height(x, z):
        # the road follows a smoothed profile of the terrain along the curve
        return 0.55 * base_height(x, z)

    n = int(size // cell)
    half = size / 2
    terrain = Mesh(id=new_uid("mesh_"), name="Terrain", role=ROLE_TERRAIN, materials=["grass", "verge", "road", "rock"],
                   source="template:valley", group="Terrain")
    heights = {}
    dist = {}
    for j in range(n + 1):
        for i in range(n + 1):
            x, z = -half + i * cell, -half + j * cell
            d = road_distance(x, z)
            h = base_height(x, z)
            blend = max(0.0, min(1.0, (d - road_width * 0.8) / (road_width * 3.0)))
            y = road_height(x, z) * (1 - blend) + h * blend
            heights[(i, j)] = y
            dist[(i, j)] = d
            terrain.positions.extend((x, y, z))
    terrain.uv = []
    def vid(i, j):
        return j * (n + 1) + i
    for j in range(n):
        for i in range(n):
            quad = ((i, j), (i + 1, j), (i + 1, j + 1), (i, j + 1))
            dmin = min(dist[q] for q in quad)
            slope = max(heights[q] for q in quad) - min(heights[q] for q in quad)
            mat = 2 if dmin < road_width / 2 else 1 if dmin < road_width else 3 if slope > cell * 0.9 else 0
            # Blender winding (CCW from above): game (x, z) -> Blender (x, -z), so wind (i,j),(i,j+1),(i+1,j+1)
            for tri in ((quad[0], quad[3], quad[2]), (quad[0], quad[2], quad[1])):
                terrain.triangles.extend(vid(*q) for q in tri)
                terrain.tri_material.append(mat)
                for q in tri:
                    x, z = -half + q[0] * cell, -half + q[1] * cell
                    terrain.uv.extend((x / 12.0, z / 12.0))
    project.meshes.append(terrain)

    # AI route along the road, slightly above the surface
    route = []
    for i in range(0, len(samples), 4):
        x, z = samples[i]
        route.append((x, road_height(x, z) + 0.3, z))
    project.route.points = route
    project.route.spacing = 20.0

    def heading(a, b):
        return math.degrees(math.atan2(b[0] - a[0], b[2] - a[2]))
    project.start = Area(center=route[2], heading=heading(route[2], route[3]), width=22.0, depth=10.0)
    project.finish = Area(center=route[-3], heading=heading(route[-4], route[-3]), width=22.0, depth=12.0)
    for k, (p, h) in enumerate(place_along(route, 3, start_fraction=0.2, end_fraction=0.85)):
        project.checkpoints.append(Checkpoint(uid=new_uid("cp_"), center=p, radius=20.0, extra_time=45.0, heading=h,
                                              name=f"Checkpoint {k + 1}"))
    project.environment.time_to_first_checkpoint = 60.0

    # one building beside the road with its own collision proxy
    bx, bz = _road_curve(0.5, size)
    bx += 28.0
    by = base_height(bx, bz) - 1.0
    lo, hi = (bx - 6.0, by, bz - 4.0), (bx + 6.0, by + 7.0, bz + 4.0)
    tris = box_proxy(lo, hi)
    building = Mesh(id=new_uid("mesh_"), name="Farm house", role=ROLE_VISUAL, materials=["building"],
                    source="template:valley", group="Objects")
    building.uv = []
    for tri in tris:
        for p in tri:
            building.triangles.append(len(building.positions) // 3)
            building.positions.extend(p)
            building.uv.extend(((p[0] + p[2]) / 6.0, p[1] / 6.0))
        building.tri_material.append(0)
    project.meshes.append(building)
    proxy = Mesh(id=new_uid("mesh_"), name="Farm house collision", role=ROLE_COLLISION, materials=["collision"],
                 source="template:valley", group="Objects")
    for tri in box_proxy((lo[0], lo[1] - 2.0, lo[2]), hi):
        for p in tri:
            proxy.triangles.append(len(proxy.positions) // 3)
            proxy.positions.extend(p)
        proxy.tri_material.append(0)
    project.meshes.append(proxy)
    project.limits.mode = "wide"
    project.log("template_valley", size=size, cell=cell, triangles=terrain.triangle_count)
    return project
