#!/usr/bin/env python3
"""Export only Ghidra-defined strings and xrefs with the installed bridge."""
from __future__ import annotations

import argparse
import json
import os
import shutil
import subprocess
from pathlib import Path


BUILDS = {
    "8.4.1": "MRallye_8_4_1",
    "9.3.1": "MRallye_9_3_1",
    "9.10.0": "MRallye_9_10_0",
    "retail": "MRallye_retail",
}


def yaml_string(value: str) -> str:
    return json.dumps(value, ensure_ascii=True)


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--ghidra-home", type=Path, help="Defaults to ../_reverse-tools/ghidra-bridge-main/ghidra_12.0.4_PUBLIC")
    ap.add_argument("--bridge-root", type=Path, help="Defaults to ../_reverse-tools/ghidra-bridge-main")
    ap.add_argument("--output-dir", type=Path, help="Defaults to research-output/r-exe1")
    ap.add_argument("--builds", default=",".join(BUILDS))
    args = ap.parse_args()
    repo = Path(__file__).resolve().parents[2]
    bridge_root = (args.bridge_root or (repo.parent / "_reverse-tools" / "ghidra-bridge-main")).resolve()
    ghidra_home = (args.ghidra_home or (bridge_root / "ghidra_12.0.4_PUBLIC")).resolve()
    output = (args.output_dir or (repo / "research-output" / "r-exe1")).resolve()
    cli = bridge_root / ".venv" / "Scripts" / "ghidra-bridge.exe"
    if not cli.is_file():
        raise SystemExit(f"Installed ghidra-bridge CLI not found: {cli}")
    java_home = Path(os.environ.get("JAVA_HOME", "")) if os.environ.get("JAVA_HOME") else None
    if not java_home or not (java_home / "bin" / "java.exe").is_file():
        java = shutil.which("java")
        if not java:
            raise SystemExit("Set JAVA_HOME to a supported JDK before using ghidra-bridge")
        java_home = Path(java).resolve().parent.parent
    project_root = output / "ghidra-projects"
    scratch = output / "bridge-user"
    for child in ("Profile", "Roaming", "Local", "Temp"):
        (scratch / child).mkdir(parents=True, exist_ok=True)
    env = os.environ.copy()
    env.update({
        "JAVA_HOME": str(java_home), "GHIDRA_INSTALL_DIR": str(ghidra_home),
        "USERPROFILE": str(scratch / "Profile"), "APPDATA": str(scratch / "Roaming"),
        "LOCALAPPDATA": str(scratch / "Local"), "TEMP": str(scratch / "Temp"), "TMP": str(scratch / "Temp"),
    })
    chosen = [x.strip() for x in args.builds.split(",") if x.strip()]
    unknown = set(chosen) - set(BUILDS)
    if unknown:
        raise SystemExit(f"Unknown builds: {', '.join(sorted(unknown))}")
    for build in chosen:
        project_name = BUILDS[build]
        project_file = project_root / f"{project_name}.gpr"
        if not project_file.is_file():
            raise SystemExit(f"Ghidra project is missing for {build}: {project_file}; run r_exe1_ghidra.py first")
        export_dir = output / "bridge-strings" / build
        export_dir.mkdir(parents=True, exist_ok=True)
        cfg = output / "bridge-configs" / f"{build}.yaml"
        cfg.parent.mkdir(parents=True, exist_ok=True)
        cfg.write_text(
            "ghidra:\n"
            f"  install_dir: {yaml_string(str(ghidra_home).replace('\\\\', '/'))}\n"
            f"  project_dir: {yaml_string(str(project_root).replace('\\\\', '/'))}\n"
            f"  project_name: {yaml_string(project_name)}\n"
            "  program_name: \"MRallye.exe\"\n"
            "paths:\n"
            f"  export_dir: {yaml_string(str(export_dir).replace('\\\\', '/'))}\n"
            f"  address_map: {yaml_string(str(export_dir / 'address_map.json').replace('\\\\', '/'))}\n",
            encoding="utf-8",
        )
        command = [str(cli), "--config", str(cfg), "--export-dir", str(export_dir), "export", "strings"]
        print(f"EXPORT STRINGS {build}", flush=True)
        result = subprocess.run(command, cwd=bridge_root, env=env, text=True, capture_output=True)
        (export_dir / "bridge-export.stdout.log").write_text(result.stdout, encoding="utf-8", errors="replace")
        (export_dir / "bridge-export.stderr.log").write_text(result.stderr, encoding="utf-8", errors="replace")
        if result.returncode != 0 or not (export_dir / "_strings.json").is_file():
            raise SystemExit(f"Bridge string export failed for {build} (exit {result.returncode}); see {export_dir}")
        payload = json.loads((export_dir / "_strings.json").read_text(encoding="utf-8"))
        print(f"DONE {build}: {len(payload)} string records -> {export_dir}", flush=True)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
