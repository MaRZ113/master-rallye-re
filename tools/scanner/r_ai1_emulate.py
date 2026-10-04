"""Execute the actual R-AI1 x86 selector in Ghidra's emulator, never in the game.

Use the installed ghidra-bridge Python and the latest Ghidra installation.
Temporary code/disassembly changes are rolled back; the project is not saved.
"""
from __future__ import annotations

import argparse
import json
import struct
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from r_ai1_mixed_class import (CONTINUE, SITE, SELECTOR, RETAIL_SHA256,
                              ignored_output, patch_ranges, verify_candidate)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--install", required=True, type=Path)
    parser.add_argument("--project", required=True, type=Path)
    parser.add_argument("--candidate", required=True, type=Path)
    parser.add_argument("--output", required=True, type=Path)
    args = parser.parse_args()
    manifest = verify_candidate(args.candidate.read_bytes())
    output = ignored_output(args.output)
    import pyghidra
    pyghidra.start(install_dir=args.install)
    from java.lang import Object
    from ghidra.program.flatapi import FlatProgramAPI
    from ghidra.app.emulator import EmulatorHelper
    project = pyghidra.open_project(args.project, "MasterRallye")
    consumer = Object()
    program = project.getProjectData().getFile("/MRallye.exe").getReadOnlyDomainObject(
        consumer, -1, pyghidra.task_monitor())
    transaction = None
    try:
        if str(program.getExecutableSHA256()) != RETAIL_SHA256:
            raise ValueError("Analyzed program differs from pristine retail")
        api = FlatProgramAPI(program)
        transaction = program.startTransaction("R-AI1 unsaved selector emulation")
        memory = program.getMemory()
        for patch in patch_ranges():
            if patch["va"] is None:
                continue
            address, code = api.toAddr(patch["va"]), patch["replacement"]
            if not memory.contains(address):
                block = memory.createInitializedBlock("R_AI1_TEMP", address, len(code),
                                                      0, pyghidra.task_monitor(), False)
                block.setExecute(True)
            api.clearListing(address, address.add(len(code) - 1))
            memory.setBytes(address, code)
            api.disassemble(address)
        # T1 ID0 player is excluded: selected IDs1..6, last pool item6.
        # Original exclusion slots have become driver/vehicle scratch9 and6.
        normal = [1, 3, 0, 9, 6]
        cases = []
        for selected in range(1, 7):
            for driver in range(10):
                for slot in (0, 1, 2, 3):
                    cases.append((slot, selected, driver, normal, slot == 1))
        for arg, bad in ((0, 0), (0, 2), (1, 0), (1, 2), (1, 4),
                         (2, 1), (2, 2), (2, 4)):
            values = list(normal)
            values[arg] = bad
            cases.append((1, 1, 9, values, False))
        rows = []
        for n, (slot, selected, driver, values, changes) in enumerate(cases):
            emu = EmulatorHelper(program)
            try:
                stack = 0x007F1000
                initial = bytearray(b"\xa5" * 0xA0)
                struct.pack_into("<II", initial, 0x14, selected, driver)
                for offset, value in zip((0x84, 0x88, 0x8C, 0x90, 0x94), values):
                    struct.pack_into("<I", initial, offset, value & 0xFFFFFFFF)
                emu.writeMemory(api.toAddr(stack), bytes(initial))
                registers = {"EAX": 0xDEADBEEF, "ECX": 0x11112222, "EDX": 0x33334444,
                             "EBX": 0x55556666, "EBP": 0x77778888, "ESI": slot,
                             "EDI": 0x9999AAAA, "ESP": stack}
                # Sleigh models these flag registers independently of its eflags
                # scratch register; PUSHFD packs them and omits reserved bit 1.
                flags = (0x202, 0x246, 0x297)[n % 3]
                registers.update({name: int(bool(flags & (1 << bit))) for name, bit in
                                  (("CF", 0), ("PF", 2), ("AF", 4), ("ZF", 6),
                                   ("SF", 7), ("TF", 8), ("IF", 9), ("DF", 10), ("OF", 11))})
                for name, value in registers.items():
                    emu.writeRegister(name, value)
                emu.writeRegister("EIP", SITE)
                steps = 0
                while emu.getExecutionAddress().getOffset() != CONTINUE:
                    if steps > 40 or not emu.step(pyghidra.task_monitor()):
                        raise ValueError(f"Emulator failed: {emu.getLastError()}")
                    steps += 1
                chosen = 14 if changes else selected
                struct.pack_into("<I", initial, 0x14, chosen)
                if bytes(emu.readMemory(api.toAddr(stack), len(initial))) != bytes(initial):
                    raise ValueError("Selector changed unrelated locals/arguments/DriverID")
                if bytes(emu.readMemory(api.toAddr(stack - 4), 4)) != struct.pack("<I", chosen):
                    raise ValueError("Displaced PUSH did not preserve the stock argument")
                expected = {**registers, "EAX": chosen, "ESP": stack - 4}
                for name, value in expected.items():
                    actual = int(str(emu.readRegister(name))) & 0xFFFFFFFF
                    if actual != value:
                        raise ValueError(f"Register/flags changed unexpectedly: {name}: {actual:#x} != {value:#x}")
                rows.append({"slot": slot, "stock_id": selected, "driver": driver,
                             "args": values, "output_id": chosen, "steps": steps})
            finally:
                emu.dispose()
        output.parent.mkdir(parents=True, exist_ok=True)
        output.write_text(json.dumps({"status": "STATIC_X86_EMULATION_PASS",
                                      "runtime_game_test": False, "cases": len(rows),
                                      "candidate_sha256": manifest["output_sha256"],
                                      "project_saved": False, "rows": rows}, indent=2) + "\n")
        print("Actual x86 selector:", len(rows), "cases PASS; game runtime untested")
    finally:
        if transaction is not None:
            program.endTransaction(transaction, False)
        program.release(consumer)
        project.close()


if __name__ == "__main__":
    main()
