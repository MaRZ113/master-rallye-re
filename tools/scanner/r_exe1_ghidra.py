#!/usr/bin/env python3
"""Create isolated local Ghidra projects for the four read-only corpus EXEs."""
from __future__ import annotations

import argparse
import json
import os
import shutil
import subprocess
from pathlib import Path


BUILDS = {
    "8.4.1": ("demo-8.4.1", "MRallye_8_4_1"),
    "9.3.1": ("demo-9.3.1", "MRallye_9_3_1"),
    "9.10.0": ("demo-9.10.0", "MRallye_9_10_0"),
    "retail": ("retail", "MRallye_retail"),
}


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--corpora", type=Path)
    ap.add_argument("--ghidra-home", type=Path, help="Defaults to ../_reverse-tools/ghidra-bridge-main/ghidra_12.0.4_PUBLIC")
    ap.add_argument("--output-dir", type=Path, help="Defaults to research-output/r-exe1")
    ap.add_argument("--builds", default=",".join(BUILDS), help="Comma-separated subset in canonical build names")
    ap.add_argument("--max-cpu", type=int, default=2)
    ap.add_argument("--timeout-seconds", type=int, default=600)
    args = ap.parse_args()
    repo = Path(__file__).resolve().parents[2]
    corpora = (args.corpora or (repo.parent / "corpora")).resolve()
    ghidra_home = (args.ghidra_home or (repo.parent / "_reverse-tools" / "ghidra-bridge-main" / "ghidra_12.0.4_PUBLIC")).resolve()
    output = (args.output_dir or (repo / "research-output" / "r-exe1")).resolve()
    analyzer = ghidra_home / "support" / "analyzeHeadless.bat"
    if not analyzer.is_file():
        raise SystemExit(f"Ghidra headless analyzer not found: {analyzer}")
    java_home = Path(os.environ.get("JAVA_HOME", "")) if os.environ.get("JAVA_HOME") else None
    if not java_home or not (java_home / "bin" / "java.exe").is_file():
        java = shutil.which("java")
        if not java:
            raise SystemExit("Set JAVA_HOME to a supported JDK before running Ghidra")
        java_home = Path(java).resolve().parent.parent
    user_home = output / "ghidra-user"
    env = os.environ.copy()
    env.update({
        "JAVA_HOME": str(java_home),
        "USERPROFILE": str(user_home / "Profile"),
        "APPDATA": str(user_home / "Roaming"),
        "LOCALAPPDATA": str(user_home / "Local"),
        "TEMP": str(user_home / "Temp"),
        "TMP": str(user_home / "Temp"),
    })
    for key in ("Profile", "Roaming", "Local", "Temp"):
        (user_home / key).mkdir(parents=True, exist_ok=True)
    project_root = output / "ghidra-projects"
    project_root.mkdir(parents=True, exist_ok=True)
    chosen = [x.strip() for x in args.builds.split(",") if x.strip()]
    unknown = set(chosen) - set(BUILDS)
    if unknown:
        raise SystemExit(f"Unknown builds: {', '.join(sorted(unknown))}")
    manifest_path = output / "analysis-manifest.json"
    if manifest_path.is_file():
        try:
            manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError):
            manifest = {"schema_version": 1, "analysis_version": "Ghidra 12.1.4 (local copy in ghidra_12.0.4_PUBLIC folder)", "builds": {}}
    else:
        manifest = {"schema_version": 1, "analysis_version": "Ghidra 12.1.4 (local copy in ghidra_12.0.4_PUBLIC folder)", "builds": {}}
    manifest.setdefault("builds", {})
    for build in chosen:
        folder, project_name = BUILDS[build]
        exe = corpora / folder / "MRallye.exe"
        if not exe.is_file():
            raise SystemExit(f"Executable missing: {exe}")
        project_file = project_root / f"{project_name}.gpr"
        if project_file.exists():
            print(f"SKIP {build}: isolated Ghidra project already exists at {project_file}")
            continue
        log = output / f"analysis-{build}.log"
        command = [
            str(analyzer), str(project_root), project_name, "-import", str(exe),
            "-analysisTimeoutPerFile", str(args.timeout_seconds), "-max-cpu", str(args.max_cpu),
            "-log", str(log),
        ]
        print(f"ANALYZE {build}: {exe}", flush=True)
        result = subprocess.run(command, cwd=repo, env=env, text=True, capture_output=True)
        # Keep full analysis chatter local; report only concise status to the console.
        (output / f"analysis-{build}.stdout.log").write_text(result.stdout, encoding="utf-8", errors="replace")
        (output / f"analysis-{build}.stderr.log").write_text(result.stderr, encoding="utf-8", errors="replace")
        if result.returncode != 0 or not project_file.exists():
            raise SystemExit(f"Ghidra failed for {build} (exit {result.returncode}); inspect {log}")
        manifest["builds"][build] = {
            "executable_relative_path": f"corpora/{folder}/MRallye.exe",
            "project_name": project_name,
            "project_file": f"research-output/r-exe1/ghidra-projects/{project_name}.gpr",
            "analysis_log": f"research-output/r-exe1/analysis-{build}.log",
            "status": "ANALYSIS_SUCCEEDED",
        }
        manifest_path.write_text(json.dumps(manifest, indent=2) + "\n", encoding="utf-8")
        print(f"DONE {build}: Ghidra analysis completed", flush=True)
    print(f"Local project data and full logs: {output}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
