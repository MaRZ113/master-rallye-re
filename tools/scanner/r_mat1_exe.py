"""Narrow, unsaved Ghidra/ghidra-bridge vehicle material evidence export.

Run with the installed bridge's Python. Raw assembly/decompilation/IR stays in
the ignored output directory; no project analysis or saved changes are made.
"""
from __future__ import annotations

import argparse
import json
from pathlib import Path

EXPECTED_RETAIL_SHA256 = "bf8aef32407eb6552c05045b8abef149f32983cedd9503b865069b444c5f96b4"


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("addresses", nargs="+", type=lambda value: int(value, 16))
    parser.add_argument("--install", type=Path, required=True)
    parser.add_argument("--project", type=Path, required=True)
    parser.add_argument("--name", default="MasterRallye")
    parser.add_argument("--program", default="MRallye.exe")
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--scan-textures", action="store_true", help="List SetTexture-shaped calls in the renderer region")
    parser.add_argument("--data", nargs="*", type=lambda value: int(value, 16), default=[])
    args = parser.parse_args()
    repository = Path(__file__).resolve().parents[2]
    args.output = args.output.resolve()
    if not args.output.is_relative_to(repository / ".research-output"):
        raise ValueError("R-MAT1 raw evidence must stay under this checkout's .research-output")
    import pyghidra
    pyghidra.start(install_dir=args.install)
    from java.lang import Object
    from ghidra.program.flatapi import FlatProgramAPI
    from ghidra.app.decompiler import DecompInterface
    from ghidra_ai_bridge.exporters.runner import export_single_function
    project = pyghidra.open_project(args.project, args.name)
    consumer = Object()
    program = None
    decomp = ir = None
    try:
        domain_file = project.getProjectData().getFile("/" + args.program)
        if domain_file is None:
            def names(folder):
                return [str(item.getPathname()) for item in folder.getFiles()] + [
                    name for child in folder.getFolders() for name in names(child)]
            raise ValueError("Program missing; available: " + str(names(project.getProjectData().getRootFolder())))
        program = domain_file.getReadOnlyDomainObject(consumer, -1, pyghidra.task_monitor())
        if str(program.getExecutableSHA256()).casefold() != EXPECTED_RETAIL_SHA256:
            raise ValueError("Program SHA-256 differs from the R-MAT1 retail target")
        api = FlatProgramAPI(program)
        fm = program.getFunctionManager()
        args.output.mkdir(parents=True, exist_ok=True)
        if args.scan_textures:
            calls = []
            for inst in program.getListing().getInstructions(api.toAddr(0x00530000), True):
                if inst.getAddress().getOffset() >= 0x00590000:
                    break
                if inst.getMnemonicString() == "CALL" and "+ 0xf4]" in str(inst):
                    fn = fm.getFunctionContaining(inst.getAddress())
                    calls.append({"address": str(inst.getAddress()), "instruction": str(inst),
                                  "function": str(fn.getEntryPoint()) if fn else None})
            (args.output / "settexture-call-sites.json").write_text(json.dumps(calls, indent=2) + "\n")
            print("SetTexture-shaped sites:", calls, flush=True)
        if args.data:
            data = {"%08x" % value: ["%08x" % (int(program.getMemory().getInt(api.toAddr(value + i * 4))) & 0xffffffff)
                                      for i in range(16)] for value in args.data}
            (args.output / "data-words.json").write_text(json.dumps(data, indent=2) + "\n")
        transaction = program.startTransaction("R-MAT1 temporary missing virtual methods")
        try:
            functions = []
            for value in args.addresses:
                address = api.toAddr(value)
                fn = fm.getFunctionAt(address)
                if fn is None:
                    api.disassemble(address)
                    fn = api.createFunction(address, "R_MAT1_%08x" % value)
                if fn is None:
                    raise ValueError("Cannot identify function at %08x" % value)
                functions.append(fn)
            decomp = DecompInterface()
            decomp.openProgram(program)
            ir = DecompInterface()
            ir.setSimplificationStyle("normalize")
            ir.openProgram(program)
            index = {}
            for fn in functions:
                row = export_single_function(fn, program, fm, program.getReferenceManager(),
                                             str(args.output), program.getListing(), decomp, ir)
                address = row["address"]
                index[address] = {"address": address, "name": row["name"],
                                  "num_callers": len(row["callers"]), "num_callees": len(row["callees"])}
                print(address, len(row["assembly"]), "instructions", flush=True)
            index_path = args.output / "_index.json"
            old = json.loads(index_path.read_text()) if index_path.exists() else {}
            old.update(index)
            index_path.write_text(json.dumps(old, indent=2) + "\n")
            (args.output / "provenance.json").write_text(json.dumps({
                "program": program.getName(), "executable_sha256": str(program.getExecutableSHA256()),
                "ghidra_install": str(args.install), "exporter": "ghidra_ai_bridge.exporters.runner.export_single_function",
                "project_saved": False, "temporary_transaction": "ROLLED_BACK",
            }, indent=2) + "\n")
        finally:
            if decomp is not None:
                decomp.dispose()
            if ir is not None:
                ir.dispose()
            program.endTransaction(transaction, False)
    finally:
        if program is not None:
            program.release(consumer)
        project.close()


if __name__ == "__main__":
    main()
