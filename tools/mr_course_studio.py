#!/usr/bin/env python3
"""Master Rallye Course Studio command line (same core as the Blender add-on).

  mr_course_studio.py new <project-dir> --name MyCourse [--template valley|empty] [--title "..."]
  mr_course_studio.py import-retail <project-dir> --race France1 [--resource-root R] [--no-collision]
  mr_course_studio.py import-gxm <project-dir> --gxm path\\to\\course.gxm
  mr_course_studio.py import-obj <project-dir> --obj terrain.obj [--role terrain] [--material grass]
  mr_course_studio.py validate <project-dir> [--resource-root R] [--collision]
  mr_course_studio.py build <project-dir> [--resource-root R] [--output DIR] [--catalog CAP2.json] [--cap2]
  mr_course_studio.py info <project-dir>

The resource root (directory with DataGx + DataScene, e.g. an unpacked Data.sma)
is taken from --resource-root, $MR_RESOURCE_ROOT, or the project's last value.
"""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))
sys.setrecursionlimit(100000)

from master_rallye.studio.model import load_project, resolve_resource_root, save_project  # noqa: E402


def _root(args, project=None):
    hint = args.resource_root or (project.extras.get("resource_root_hint") if project else None)
    root = resolve_resource_root(hint, extra=[ROOT.parent / "corpora" / "retail", ROOT.parent])
    if root is None:
        sys.exit("resource root not found: pass --resource-root (folder with DataGx and DataScene)")
    return root


def _progress(stage, fraction=None):
    print(f"  [{stage}] {'' if fraction is None else f'{fraction:.0%}'}", flush=True)


def main(argv=None) -> int:
    p = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    sub = p.add_subparsers(dest="command", required=True)
    for name in ("new", "import-retail", "import-gxm", "import-obj", "validate", "build", "info"):
        s = sub.add_parser(name)
        s.add_argument("project", type=Path)
        s.add_argument("--resource-root")
        if name == "new":
            s.add_argument("--name", required=True)
            s.add_argument("--title", default="")
            s.add_argument("--template", choices=("valley", "empty"), default="valley")
            s.add_argument("--environment", default="France1")
        if name == "import-retail":
            s.add_argument("--race", required=True)
            s.add_argument("--no-collision", action="store_true")
        if name == "import-gxm":
            s.add_argument("--gxm", type=Path, required=True)
        if name == "import-obj":
            s.add_argument("--obj", type=Path, required=True)
            s.add_argument("--role", default="terrain")
            s.add_argument("--material", default="grass")
            s.add_argument("--scale", type=float, default=1.0)
            s.add_argument("--z-up", action="store_true")
        if name == "validate":
            s.add_argument("--collision", action="store_true", help="also build the collision tree and probe it")
        if name == "build":
            s.add_argument("--output", type=Path)
            s.add_argument("--catalog", help="accepted COURSE-CAP2 build input or courses.json")
            s.add_argument("--cap2", action="store_true", help="also run the COURSE-CAP2 private package build")
    args = p.parse_args(argv)

    if args.command == "new":
        from master_rallye.studio.templates import new_project, valley_course
        project = (valley_course(args.name, title=args.title or args.name) if args.template == "valley"
                   else new_project(args.name, title=args.title))
        project.environment.template = args.environment
        save_project(project, args.project)
        print(f"created {args.project / 'project.json'}")
        return 0
    if args.command == "import-retail":
        from master_rallye.studio.importer import import_retail_course
        root = _root(args)
        project = import_retail_course(root, args.race, extract_collision=not args.no_collision, progress=_progress)
        project.extras["resource_root_hint"] = str(root)
        save_project(project, args.project)
        print(json.dumps([(m.name, m.role, m.triangle_count) for m in project.meshes]))
        return 0

    project = load_project(args.project)
    if args.command == "import-gxm":
        from master_rallye.studio.importer import import_gxm
        import_gxm(args.gxm, project)
        save_project(project, args.project)
        return 0
    if args.command == "import-obj":
        from master_rallye.studio.importer import import_obj
        import_obj(args.obj, project, role=args.role, material=args.material, scale=args.scale, y_up=not args.z_up)
        save_project(project, args.project)
        return 0
    if args.command == "info":
        print(json.dumps({"name": project.name, "course": project.course_key(), "meshes":
                          [(m.name, m.role, m.triangle_count) for m in project.meshes],
                          "materials": len(project.materials), "checkpoints": len(project.checkpoints),
                          "route_points": len(project.route.points), "provenance": project.provenance.kind}, indent=1))
        return 0
    root = _root(args, project)
    if args.command == "validate":
        from master_rallye.studio.validate import summary, validate_project
        report = None
        if args.collision:
            from master_rallye.studio.collision import build_tree, validate_tree
            tree, _, stats = build_tree(project)
            report = validate_tree(project, tree)
            print(json.dumps({"tree": stats, "probes": report.summary()}, indent=1, default=str))
        findings = validate_project(project, resource_root=root, project_dir=args.project, collision_report=report)
        for f in findings:
            print(f"{f.severity.upper():8} {f.category:10} {f.message}")
        print(json.dumps(summary(findings)))
        return 1 if any(f.severity == "error" for f in findings) else 0
    if args.command == "build":
        from master_rallye.studio.build import build_course
        if args.catalog:
            project.build.catalog = str(Path(args.catalog).resolve())
        result = build_course(project, project_dir=args.project, resource_root=root, output=args.output,
                              progress=_progress, run_cap2=args.cap2)
        save_project(project, args.project)
        for f in result.findings:
            if f.severity != "info":
                print(f"{f.severity.upper():8} {f.category:10} {f.message}")
        print(json.dumps({"ok": result.ok, "output": str(result.output), "dx": result.report.get("dx", {}).get("dx_bytes"),
                          "probes": result.report.get("collision_probes"), "registration": result.report.get("registration")},
                         indent=1, default=str))
        return 0 if result.ok else 1
    return 2


if __name__ == "__main__":
    raise SystemExit(main())
