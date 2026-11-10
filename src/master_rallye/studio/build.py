"""One-click Course build: validate, write every native resource, register, publish atomically.

Output (``<output>/<CourseKey>/``):

* ``resource-root/DataGx/Course/<key>/<key>.dx`` + ``.txt`` + FEED textures;
* ``resource-root/DataScene/RaceTest/<Key>.xml`` + ``.hnt``;
* ``resource-root/DataScene/ICont/<key>.sfl``;
* ``courses.json`` (accepted CAP2 catalog + this course and race) and
  ``compose.json`` (CAP2 build input whose ``resource_overrides`` point at the
  files above), when a CAP2 base is configured;
* ``course-build.json``: inputs, hashes, every report and all findings.

Nothing outside the output directory is written; Retail, Pristine and the
game installation are read only. The tree is staged next to the target and
moved into place with ``os.replace`` after it has been re-read and checked.
"""
from __future__ import annotations

import copy
import hashlib
import json
import os
import shutil
import subprocess
import sys
import time
from dataclasses import dataclass, field
from pathlib import Path

from . import SCHEMA
from .ai import raceline, sfl_bytes
from .collision import validate_tree
from .dx_build import build_course_dx, verify_course_dx
from .model import CourseProject, safe_key
from .race import build_hnt, build_racetest
from .textures import convert_image, noise_texture, solid_texture
from .validate import ERROR, WARNING, Finding, ci_path, summary, validate_project

ROOT = Path(__file__).resolve().parents[3]


def _sha(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


@dataclass
class BuildResult:
    ok: bool
    output: Path | None
    findings: list
    report: dict = field(default_factory=dict)

    def errors(self):
        return [f for f in self.findings if f.severity == ERROR]


def _texture_payloads(project: CourseProject, keys, resource_root: Path | None, project_dir: Path | None):
    payloads, reports, problems = {}, {}, []
    for key in keys:
        tex = project.textures.get(key)
        data = None
        if tex is not None and tex.source:
            path = Path(tex.source)
            if not path.is_absolute() and project_dir is not None:
                path = project_dir / path
            if path.exists():
                data, info = convert_image(path)
                reports[key] = info
            else:
                problems.append(f"texture {key}: image {path} is missing")
                continue
        if data is None and tex is not None and tex.native and resource_root is not None:
            found = ci_path(resource_root, tex.native)
            if found is not None:
                data = found.read_bytes()
                reports[key] = {"native": tex.native}
        if data is None and key in ("noise-tga", "aluminium-tga") and resource_root is not None:
            for course in ("France1", "Spain2", "Italy2", "Turkey1"):
                found = ci_path(resource_root, f"DataGx/Course/{course}/{key}.dxt")
                if found is not None:
                    data = found.read_bytes()
                    reports[key] = {"native": f"DataGx/Course/{course}/{key}.dxt"}
                    break
        if data is None and key == "noise-tga":
            data = noise_texture()
            reports[key] = {"generated": "neutral noise"}
        if data is None and key == "aluminium-tga":
            data = solid_texture((200, 200, 205, 255))
            reports[key] = {"generated": "flat metal"}
        if data is None:
            problems.append(f"texture {key} could not be resolved")
            continue
        payloads[key] = data
    return payloads, reports, problems


def rigid_base_asset(resource_root: Path | None) -> Path | None:
    """Accepted Renderer RigidProps asset (36 PS2 courses), used as the base the Studio course is added to."""
    candidates = [os.environ.get("MR_RIGID_BASE_ASSET")]
    if resource_root is not None:
        for up in [Path(resource_root)] + list(Path(resource_root).parents)[:3]:
            candidates.append(str(up / "PS2Grass" / "PS2RigidProps.ps2rgd"))
    for c in candidates:
        if c and Path(c).is_file():
            return Path(c)
    return None


def _load_cap2_base(path: Path):
    """Accepted CAP2 input: a build-input/compose JSON (with course_manifest) or a courses.json catalog."""
    data = json.loads(Path(path).read_text(encoding="utf-8"))
    if "course_manifest" in data:
        catalog = json.loads(Path(data["course_manifest"]).read_text(encoding="utf-8"))
        return data, catalog
    if data.get("schema") == "mr-course-registry/1":
        return None, data
    raise ValueError(f"{path} is neither a CAP2 build input nor a mr-course-registry/1 catalog")


# Retail Course Select groups: original entries per group (COURSE-CAP2 menu_groups of the accepted build).
RETAIL_GROUP_SIZES = (3, 3, 3, 3, 3, 11, 10, 3)


def register_course(catalog: dict, *, key: str, title: str, menu_group: int, menu_position: int, modes,
                    template_race: dict | None = None) -> tuple[dict, dict]:
    """Return (catalog copy with this course and race, race row). Original Race IDs 0..38 stay unchanged.

    Rebuilding the same course key keeps its Race ID, menu slot and progress key.
    """
    from ..course_registry import validate_manifest
    catalog = copy.deepcopy(catalog)
    baseline = copy.deepcopy(catalog["races"][:39])
    course_key = f"studio:{key}"
    folder = f"DataGx/Course/{key}"
    if not 0 <= menu_group < len(RETAIL_GROUP_SIZES):
        raise ValueError(f"menu group {menu_group} does not exist (0..{len(RETAIL_GROUP_SIZES) - 1})")
    if not any(c["key"] == course_key for c in catalog["courses"]):
        catalog["courses"].append({"key": course_key, "folder": folder, "model": f"{folder}/{key.lower()}.dx"})
    template = template_race or next(r for r in catalog["races"] if r["id"] == 0)
    row = next((r for r in catalog["races"] if r["course"] == course_key), None)
    if row is None:
        taken = [r["menu"]["position"] for r in catalog["races"] if r.get("menu", {}).get("group") == menu_group]
        position = max([RETAIL_GROUP_SIZES[menu_group] - 1] + taken) + 1 if menu_position < 0 else menu_position
        if position in taken:
            raise ValueError(f"menu position {position} of group {menu_group} is already used")
        row = {"id": len(catalog["races"]), "menu": {"group": menu_group, "position": position,
                                                     "flag_frame": 0, "screenshot_pair": 0}}
        catalog["races"].append(row)
    race_id = row["id"]
    row.update(course=course_key, scene=f"DataScene/RaceTest/{key}.xml", icont=f"DataScene/ICont/{key.lower()}.sfl",
               title=title or key, modes=list(modes), progress_key=f"studio-{key.lower()}",
               native_fields=[race_id] + list(template["native_fields"][1:]))
    validate_manifest(catalog, baseline)
    return catalog, row


def cap2_python() -> str:
    """An interpreter that can run the COURSE-CAP2 builder (it needs ``capstone``)."""
    candidates = [os.environ.get("MR_CAP2_PYTHON"), sys.executable,
                  str(Path.home() / "scoop" / "apps" / "python" / "current" / "python.exe"), shutil.which("python")]
    for exe in candidates:
        if exe and Path(exe).exists() and Path(exe).name.lower().startswith("python"):
            probe = subprocess.run([exe, "-c", "import capstone"], capture_output=True)
            if probe.returncode == 0:
                return exe
    raise RuntimeError("COURSE-CAP2 needs a Python with the 'capstone' package (set MR_CAP2_PYTHON)")


def build_course(project: CourseProject, *, project_dir: Path | None, resource_root: Path | None,
                 output: Path | None = None, progress=None, run_cap2: bool = False,
                 cap2_output: Path | None = None) -> BuildResult:
    say = progress or (lambda stage, fraction=None: None)
    began = time.time()
    key = safe_key(project.course_key())
    project.build.course_key = key
    out_root = Path(output) if output else (Path(project_dir or ".") / (project.build.output or "build"))
    target = out_root / key
    report: dict = {"schema": "mr-course-studio-build/1", "project_schema": SCHEMA, "project": project.uid,
                    "course": key, "title": project.build.title or project.name, "started": began}

    # 1. validate (collision probes are added after the tree exists)
    say("validate", 0.0)
    findings = validate_project(project, resource_root=resource_root, project_dir=project_dir)
    if any(f.severity == ERROR for f in findings):
        return BuildResult(False, None, findings, {**report, "stopped": "validation"})

    # 2-3. geometry, surfaces, collision tree
    say("geometry", 0.1)
    dx = build_course_dx(project, progress=lambda stage, f: say(stage, 0.1 + 0.5 * f))
    verify = verify_course_dx(dx.dx, dx)
    report["dx"] = dx.report
    report["dx_verify"] = verify
    if not verify["ok"]:
        findings.append(Finding(ERROR, "geometry", "written DX failed re-read: " + "; ".join(verify["problems"])))
    say("collision probes", 0.62)
    probes = validate_tree(project, dx.bsp_tree)
    report["collision_probes"] = probes.summary()
    findings += [f for f in validate_project(project, resource_root=resource_root, project_dir=project_dir,
                                              collision_report=probes) if f.category == "collision"]

    # 4. textures
    say("textures", 0.7)
    textures, tex_reports, tex_problems = _texture_payloads(project, dx.texture_keys, resource_root, project_dir)
    report["textures"] = tex_reports
    for problem in tex_problems:
        findings.append(Finding(ERROR, "resources", problem))
    optional = {}
    if project.extras.get("ps2_props"):
        from .ps2_objects import build_optional_asset
        base = rigid_base_asset(resource_root)
        if base is None:
            findings.append(Finding(WARNING, "resources", "physical objects need the Renderer RigidProps base asset "
                                    "(PS2RigidProps.ps2rgd); the course is built without them"))
        else:
            model_textures = {m.get("texture") for m in (project.extras.get("ps2_models") or {}).values()} - {None}
            tex_for_models, _, _ = _texture_payloads(project, sorted(model_textures), resource_root, project_dir)
            try:
                data, manifest = build_optional_asset(project, base, f"DataGx/Course/{key}/{key.lower()}.dx", dx.dx,
                                                      tex_for_models)
                optional["optional/PS2RigidProps.ps2rgd"] = data
                manifest["renderer_ini"] = {"RigidPropsAsset": "<path to optional/PS2RigidProps.ps2rgd>",
                                            "RigidPropsAssetSha256": manifest["asset_sha256"]}
                optional["optional/rigid-props.json"] = json.dumps(manifest, indent=1).encode()
                optional["optional/RigidProps.ini"] = (
                    "; Renderer RigidProps (optional): add to PS2Port.ini of a Renderer build that supports\r\n"
                    "; RigidPropsAssetSha256 (feature/course-studio-rigid). Without it the course runs without props.\r\n"
                    f"RigidPropsAsset=PS2RigidProps.ps2rgd\r\nRigidPropsAssetSha256={manifest['asset_sha256']}\r\n").encode()
                report["physical_objects"] = {k: v for k, v in manifest.items() if k != "models"}
            except ValueError as exc:
                findings.append(Finding(ERROR, "gameplay", f"physical objects: {exc}"))

    # 5-7. scene, AI field, HNT
    say("scene", 0.8)
    if resource_root is None:
        findings.append(Finding(ERROR, "resources", "a resource root is required for the environment template scene"))
        return BuildResult(False, None, findings, report)
    template = ci_path(resource_root, f"DataScene/RaceTest/{project.environment.template}.xml")
    if template is None:
        findings.append(Finding(ERROR, "resources", f"template scene {project.environment.template} not found"))
        return BuildResult(False, None, findings, report)
    scene, scene_report = build_racetest(project, template)
    report["scene"] = scene_report
    sfl = sfl_bytes(project)
    hnt = build_hnt(key, dx.texture_keys)
    if any(f.severity == ERROR for f in findings):
        return BuildResult(False, None, findings, report)

    # 8. stage
    say("stage", 0.9)
    files = {
        f"DataGx/Course/{key}/{key.lower()}.dx": dx.dx,
        f"DataGx/Course/{key}/{key.lower()}.txt": dx.txt.encode("latin-1", "replace"),
        f"DataScene/RaceTest/{key}.xml": scene,
        f"DataScene/RaceTest/{key}.hnt": hnt,
        f"DataScene/ICont/{key.lower()}.sfl": sfl,
    }
    for tk, data in textures.items():
        files[f"DataGx/Course/{key}/{tk}.dxt"] = data
    out_root.mkdir(parents=True, exist_ok=True)
    staging = out_root / f".{key}.staging-{os.getpid()}"
    if staging.exists():
        shutil.rmtree(staging)
    try:
        for rel, data in files.items():
            path = staging / "resource-root" / rel
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_bytes(data)
        for rel, data in optional.items():
            path = staging / rel
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_bytes(data)
        report["files"] = {rel: {"sha256": _sha(data), "bytes": len(data)} for rel, data in files.items()}
        report["optional_files"] = {rel: {"sha256": _sha(data), "bytes": len(data)} for rel, data in optional.items()}

        # 9. re-read the staged tree with the independent readers
        from ..course_xml import parse_course_xml
        from ..sfl import parse_sfl
        staged_xml = parse_course_xml(staging / "resource-root" / f"DataScene/RaceTest/{key}.xml")
        staged_sfl = parse_sfl(staging / "resource-root" / f"DataScene/ICont/{key.lower()}.sfl")
        report["reread"] = {"xml_eggs": len(staged_xml.eggs), "sfl_cells": staged_sfl.cell_count,
                            "dx": verify_course_dx((staging / "resource-root" / f"DataGx/Course/{key}/{key.lower()}.dx").read_bytes())["ok"]}

        # 10. registry rows for COURSE-CAP2
        if project.build.catalog:
            base_path = Path(project.build.catalog)
            if not base_path.is_absolute() and project_dir is not None:
                base_path = project_dir / base_path
            base, catalog = _load_cap2_base(base_path)
            catalog, row = register_course(catalog, key=key, title=project.build.title or project.name,
                                           menu_group=project.build.menu_group,
                                           menu_position=project.build.menu_position, modes=project.build.modes)
            (staging / "courses.json").write_text(json.dumps(catalog, indent=2, sort_keys=True), encoding="utf-8")
            report["registration"] = {"race_id": row["id"], "menu": row["menu"], "title": row["title"]}
            if base is not None:
                # A new course changes the gameplay contract, so CAP2 must start from a fresh private profile:
                # the base's saved player state and previous contract are not carried over.
                compose = {k: v for k, v in base.items() if k not in ("course_manifest", "resource_overrides",
                                                                      "player_state_source", "previous_course_contract")}
                compose["course_manifest"] = str((target / "courses.json").resolve())
                # chained Studio builds keep the earlier courses' files (their catalog rows are kept too)
                compose["resource_overrides"] = {**base.get("resource_overrides", {}),
                                                 **{rel: str((target / "resource-root" / rel).resolve()) for rel in files}}
                (staging / "compose.json").write_text(json.dumps(compose, indent=2), encoding="utf-8")
        report["findings"] = [f.to_dict() for f in findings]
        report["summary"] = summary(findings)
        report["seconds"] = round(time.time() - began, 1)
        report["runtime"] = "NOT RUN BY THE BUILD: owner gameplay test required"
        (staging / "course-build.json").write_text(json.dumps(report, indent=1, default=str), encoding="utf-8")

        # 11. publish atomically (previous build is kept as .previous)
        if target.exists():
            previous = out_root / f"{key}.previous"
            if previous.exists():
                shutil.rmtree(previous)
            os.replace(target, previous)
        os.replace(staging, target)
    finally:
        if staging.exists():
            shutil.rmtree(staging, ignore_errors=True)
    project.log("build", output=str(target), dx_sha256=report["files"][f"DataGx/Course/{key}/{key.lower()}.dx"]["sha256"])

    # 12. optional CAP2 private package
    if run_cap2:
        compose = target / "compose.json"
        if not compose.exists():
            findings.append(Finding(ERROR, "resources", "CAP2 package requested but no CAP2 base input is configured"))
        else:
            # COURSE-CAP2 accepts private packages only below its own research output (fresh directory)
            dest = cap2_output or (ROOT / ".research-output" / "course-cap2" /
                                   f"studio-{key.lower()}-{time.strftime('%Y%m%d-%H%M%S')}")
            say("cap2", 0.95)
            proc = subprocess.run([cap2_python(), str(ROOT / "tools" / "build_course_registry.py"), "--manifest",
                                   str(compose), "--output", str(dest)], capture_output=True, text=True,
                                  env={**os.environ, "PYTHONPATH": os.pathsep.join([str(ROOT / "src"), str(ROOT / "tools")])})
            report["cap2"] = {"returncode": proc.returncode, "output": str(dest), "stdout": proc.stdout[-4000:],
                              "stderr": proc.stderr[-4000:]}
            if proc.returncode != 0:
                findings.append(Finding(ERROR, "resources", "COURSE-CAP2 build failed: " + proc.stderr.strip()[-400:]))
            (target / "course-build.json").write_text(json.dumps({**report, "findings": [f.to_dict() for f in findings]},
                                                                 indent=1, default=str), encoding="utf-8")
    say("done", 1.0)
    ok = not any(f.severity == ERROR for f in findings)
    return BuildResult(ok, target, findings, report)
