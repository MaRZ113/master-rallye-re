"""Execute the actual R-AI1 x86 selector in Ghidra's emulator, never in the game.

Use the installed ghidra-bridge Python and the latest Ghidra installation.
Temporary code/disassembly changes are rolled back; the project is not saved.
"""
from __future__ import annotations

import argparse
import itertools
import json
import struct
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from r_ai1_mixed_class import (CONTINUE, SITE, SELECTOR, RETAIL_SHA256,
                              ignored_output, patch_ranges, verify_candidate,
                              general_ranges, build_general)


def emulate_general(program, api, monitor, source):
    """Execute the full native chooser, with explicit synthetic OS/data boundaries.

    Actual class cases, pool draw, vector erase, both shuffles, CRT rand and
    driver selection execute as x86. Broker/heap/TLS and game range outputs
    are bounded stubs. This is neither a game run nor a physics emulation.
    """
    from ghidra.app.emulator import EmulatorHelper
    build_general(source, "stock")  # exact source/PE gate before temporary edits
    memory = program.getMemory()
    patched = general_ranges()
    def install(policy):
        ranges = [] if policy == "stock" else general_ranges(policy)
        for row in patched:
            if row["va"] is None:
                continue
            address = api.toAddr(row["va"])
            if not memory.contains(address):
                block = memory.createInitializedBlock("R_AI11_TEMP", address, 512, 0, monitor, False)
                block.setExecute(True)
            code = row["original"] if policy == "stock" else next(
                item["replacement"] for item in ranges if item["va"] == row["va"])
            api.clearListing(address, address.add(511 if row["va"] == SELECTOR else len(code) - 1))
            memory.setBytes(address, code)
            api.disassemble(address)

    def run(player, draws, first=1, count=3, mode=2, seed=12345, unlocked=False):
        emu = EmulatorHelper(program)
        def reg(name):
            return int(str(emu.readRegister(name))) & 0xffffffff
        def putreg(name, value):
            emu.writeRegister(name, value & 0xffffffff)
        def read(address):
            return struct.unpack("<I", bytes(emu.readMemory(api.toAddr(address), 4)))[0]
        def write(address, value):
            emu.writeMemory(api.toAddr(address), struct.pack("<I", value & 0xffffffff))
        def ret(value=None, pop=0):
            sp = reg("ESP")
            destination = read(sp)
            if value is not None:
                putreg("EAX", value)
            putreg("ESP", sp + 4 + pop)
            putreg("EIP", destination)
        participants = {n: {"CarID": player if n == 0 else -1,
                            "CarClass": player // 7 if n == 0 else -1,
                            "DriverID": 30 if n == 0 else -1} for n in range(4)}
        writes, ranges, allocations = [], [], {}
        next_heap = 0x00780000
        draw_iter = iter(draws)
        rng = seed
        try:
            stack, sentinel, registry = 0x007f1000, 0x007ffff0, 0x00710000
            emu.writeMemory(api.toAddr(stack - 1024), bytes(2048))
            for offset, value in enumerate((sentinel, first, count, player // 7, player, -1)):
                write(stack + offset * 4, value)
            emu.writeMemory(api.toAddr(0), bytes(16))
            for n in range(25):
                write(registry + n * 0x34 + 0xc, 0 if n < 7 else 1 if n < 14 else 2)
            original = {"EBX": 0x11223344, "EBP": 0x22334455,
                        "ESI": 0x33445566, "EDI": 0x44556677}
            for name, value in {**original, "ESP": stack, "EIP": 0x458090,
                                "FS_OFFSET": 0, "DF": 0}.items():
                putreg(name, value)
            steps = 0
            executed = set()
            while emu.getExecutionAddress().getOffset() != sentinel:
                pc = emu.getExecutionAddress().getOffset()
                executed.add(pc)
                sp = reg("ESP")
                if pc == 0x4ada50:
                    ret(0x00720000)
                elif pc == 0x4abe90:
                    ret(mode)
                elif pc == 0x4ac660:
                    slot = read(sp + 4)
                    if slot not in participants:
                        raise ValueError("Getter escaped existing four slots")
                    ret(participants[slot]["CarID"], 4)
                elif pc in (0x4acaf0, 0x4acc10, 0x4accd0):
                    slot, value = read(sp + 4), read(sp + 8)
                    if slot not in participants:
                        raise ValueError("Publisher escaped existing four slots")
                    key = {0x4acaf0: "CarID", 0x4acc10: "CarClass", 0x4accd0: "DriverID"}[pc]
                    participants[slot][key] = value
                    writes.append((slot, key, value))
                    ret(None, 8)
                elif pc == 0x45a3c0:
                    ret(registry)
                elif pc == 0x4b0310:
                    ret(0x00730000, 4)
                elif pc == 0x4afb70:
                    ret(int(unlocked))
                elif pc == 0x4d1e90:
                    ret(0x00740000)
                elif pc == 0x4d1df0:
                    low, high = read(sp + 4), read(sp + 8)
                    if (low, high) == (0, 3):
                        value = next(draw_iter)
                    elif (low, high) == (0, 65535):
                        # Synthetic seed stimuli, matching the native positive
                        # state recurrence; FP instruction rounding is a boundary.
                        rng = (rng * 48271) % 2147483647
                        value = ((rng & 0xffffff) * 65535) // (1 << 24)
                    else:
                        raise ValueError(f"Unexpected native range: {low}, {high}")
                    ranges.append((low, high, value))
                    ret(value, 8)
                elif pc == 0x5c8471:
                    ret(0x00750000)  # actual srand/rand use this synthetic TLS state
                elif pc in (0x414920, 0x411c90):
                    vec = reg("ECX")
                    position = read(sp + 4)
                    count_insert = 1 if pc == 0x414920 else read(sp + 8)
                    value_ptr = read(sp + (8 if pc == 0x414920 else 12))
                    if count_insert != 1:
                        raise ValueError("Unexpected vector insert size")
                    begin, end = read(vec + 4), read(vec + 8)
                    if not begin:
                        begin = end = next_heap
                        next_heap += 512
                        allocations[vec] = begin
                        emu.writeMemory(api.toAddr(begin), bytes(512))
                        write(vec + 4, begin)
                        write(vec + 12, begin + 512)
                        position = begin
                    if position < begin or position > end or end >= begin + 508:
                        raise ValueError("Vector insert escaped synthetic allocation")
                    value = read(value_ptr)
                    for cursor in range(end, position, -4):
                        write(cursor, read(cursor - 4))
                    write(position, value)
                    write(vec + 8, end + 4)
                    ret(position, 8 if pc == 0x414920 else 12)
                elif pc == 0x411670:
                    ret()  # no OS allocator/free, cleanup control flow still executes
                else:
                    # Do not silently skip unknown calls; a bounded instruction
                    # budget also catches paths leaving the reconstructed chooser.
                    if not emu.step(monitor):
                        raise ValueError(f"x86 failed at {pc:#x}: {emu.getLastError()}")
                steps += 1
                if steps > 20000:
                    raise ValueError(f"x86 instruction budget at {pc:#x}")
            for name, value in original.items():
                if reg(name) != value:
                    raise ValueError(f"Callee-saved {name} was not restored")
            if reg("ESP") != stack + 24 or read(0) != 0:
                raise ValueError("RET/stack/SEH restoration failed")
            return {"participants": participants, "writes": writes, "rng": ranges,
                    "steps": steps, "executed_driver": 0x458980 in executed,
                    "executed_vehicle_shuffle": 0x450580 in executed,
                    "executed_driver_shuffle": 0x458a80 in executed,
                    "executed_crt_rand": 0x5c37b8 in executed}
        except Exception as exc:
            raise ValueError(f"player={player}, draws={draws}, first={first}, count={count}, mode={mode}: {exc}") from exc
        finally:
            emu.dispose()

    rows = []
    install("stock")
    baselines = {}
    guards = [(1, 3, 1), (1, 3, 3), (1, 3, 14), (2, 2, 2), (1, 2, 2), (1, 0, 2), (0, 3, 2)]
    for player in (0, 7, 14):
        result = run(player, ())
        assert all(result["participants"][n]["CarClass"] == player // 7 for n in (1, 2, 3))
        rows.append({"policy": "stock", "player": player, "result": result})
    for guard in guards:
        baselines[guard] = run(0, (), *guard)
    for policy in ("diverse", "mixed"):
        install(policy)
        plans = [(2, 1, 0)] if policy == "diverse" else list(itertools.product(range(3), repeat=3))
        for player in (0, 7, 14):
            for plan in plans:
                result = run(player, plan)
                cars = result["participants"]
                if cars[0] != {"CarID": player, "CarClass": player // 7, "DriverID": 30}:
                    raise ValueError("Human participant changed")
                if tuple(cars[n]["CarClass"] for n in (1, 2, 3)) != plan:
                    raise ValueError("Per-slot class input was not preserved")
                if len({car["CarID"] for car in cars.values()}) != 4:
                    raise ValueError("CarIDs alias across a rebuilt pool")
                if len({cars[n]["DriverID"] for n in (1, 2, 3)}) != 3:
                    raise ValueError("Driver pool was reinitialized/aliased")
                if any(not 0 <= cars[n]["DriverID"] < 10 for n in (1, 2, 3)):
                    raise ValueError("Invalid driver")
                if not all(result[key] for key in ("executed_driver", "executed_vehicle_shuffle",
                                                  "executed_driver_shuffle", "executed_crt_rand")):
                    raise ValueError("Native RNG/bookkeeping not executed")
                if policy == "mixed" and [call[2] for call in result["rng"] if call[:2] == (0, 3)] != list(plan):
                    raise ValueError("Class RNG was not called independently once per AI")
                rows.append({"policy": policy, "player": player, "plan": plan, "result": result})
        if policy == "mixed":
            for guard in guards:
                actual = run(0, (), *guard)
                for key in ("participants", "writes", "rng"):
                    if actual[key] != baselines[guard][key]:
                        raise ValueError(f"Guard changed stock {key}: {guard}")
                rows.append({"policy": "mixed", "guard": guard, "stock_equal": True, "result": actual})
    return {"status": "STATIC_NATIVE_CHOOSER_EMULATION_PASS", "runtime_game_test": False,
            "cases": len(rows), "source_sha256": RETAIL_SHA256, "project_saved": False,
            "boundaries": ["Broker", "heap insert/free", "TLS pointer", "game range outputs"],
            "rows": rows}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--install", required=True, type=Path)
    parser.add_argument("--project", required=True, type=Path)
    parser.add_argument("--candidate", type=Path)
    parser.add_argument("--general-source", type=Path)
    parser.add_argument("--output", required=True, type=Path)
    args = parser.parse_args()
    if bool(args.candidate) == bool(args.general_source):
        parser.error("Choose --candidate (legacy) or --general-source (R-AI1.1)")
    manifest = verify_candidate(args.candidate.read_bytes()) if args.candidate else None
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
        if args.general_source:
            result = emulate_general(program, api, pyghidra.task_monitor(), args.general_source.read_bytes())
            output.parent.mkdir(parents=True, exist_ok=True)
            output.write_text(json.dumps(result, indent=2) + "\n")
            print("Native chooser:", result["cases"], "cases PASS; game runtime untested")
            return
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
