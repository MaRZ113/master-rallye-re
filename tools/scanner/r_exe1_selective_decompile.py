#!/usr/bin/env python3
"""Export a bounded set of functions from the prepared Ghidra projects.

Uses ghidra-bridge's PyGhidra exporter for each selected function only. All
outputs are derived, local analysis metadata and belong under ignored
research-output/.
"""
from __future__ import annotations

import argparse
import json
import os
import shutil
import subprocess
import sys
from pathlib import Path


BUILDS = {
    "8.4.1": "MRallye_8_4_1",
    "9.3.1": "MRallye_9_3_1",
    "9.10.0": "MRallye_9_10_0",
    "retail": "MRallye_retail",
}


def worker(args: argparse.Namespace) -> int:
    import pyghidra
    from ghidra_ai_bridge.config import load_config
    from ghidra_ai_bridge.exporters.runner import export_single_function

    cfg = load_config(config_path=str(args.config))
    output_dir = Path(args.output_dir).resolve()
    output_dir.mkdir(parents=True, exist_ok=True)
    pyghidra.start()
    from ghidra.app.decompiler import DecompInterface
    from ghidra.util.task import ConsoleTaskMonitor
    manifest = {"schema_version": 1, "build": args.build, "functions": [], "missing": []}
    with pyghidra.open_program(
        None,
        project_location=cfg.ghidra_project_dir,
        project_name=cfg.ghidra_project_name,
        program_name=cfg.ghidra_program_name,
        analyze=False,
        nested_project_location=False,
    ) as flat_api:
        program = flat_api.getCurrentProgram()
        fm = program.getFunctionManager()
        ref_mgr = program.getReferenceManager()
        listing = program.getListing()
        address_factory = program.getAddressFactory()
        memory = program.getMemory()
        symbol_table = program.getSymbolTable()
        manifest["vtables"] = []
        for requested in args.vtable:
            base = address_factory.getDefaultAddressSpace().getAddress(requested.lower().removeprefix("0x"))
            entries = []
            for index in range(args.vtable_count):
                slot = base.add(index * program.getDefaultPointerSize())
                try:
                    target_value = memory.getInt(slot) & 0xFFFFFFFF
                    target = address_factory.getDefaultAddressSpace().getAddress(target_value)
                    func = fm.getFunctionAt(target) or fm.getFunctionContaining(target)
                    symbol = symbol_table.getPrimarySymbol(target)
                    if func is None:
                        if index == 0:
                            entries.append({"index": index, "slot": str(slot), "target": str(target), "symbol": symbol.getName() if symbol else None, "function": None})
                        break
                    entries.append({"index": index, "slot": str(slot), "target": str(target), "symbol": symbol.getName() if symbol else None, "function": func.getName(), "function_entry": str(func.getEntryPoint())})
                except Exception as exc:
                    manifest.setdefault("vtable_errors", []).append({"table": requested, "index": index, "error": str(exc)})
                    break
            manifest["vtables"].append({"table": requested, "entries": entries})
        manifest["xrefs_to"] = []
        for requested in args.xref_to:
            address = address_factory.getDefaultAddressSpace().getAddress(requested.lower().removeprefix("0x"))
            refs = []
            for ref in ref_mgr.getReferencesTo(address):
                source = ref.getFromAddress()
                function = fm.getFunctionContaining(source)
                refs.append({"from": str(source), "type": str(ref.getReferenceType()), "function": function.getName() if function else None, "function_entry": str(function.getEntryPoint()) if function else None})
            manifest["xrefs_to"].append({"target": requested, "references": refs})
        manifest["external_xrefs"] = []
        if args.external:
            patterns = [pattern.casefold() for pattern in args.external]
            for symbol in symbol_table.getAllSymbols(True):
                name = symbol.getName()
                if not any(pattern in name.casefold() for pattern in patterns):
                    continue
                refs = []
                for ref in ref_mgr.getReferencesTo(symbol.getAddress()):
                    source = ref.getFromAddress()
                    function = fm.getFunctionContaining(source)
                    refs.append({"from": str(source), "type": str(ref.getReferenceType()), "function": function.getName() if function else None, "function_entry": str(function.getEntryPoint()) if function else None})
                manifest["external_xrefs"].append({"symbol": name, "namespace": str(symbol.getParentNamespace()), "address": str(symbol.getAddress()), "references": refs})
        manifest["disassembly_ranges"] = []
        for requested in args.disasm_range:
            start_text, end_text = requested.split(":", 1)
            start = address_factory.getDefaultAddressSpace().getAddress(start_text.lower().removeprefix("0x"))
            end = address_factory.getDefaultAddressSpace().getAddress(end_text.lower().removeprefix("0x"))
            rows = []
            cursor = start
            while cursor.compareTo(end) <= 0:
                instruction = listing.getInstructionAt(cursor)
                if instruction is None:
                    cursor = cursor.add(1)
                    continue
                containing = fm.getFunctionContaining(instruction.getAddress())
                references = [str(ref.getToAddress()) for ref in ref_mgr.getReferencesFrom(instruction.getAddress())]
                rows.append({
                    "address": str(instruction.getAddress()),
                    "instruction": str(instruction),
                    "function_entry": str(containing.getEntryPoint()) if containing else None,
                    "references": references,
                })
                cursor = instruction.getMaxAddress().add(1)
            manifest["disassembly_ranges"].append({"range": requested, "instructions": rows})
        manifest["memory_word_ranges"] = []
        for requested in args.word_range:
            start_text, end_text = requested.split(":", 1)
            start = address_factory.getDefaultAddressSpace().getAddress(start_text.lower().removeprefix("0x"))
            end = address_factory.getDefaultAddressSpace().getAddress(end_text.lower().removeprefix("0x"))
            rows = []
            cursor = start
            while cursor.compareTo(end) <= 0:
                try:
                    value = memory.getInt(cursor) & 0xFFFFFFFF
                    target = address_factory.getDefaultAddressSpace().getAddress(value)
                    symbol = symbol_table.getPrimarySymbol(target)
                    rows.append({"address": str(cursor), "value": f"0x{value:08x}", "target_symbol": symbol.getName() if symbol else None})
                except Exception as exc:
                    rows.append({"address": str(cursor), "error": str(exc)})
                cursor = cursor.add(4)
            manifest["memory_word_ranges"].append({"range": requested, "words": rows})
        decomp = DecompInterface()
        decomp.openProgram(program)
        ir_decomp = DecompInterface()
        ir_decomp.setSimplificationStyle("normalize")
        ir_decomp.openProgram(program)
        monitor = ConsoleTaskMonitor()
        seen: set[str] = set()
        for requested in args.target:
            normalized = requested.lower().removeprefix("0x").replace(":", "")
            try:
                address = program.getAddressFactory().getDefaultAddressSpace().getAddress(normalized)
                func = fm.getFunctionAt(address) or fm.getFunctionContaining(address)
            except Exception:
                func = None
            if func is None:
                manifest["missing"].append(requested)
                continue
            entry = str(func.getEntryPoint())
            if entry not in seen:
                data = export_single_function(
                    func, program, fm, ref_mgr, str(output_dir), listing,
                    decomp=decomp, ir_decomp=ir_decomp, monitor=monitor,
                )
                seen.add(entry)
                manifest["functions"].append({
                    "address": entry,
                    "name": data.get("name"),
                    "signature": data.get("signature"),
                    "callers": len(data.get("callers", [])),
                    "callees": len(data.get("callees", [])),
                    "file": f"{entry.replace(':', '_')}.json",
                })
            manifest.setdefault("requested_to_function", []).append({
                "requested": requested,
                "resolved": entry,
                "exact_entry": entry.lower().endswith(normalized.zfill(8)),
            })
        decomp.dispose()
        ir_decomp.dispose()
    manifest_name = "_selective_manifest.json" if args.target else "_probe_manifest.json"
    manifest_path = output_dir / manifest_name
    manifest_path.write_text(json.dumps(manifest, indent=2) + "\n", encoding="utf-8")
    print(f"{args.build}: exported {len(manifest['functions'])} selected functions; missing={len(manifest['missing'])}")
    return 0


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--build", choices=BUILDS, required=True)
    ap.add_argument("--target", action="append", default=[], help="Function address; repeat as needed")
    ap.add_argument("--bridge-root", type=Path, help="Defaults to ../_reverse-tools/ghidra-bridge-main")
    ap.add_argument("--output-dir", type=Path, help="Defaults to research-output/r-exe1/bridge-selected/<build>")
    ap.add_argument("--vtable", action="append", default=[], help="Read a function pointer table at this address")
    ap.add_argument("--vtable-count", type=int, default=32)
    ap.add_argument("--xref-to", action="append", default=[], help="List references to an address")
    ap.add_argument("--external", action="append", default=[], help="Find external symbols containing this name and their callers")
    ap.add_argument("--disasm-range", action="append", default=[], help="List instructions from start:end (hex addresses)")
    ap.add_argument("--word-range", action="append", default=[], help="Read aligned 32-bit words from start:end (hex addresses)")
    ap.add_argument("--worker", action="store_true", help=argparse.SUPPRESS)
    ap.add_argument("--config", type=Path, help=argparse.SUPPRESS)
    args = ap.parse_args()
    repo = Path(__file__).resolve().parents[2]
    bridge_root = (args.bridge_root or (repo.parent / "_reverse-tools" / "ghidra-bridge-main")).resolve()
    ghidra_home = bridge_root / "ghidra_12.0.4_PUBLIC"
    output_root = repo / "research-output" / "r-exe1"
    output_dir = (args.output_dir or (output_root / "bridge-selected" / args.build)).resolve()
    scratch = output_root / "bridge-user"
    for child in ("Profile", "Roaming", "Local", "Temp"):
        (scratch / child).mkdir(parents=True, exist_ok=True)
    env = os.environ.copy()
    java_home = Path(env.get("JAVA_HOME", "C:/Program Files/Eclipse Adoptium/jdk-25.0.2.10-hotspot"))
    env.update({
        "JAVA_HOME": str(java_home),
        "GHIDRA_INSTALL_DIR": str(ghidra_home),
        "USERPROFILE": str(scratch / "Profile"),
        "APPDATA": str(scratch / "Roaming"),
        "LOCALAPPDATA": str(scratch / "Local"),
        "TEMP": str(scratch / "Temp"),
        "TMP": str(scratch / "Temp"),
    })
    config = (args.config or (output_root / "bridge-configs" / f"{args.build}.yaml")).resolve()
    if args.worker:
        args.output_dir = output_dir
        args.config = config
        return worker(args)
    python = bridge_root / ".venv" / "Scripts" / "python.exe"
    if not python.is_file():
        raise SystemExit(f"ghidra-bridge environment Python not found: {python}")
    output_dir.mkdir(parents=True, exist_ok=True)
    command = [str(python), str(Path(__file__).resolve()), "--worker", "--build", args.build,
               "--config", str(config), "--output-dir", str(output_dir)]
    for target in args.target:
        command += ["--target", target]
    for table in args.vtable:
        command += ["--vtable", table]
    command += ["--vtable-count", str(args.vtable_count)]
    for target in args.xref_to:
        command += ["--xref-to", target]
    for pattern in args.external:
        command += ["--external", pattern]
    for disasm_range in args.disasm_range:
        command += ["--disasm-range", disasm_range]
    for word_range in args.word_range:
        command += ["--word-range", word_range]
    result = subprocess.run(command, cwd=bridge_root, env=env, text=True)
    return result.returncode


if __name__ == "__main__":
    raise SystemExit(main())
