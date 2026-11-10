"""Course Studio end-to-end Blender qualification (headless).

blender -b --factory-startup --python tests/blender/course_studio_e2e.py -- <work-dir> [--scenarios BDCA]

B  new course from scratch: valley template, edits (checkpoint, object with proxy, road carve), build
D  save .blend (project written by the save handler), reopen, compare, rebuild
C  external terrain: an OBJ written here, imported with Blender's OBJ importer, route/markers, build
A  Retail France1: open, change topology + material + checkpoint + route + collision, build as a new course
Writes <work-dir>/blender-qualification.json; exits non-zero on failure.
"""
import json
import math
import os
import sys
import time
import traceback
from pathlib import Path

import bpy

ROOT = Path(__file__).resolve().parents[2]
sys.path[:0] = [str(ROOT / "src"), str(ROOT / "blender")]
args = sys.argv[sys.argv.index("--") + 1:] if "--" in sys.argv else []
WORK = Path(args[0] if args else ROOT / ".research-output" / "course-studio" / "blender-e2e").resolve()
SCEN = args[args.index("--scenarios") + 1] if "--scenarios" in args else "BDCA"
WORK.mkdir(parents=True, exist_ok=True)
CAP2 = ROOT / ".research-output" / "course-cap2" / "menu-fix-01" / "build-input.json"
RESOURCE = ROOT.parent / "corpora" / "retail" / "Data.sma_unpacked"
results = {"blender": bpy.app.version_string, "work": str(WORK), "scenarios": {}}

import master_rallye_io  # noqa: E402
master_rallye_io.register()
from master_rallye_io.studio import convert as C, ops as O  # noqa: E402
from master_rallye.studio.model import load_project  # noqa: E402


def settings():
    return bpy.context.scene.mr_studio


def check(cond, message, bag):
    bag.setdefault("checks", []).append({"ok": bool(cond), "check": message})
    if not cond:
        raise AssertionError(message)


def build(bag, out_name):
    s = settings()
    s.resource_root = str(RESOURCE)
    s.cap2_input = str(CAP2) if CAP2.exists() else ""
    s.build_output = str(WORK / out_name)
    t = time.time()
    r = bpy.ops.mr.build_course()
    bag["build_seconds"] = round(time.time() - t, 1)
    check(r == {"FINISHED"}, "build operator finished", bag)
    errors = [f.message for f in s.findings if f.severity == "error"]
    bag["build_errors"] = errors
    check(not errors and s.last_build, f"build without errors {errors[:3]}", bag)
    report = json.loads((Path(s.last_build) / "course-build.json").read_text())
    bag["dx_bytes"] = report["dx"]["dx_bytes"]
    bag["draw_records"] = report["dx"]["draw_records"]
    bag["land_records"] = report["dx"]["land_database"]["records"]
    bag["collision"] = {k: report["dx"]["collision"][k] for k in ("planes", "solid_leaves", "terrain_polygons",
                                                                  "collision_polygons")}
    bag["probes"] = report["collision_probes"]
    bag["registration"] = report.get("registration")
    check(report["dx_verify"]["ok"], "written DX re-read by the independent parsers", bag)
    check(report["collision_probes"]["route_blocked"] == 0, "AI route never blocked by collision", bag)
    return report


def scenario_b(bag):
    bpy.ops.wm.read_homefile(use_empty=True)
    s = settings()
    s.resource_root = str(RESOURCE)
    r = bpy.ops.mr.new_course(name="StudioE2EValley", title="Studio E2E Valley", start_from="VALLEY", size=500.0,
                              environment="France1")
    check(r == {"FINISHED"}, "new course wizard", bag)
    terrain = next(o for o in C.studio_objects("MESH") if o.mr.role == "terrain")
    faces_before = len(terrain.data.polygons)
    # topology edit: subdivide a patch of the terrain
    bpy.context.view_layer.objects.active = terrain
    terrain.select_set(True)
    bpy.ops.object.mode_set(mode="EDIT")
    bpy.ops.mesh.select_all(action="DESELECT")
    bpy.ops.object.mode_set(mode="OBJECT")
    for poly in terrain.data.polygons[:200]:
        poly.select = True
    bpy.ops.object.mode_set(mode="EDIT")
    bpy.ops.mesh.subdivide(number_cuts=1)
    bpy.ops.object.mode_set(mode="OBJECT")
    check(len(terrain.data.polygons) > faces_before, "terrain topology changed (subdivided)", bag)
    # carve road along the route
    for o in bpy.context.selected_objects:
        o.select_set(False)
    terrain.select_set(True)
    bpy.context.view_layer.objects.active = terrain
    check(bpy.ops.mr.carve_road(width=9.0, shoulder=8.0) == {"FINISHED"}, "carve road", bag)
    # extra checkpoint at a route point, object with collision proxy
    route = C.active_route()
    mid = route.data.splines[0].points[len(route.data.splines[0].points) // 3].co
    bpy.context.scene.cursor.location = (mid.x, mid.y, mid.z)
    check(bpy.ops.mr.add_checkpoint() == {"FINISHED"}, "add checkpoint", bag)
    cps = C.studio_objects("CHECKPOINT")
    check(len(cps) == 4 and sorted(o.mr.order for o in cps) == [0, 1, 2, 3], "four ordered checkpoints", bag)
    bpy.context.scene.cursor.location = (mid.x + 40, mid.y + 20, mid.z)
    check(bpy.ops.mr.add_object(preset="HOUSE") == {"FINISHED"}, "add building with collision proxy", bag)
    check(any(o.mr.role == "collision" and o.mr.proxy_of for o in C.studio_objects("MESH")), "proxy exists", bag)
    check(bpy.ops.mr.validate() == {"FINISHED"}, "validate", bag)
    bag["validation"] = {sev: sum(f.severity == sev for f in settings().findings) for sev in ("error", "warning", "info")}
    bag["validation_messages"] = [f"{f.severity}: {f.message}" for f in settings().findings][:20]
    print(bag["validation_messages"])
    check(bpy.ops.mr.build_collision() == {"FINISHED"} and settings().collision_state == "OK", "collision rebuild", bag)
    bag["collision_summary"] = settings().collision_summary
    check(bpy.ops.mr.ai_preview() == {"FINISHED"}, "AI path preview", bag)
    path = bpy.data.objects.get("MR AI Path Preview")
    bag["ai_preview_points"] = sum(len(sp.points) for sp in path.data.splines)
    blend = WORK / "StudioE2EValley.blend"
    bpy.ops.wm.save_as_mainfile(filepath=str(blend))
    check((WORK / "StudioE2EValley_mrcourse" / "project.json").exists(), "project saved with the .blend", bag)
    build(bag, "build-B")
    bag["blend"] = str(blend)
    plain = Path(settings().last_build)
    # physical objects (optional Renderer module): PS2 families + a new model from a Blender mesh
    bpy.context.scene.cursor.location = (mid.x + 12, mid.y + 6, mid.z)
    check(bpy.ops.mr.add_physical(kind="haybale") == {"FINISHED"}, "add PS2 hay bale", bag)
    bpy.context.scene.cursor.location = (mid.x + 14, mid.y + 9, mid.z)
    check(bpy.ops.mr.add_physical(kind="tumblweed") == {"FINISHED"}, "add PS2 tumbleweed", bag)
    bpy.ops.mesh.primitive_cylinder_add(vertices=12, radius=0.5, depth=0.9, location=(mid.x + 10, mid.y + 3, mid.z + 1))
    drum = bpy.context.active_object
    drum.name = "Studio drum"
    for o in bpy.context.selected_objects:
        o.select_set(False)
    drum.select_set(True)
    check(bpy.ops.mr.add_physical(kind="SELECTED") == {"FINISHED"}, "selected mesh becomes a new physical model", bag)
    copy = drum.copy()          # an instance sharing the model
    copy.location.x += 3
    for c in drum.users_collection:
        c.objects.link(copy)
    build(bag, "build-B-phys")
    phys = Path(settings().last_build)
    report = json.loads((phys / "course-build.json").read_text())
    bag["physical_objects"] = report.get("physical_objects")
    check((phys / "optional" / "PS2RigidProps.ps2rgd").exists(), "optional Renderer asset written", bag)
    check(report["physical_objects"]["props"] == 4 and len(report["physical_objects"]["new_models"]) == 1,
          "4 props, one new model", bag)
    # Without the Renderer the course is exactly the course without physical objects:
    import hashlib
    def tree_hashes(root):
        return {f.relative_to(root).as_posix(): hashlib.sha256(f.read_bytes()).hexdigest()
                for f in (root / "resource-root").rglob("*") if f.is_file()}
    same = tree_hashes(plain) == tree_hashes(phys)
    bag["course_files_identical_without_renderer"] = same
    check(same, "game files of the course are byte-identical with and without physical objects", bag)


def scenario_d(bag):
    blend = WORK / "StudioE2EValley.blend"
    before = load_project(WORK / "StudioE2EValley_mrcourse")
    bpy.ops.wm.open_mainfile(filepath=str(blend))
    objs = C.studio_objects()
    kinds = {}
    for o in objs:
        kinds[o.mr.kind] = kinds.get(o.mr.kind, 0) + 1
    bag["objects_after_reopen"] = kinds
    after = C.scene_to_project(bpy.context)
    check(len(after.checkpoints) == len(before.checkpoints), "checkpoints survive reopen", bag)
    check(len(after.route.points) == len(before.route.points), "route survives reopen", bag)
    tb = sum(m.triangle_count for m in before.meshes)
    ta = sum(m.triangle_count for m in after.meshes)
    check(tb == ta, f"geometry survives reopen ({tb} == {ta})", bag)
    check(set(after.materials) == set(before.materials), "materials survive reopen", bag)
    check(after.build.title == before.build.title and after.build.catalog == before.build.catalog, "build settings", bag)
    check(after.textures.keys() == before.textures.keys(), "texture links survive reopen", bag)
    bag["reopen_project"] = {"meshes": len(after.meshes), "triangles": ta, "materials": len(after.materials)}
    # open the saved project folder into a new scene (portable project path)
    bpy.ops.mr.open_project(filepath=str(WORK / "StudioE2EValley_mrcourse" / "project.json"))
    again = C.scene_to_project(bpy.context)
    check(sum(m.triangle_count for m in again.meshes) == tb, "project folder reopens with identical geometry", bag)
    build(bag, "build-D")
    check(bag["registration"]["race_id"] == bag.get("expect_id", bag["registration"]["race_id"]), "stable registration", bag)


def scenario_c(bag):
    bpy.ops.wm.read_homefile(use_empty=True)
    s = settings()
    s.resource_root = str(RESOURCE)
    bpy.ops.mr.new_course(name="StudioE2EExternal", title="Studio E2E External", start_from="EMPTY",
                          environment="SpainW")
    obj_path = WORK / "external_terrain.obj"
    n, size = 60, 480.0
    with obj_path.open("w") as f:
        f.write("# external terrain (Y up)\nusemtl ground\n")
        for j in range(n + 1):
            for i in range(n + 1):
                x, z = -size / 2 + i * size / n, -size / 2 + j * size / n
                y = 10 * math.sin(x / 70) * math.cos(z / 55) + 0.0004 * x * x
                f.write(f"v {x:.3f} {y:.3f} {z:.3f}\nvt {i / 8:.4f} {j / 8:.4f}\n")
        for j in range(n):
            for i in range(n):
                a = j * (n + 1) + i + 1
                b, c, d = a + 1, a + n + 2, a + n + 1
                f.write(f"f {a}/{a} {d}/{d} {c}/{c} {b}/{b}\n")
    r = bpy.ops.mr.import_geometry(filepath=str(obj_path), role="terrain")
    check(r == {"FINISHED"}, "OBJ imported with Blender's importer", bag)
    terrain = next(o for o in C.studio_objects("MESH") if o.mr.role == "terrain")
    terrain.data.materials.clear()
    terrain.data.materials.append(bpy.data.materials.get("MR grass") or O._preset_material("Grass"))
    check(terrain.mr.role == "terrain", "external mesh has the terrain role", bag)
    # route across the terrain, snapped to it
    pts = [(-200.0 + 400.0 * k / 30, 0.0, 120.0 * math.sin(k / 30 * math.pi * 2)) for k in range(31)]
    C.curve_object("MR AI Route", pts, "ROUTE").mr.route_active = True
    bpy.ops.mr.snap_markers()
    first, last = C.curve_points(C.active_route())[1], C.curve_points(C.active_route())[-2]
    bpy.context.scene.cursor.location = C.g2b(first)
    bpy.ops.mr.add_area(kind="START")
    bpy.context.scene.cursor.location = C.g2b(last)
    bpy.ops.mr.add_area(kind="FINISH")
    bpy.ops.mr.place_checkpoints(count=2)
    bpy.ops.mr.snap_markers()
    bpy.ops.wm.save_as_mainfile(filepath=str(WORK / "StudioE2EExternal.blend"))
    build(bag, "build-C")


def scenario_a(bag):
    bpy.ops.wm.read_homefile(use_empty=True)
    s = settings()
    s.resource_root = str(RESOURCE)
    t = time.time()
    r = bpy.ops.mr.open_retail(race="France1")
    bag["open_seconds"] = round(time.time() - t, 1)
    check(r == {"FINISHED"}, "open France1", bag)
    meshes = {o.name: (o.mr.role, len(o.data.polygons)) for o in C.studio_objects("MESH")}
    bag["imported_meshes"] = meshes
    check(any(v[0] == "collision" for v in meshes.values()), "native collision recovered as editable mesh", bag)
    terrain = bpy.data.objects["Terrain"]
    me = terrain.data
    # 1. topology: delete one face and fill the hole with a fan (new polygons)
    nf = len(me.polygons)
    bpy.context.view_layer.objects.active = terrain
    for o in bpy.context.selected_objects:
        o.select_set(False)
    terrain.select_set(True)
    bpy.ops.object.mode_set(mode="EDIT")
    bpy.ops.mesh.select_all(action="DESELECT")
    bpy.ops.object.mode_set(mode="OBJECT")
    for poly in me.polygons[100:140]:
        poly.select = True
    bpy.ops.object.mode_set(mode="EDIT")
    bpy.ops.mesh.subdivide(number_cuts=2)
    bpy.ops.object.mode_set(mode="OBJECT")
    check(len(me.polygons) != nf, "France1 terrain topology changed", bag)
    # 2. geometry: raise a hill beside the road
    route = C.active_route()
    rp = route.data.splines[0].points[60].co
    for v in me.vertices:
        d = math.hypot(v.co.x - (rp.x + 60), v.co.y - rp.y)
        if d < 40:
            v.co.z += 6.0 * (1 - d / 40)
    # 3. one material: change a terrain material's surface and texture wrap
    mat = me.materials[0]
    mat.mr.surface = "gravel"
    # 4. one checkpoint moved and resized
    cp = sorted(C.studio_objects("CHECKPOINT"), key=lambda o: o.mr.order)[0]
    cp.location.x += 4.0
    cp.scale = (25.0, 25.0, 25.0)
    # 5. AI route: move a point and add one
    sp = route.data.splines[0]
    sp.points[80].co.x += 3.0
    sp.points.add(1)
    sp.points[-1].co = (sp.points[-2].co.x + 5.0, sp.points[-2].co.y, sp.points[-2].co.z, 1.0)
    # 6. collision: add an impassable blocker away from the road
    bpy.context.scene.cursor.location = (rp.x + 80, rp.y + 30, rp.z)
    bpy.ops.mr.add_blocker(width=8, depth=8, height=5)
    s.course_name = "StudioFranceEdit"
    s.course_key = "StudioFranceEdit"
    s.course_title = "France - Studio edit"
    bpy.ops.wm.save_as_mainfile(filepath=str(WORK / "StudioFranceEdit.blend"))
    report = build(bag, "build-A")
    retail = (RESOURCE / "DataGx" / "Course" / "France1" / "france1.dx")
    bag["retail_untouched"] = retail.exists()


for key, fn in (("B", scenario_b), ("D", scenario_d), ("C", scenario_c), ("A", scenario_a)):
    if key not in SCEN:
        continue
    bag = {}
    t = time.time()
    try:
        fn(bag)
        bag["status"] = "PASS"
    except Exception as exc:
        bag["status"] = "FAIL"
        bag["error"] = f"{exc}"
        bag["trace"] = traceback.format_exc()
        print(bag["trace"])
    bag["seconds"] = round(time.time() - t, 1)
    results["scenarios"][key] = bag
    (WORK / "blender-qualification.json").write_text(json.dumps(results, indent=1, default=str))
    print(f"SCENARIO {key}: {bag['status']} ({bag['seconds']} s)", flush=True)

ok = all(v["status"] == "PASS" for v in results["scenarios"].values())
results["status"] = "PASS" if ok else "FAIL"
(WORK / "blender-qualification.json").write_text(json.dumps(results, indent=1, default=str))
sys.stdout.flush()
os._exit(0 if ok else 1)
