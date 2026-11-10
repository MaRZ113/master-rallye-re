"""Installed-ZIP smoke test: Blender's own add-on installer, vendored core, new course -> build.

BLENDER_USER_SCRIPTS=<empty dir> blender -b --factory-startup --python tests/blender/course_studio_zip_smoke.py -- <zip> <work>
"""
import json
import os
import sys
from pathlib import Path

import bpy

args = sys.argv[sys.argv.index("--") + 1:]
ZIP, WORK = Path(args[0]), Path(args[1])
WORK.mkdir(parents=True, exist_ok=True)
ROOT = Path(__file__).resolve().parents[2]
assert not any("master-rallye-re-course" in p and p.endswith("src") for p in sys.path)
bpy.ops.preferences.addon_install(filepath=str(ZIP), overwrite=True)
bpy.ops.preferences.addon_enable(module="master_rallye_io")
import master_rallye_io.studio.core as core  # noqa: E402
result = {"core": core._base.__name__}
assert ".vendor." in core._base.__name__, core._base.__name__
s = bpy.context.scene.mr_studio
s.resource_root = str(ROOT.parent / "corpora" / "retail" / "Data.sma_unpacked")
bpy.ops.mr.new_course(name="ZipSmoke", title="Zip Smoke", start_from="VALLEY", size=300.0, environment="France1")
bpy.ops.wm.save_as_mainfile(filepath=str(WORK / "ZipSmoke.blend"))
s = bpy.context.scene.mr_studio
s.build_output = str(WORK / "build")
bpy.ops.mr.build_course()
result["last_build"] = s.last_build
result["errors"] = [f.message for f in s.findings if f.severity == "error"]
result["ok"] = bool(s.last_build) and not result["errors"] and (Path(s.last_build) / "course-build.json").exists()
(WORK / "zip-smoke.json").write_text(json.dumps(result, indent=1))
print("ZIP SMOKE", "PASS" if result["ok"] else "FAIL", result)
sys.stdout.flush()
os._exit(0 if result["ok"] else 1)
