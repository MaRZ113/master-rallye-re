"""Bounded Ghidra evidence export for Broker/XML/persistence research.

Run with the ghidra-bridge environment Python. Output and scratch projects
must stay under this worktree's ignored research-output directory. Use only
isolated scratch programs: defining missing functions can change that database.
Authoritative executables are read only; no inferred types or renames are applied.
"""
from __future__ import annotations

import argparse
import json
import re
import struct
from pathlib import Path

CANONICAL_SHA256 = {
    "2d4a3b02d3cdb740dfdf3c11002c0026837dc19ba8e5211ad9763b35eb06e15a",
    "611526d30be94879012efe54c56ceff428cb4d20a4bd49173370a4ebfe31a728",
    "13eaa642d0aabdfc47911a8606b02d9fc8d57d74328b36a0d3d618aadf1e0b78",
    "bf8aef32407eb6552c05045b8abef149f32983cedd9503b865069b444c5f96b4",
}


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    source = parser.add_mutually_exclusive_group(required=True)
    source.add_argument("--config", help="config pointing to an isolated scratch project")
    source.add_argument("--binary", type=Path, help="import a verified pristine corpus into a new scratch project")
    parser.add_argument("--project-name", default="BrokerCorpus")
    parser.add_argument("--output", required=True, type=Path)
    parser.add_argument("--function", action="append", default=[])
    parser.add_argument("--xref", action="append", default=[])
    parser.add_argument("--sentinel-literal", action="append", default=[], help="enumerate per-unit PUSH literal/MOV ECX string-ID initializers and their consumers")
    parser.add_argument("--call-target", action="append", default=[], help="find raw E8 rel32 candidates in executable blocks; not all candidates are validated instructions")
    parser.add_argument("--words", action="append", default=[], help="VA:count")
    parser.add_argument("--function-range", action="append", default=[], help="list existing entries within START:END; no automatic decompilation")
    parser.add_argument("--disassemble-missing", action="store_true", help="define requested entry points in the isolated scratch program only")
    args = parser.parse_args()
    addresses = args.function + args.xref + args.sentinel_literal + args.call_target
    addresses += [spec.split(":")[0] for spec in args.words]
    addresses += [part for spec in args.function_range for part in spec.split(":")]
    if any(not re.fullmatch(r"(?:0x)?[0-9a-fA-F]{1,8}", value) for value in addresses):
        parser.error("addresses must be 32-bit hexadecimal VAs")
    repo = Path(__file__).resolve().parents[2]
    output = args.output.resolve()
    if not output.is_relative_to(repo / "research-output"):
        parser.error("evidence output must be inside this worktree's research-output")
    output.mkdir(parents=True, exist_ok=True)
    import pyghidra
    from ghidra_ai_bridge.config import load_config

    if args.config:
        config = load_config(config_path=args.config)
        project_dir = Path(config.ghidra_project_dir).resolve()
        project_name = config.ghidra_project_name
        program_name = config.ghidra_program_name
        binary = None
    else:
        import hashlib
        binary = args.binary.resolve()
        if hashlib.sha256(binary.read_bytes()).hexdigest() not in CANONICAL_SHA256:
            parser.error("binary is not a verified pristine primary corpus")
        project_dir = output / "scratch-project"
        project_name = args.project_name
        program_name = binary.name
    if not project_dir.is_relative_to(repo / "research-output"):
        parser.error("scratch project must be inside this worktree's research-output")
    pyghidra.start()
    from ghidra.app.decompiler import DecompInterface
    from ghidra.util.task import ConsoleTaskMonitor

    with pyghidra.open_program(
        binary, project_location=project_dir,
        project_name=project_name,
        program_name=program_name,
        analyze=False, nested_project_location=False,
    ) as api:
        program = api.getCurrentProgram()
        if str(program.getExecutableSHA256()).lower() not in CANONICAL_SHA256:
            raise ValueError("scratch program identity is not a pristine primary corpus")
        space = program.getAddressFactory().getDefaultAddressSpace()
        functions = program.getFunctionManager()
        listing = program.getListing()
        references = program.getReferenceManager()
        memory = program.getMemory()
        decompiler = DecompInterface()
        decompiler.openProgram(program)
        manifest = {"program": program.getName(), "executable_sha256": program.getExecutableSHA256(),
                    "functions": [], "xrefs": {}, "words": {}}
        manifest["function_ranges"] = {}
        for spec in args.function_range:
            begin, end = (int(part, 16) for part in spec.split(":"))
            manifest["function_ranges"][spec] = [
                {"entry": str(f.getEntryPoint()), "name": f.getName()}
                for f in functions.getFunctions(True)
                if begin <= f.getEntryPoint().getOffset() < end
            ]

        def addr(text):
            return space.getAddress(int(text, 16))

        def refs_to(address):
            rows = []
            for ref in references.getReferencesTo(address):
                source = ref.getFromAddress()
                owner = functions.getFunctionContaining(source)
                rows.append({"from": str(source), "kind": str(ref.getReferenceType()),
                             "function": str(owner.getEntryPoint()) if owner else None})
            return rows

        for text in args.function:
            address = addr(text)
            function = functions.getFunctionAt(address)
            if function is None and args.disassemble_missing:
                api.disassemble(address)
                function = api.createFunction(address, "Scratch_" + text)
            if function is None:
                manifest["functions"].append({"requested": text, "error": "no exact function"})
                continue
            entry = str(function.getEntryPoint())
            result = decompiler.decompileFunction(function, 60, ConsoleTaskMonitor())
            c = result.getDecompiledFunction()
            code = c.getC() if c else str(result.getErrorMessage())
            (output / (entry + ".c.txt")).write_text("\n".join(line for line in code.splitlines() if line.strip()), encoding="utf-8")
            assembly = []
            outgoing = []
            for instruction in listing.getInstructions(function.getBody(), True):
                instruction_address = instruction.getAddress()
                targets = [str(ref.getToAddress()) for ref in references.getReferencesFrom(instruction_address)]
                assembly.append(str(instruction_address) + " " + str(instruction) + " ; " + ",".join(targets))
                outgoing.extend(targets)
            (output / (entry + ".asm.txt")).write_text("\n".join(assembly), encoding="utf-8")
            manifest["functions"].append({"requested": text, "entry": entry, "name": function.getName(),
                                           "callers": refs_to(address), "references_from": sorted(set(outgoing))})
        for text in args.xref:
            manifest["xrefs"][text] = refs_to(addr(text))
        manifest["sentinels"] = {}
        for text in args.sentinel_literal:
            records = []
            for ref in references.getReferencesTo(addr(text)):
                init = ref.getFromAddress()
                # The unanalysed DATA refs are frequently actual initializer
                # instructions. Validate opcodes rather than treating all as code.
                if (memory.getByte(init) & 255) != 0x68 or (memory.getByte(init.add(5)) & 255) != 0xb9:
                    continue
                target = space.getAddress(memory.getInt(init.add(6)) & 0xffffffff)
                consumers = [row for row in refs_to(target) if row["from"] != str(init.add(5))]
                records.append({"initializer": str(init), "string_id_object": str(target), "consumers": consumers})
            manifest["sentinels"][text] = records
        for spec in args.words:
            text, count = spec.split(":")
            start = addr(text)
            manifest["words"][spec] = [f"{memory.getInt(start.add(i * 4)) & 0xffffffff:08x}" for i in range(int(count))]
        manifest["raw_call_candidates"] = {}
        for text in args.call_target:
            wanted = int(text, 16)
            rows = []
            for block in memory.getBlocks():
                if not block.isExecute():
                    continue
                start = block.getStart()
                size = block.getSize()
                import jpype
                data = jpype.JArray(jpype.JByte)(int(size))
                memory.getBytes(start, data)
                payload = bytes((int(b) & 255) for b in data)
                cursor = payload.find(b"\xe8")
                while 0 <= cursor <= len(payload) - 5:
                    source = start.add(cursor)
                    displacement = struct.unpack_from("<i", payload, cursor + 1)[0]
                    if (source.getOffset() + 5 + displacement) & 0xffffffff == wanted:
                        instruction = listing.getInstructionAt(source)
                        owner = functions.getFunctionContaining(source)
                        rows.append({"from": str(source), "instruction": str(instruction) if instruction else None,
                                     "function": str(owner.getEntryPoint()) if owner else None})
                    cursor = payload.find(b"\xe8", cursor + 1)
            manifest["raw_call_candidates"][text] = rows
        decompiler.dispose()
        (output / "manifest.json").write_text(json.dumps(manifest, indent=2), encoding="utf-8")
        print(f"Exported {len(manifest['functions'])} requested functions to {output}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
