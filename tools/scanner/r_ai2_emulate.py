"""Bounded native five-car setup/allocation/cleanup emulation; never runs the game."""
from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
import r_ai2_capacity as c
from r_ai1_hardening_emulate import Machine
from r_ai1_emulate import emulate_general


class BoundedMachine(Machine):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.blocks = []
        self.native_allocations = []
        self.frees = []

    def alloc(self, data):
        left = super().alloc(b"\xa5" * 16 + data + b"\xa5" * 16)
        self.blocks.append((left + 16, len(data)))
        return left + 16

    def guards(self):
        for ptr, size in self.blocks:
            for address in (ptr - 16, ptr + size):
                if bytes(self.emu.readMemory(self.api.toAddr(address), 16)) != b"\xa5" * 16:
                    raise ValueError("Native write exceeded bounded allocation")

    def execute_bounded(self, boundary, pop=0):
        self.steps = 0
        while self.emu.getExecutionAddress().getOffset() != self.stop:
            pc = self.emu.getExecutionAddress().getOffset(); self.visited.add(pc)
            if not boundary(pc) and not self.emu.step(self.monitor):
                raise ValueError(f"x86 failed at {pc:#x}: {self.emu.getLastError()}")
            self.steps += 1
            if self.steps > 30000:
                raise ValueError(f"Instruction budget at {pc:#x}")
        for name, value in self.saved.items():
            if self.reg(name) != value:
                raise ValueError("Callee-saved register changed: " + name)
        if self.reg("ESP") != self.stack + 4 + pop or self.read(0) != 0:
            raise ValueError("Stack/SEH restoration failed")
        self.guards()

    def heap_boundary(self, pc):
        sp = self.reg("ESP")
        if pc == 0x5C1CB4:
            size = self.read(sp + 4)
            if size > 4096:
                raise ValueError("Unexpected allocation size")
            ptr = self.alloc(bytes(size)); self.native_allocations.append((ptr, size)); self.ret(ptr)
        elif pc == 0x5B4C00:
            if self.read(sp + 4): self.frees.append(self.read(sp + 4))
            self.ret()
        else:
            return False
        return True


def setup(program, api, monitor, state, direct=False):
    m = BoundedMachine(program, api, monitor, c.CAVE if direct else 0x47B780)
    writes, counts, original_reads = [], [], []
    registry = m.alloc(bytes(0x1000)); quick = m.alloc(bytes(0x100)); race = m.alloc(bytes(0x100))
    m.write(registry + state["player"] * 0x34 + 0xC, 0 if state["player"] < 7 else 1)
    m.put("ECX", quick)
    preserved = {"ECX": quick, "EDX": 0x12345678}
    m.put("EDX", preserved["EDX"])
    flags = {"CF": 1, "ZF": 0, "SF": 1, "OF": 0, "PF": 1, "AF": 0, "DF": 0}
    for name, value in flags.items(): m.put(name, value)
    getters = {0x4AE090: "mode", 0x4AE2D0: "split", 0x4AE0F0: "ghost", 0x4AE030: "track"}
    def boundary(pc):
        sp = m.reg("ESP")
        if pc == 0x4AE700: m.ret(quick)
        elif pc == 0x4ADA50: m.ret(race)
        elif pc == 0x4AE150:
            original_reads.append(state["opponents"]); m.ret(state["opponents"])
        elif pc in getters: m.ret(int(state[getters[pc]]))
        elif pc == 0x4ADFB0: m.ret(state["player"], 4)
        elif pc == 0x45A3C0: m.ret(registry)
        elif pc in (0x4AE1B0, 0x4AE210): m.ret(0)
        elif pc in (0x4ACAF0, 0x4ACC10):
            writes.append((pc, m.read(sp + 4), m.read(sp + 8))); m.ret(None, 8)
        elif pc in (0x4AC2B0, 0x4AC220, 0x4AC1C0, 0x4AC500, 0x4AC3D0, 0x4AC4D0):
            writes.append((pc, m.read(sp + 4))); m.ret(None, 4)
        elif pc == 0x4AC660: m.ret(state["player"], 4)
        elif pc == 0x4AC730: m.ret(0 if state["player"] < 7 else 1, 4)
        elif pc == 0x458950:
            # Singleton getter consumes none of the five already-pushed chooser arguments.
            counts.append(("chooser_owner", m.read(sp + 4), m.read(sp + 8))); m.ret(0x720000)
        elif pc == 0x458090:
            counts.append(("chooser", m.read(sp + 4), m.read(sp + 8))); m.ret(None, 20)
        else: return False
        return True
    try:
        m.execute_bounded(boundary)
        expected = c.effective_opponents(**state)
        if direct:
            if m.reg("EAX") != expected or any(m.reg(n) != v for n, v in preserved.items()) or any(m.reg(n) != v for n, v in flags.items()):
                raise ValueError("Getter result/register/flags preservation failed")
            if original_reads != [state["opponents"]]: raise ValueError("Original getter bypassed")
        else:
            if (0x4AC3D0, expected + 1) not in writes or original_reads != [state["opponents"]] * 2:
                raise ValueError("Native NumCars setup mismatch")
            if state["mode"] == 2 and not state["split"] and counts != [("chooser_owner", 1, expected), ("chooser", 1, expected)]:
                raise ValueError("Native AI count/first slot mismatch")
        return {"state": state, "direct": direct, "writes": writes, "chooser_counts": counts,
                "original_reads": original_reads, "steps": m.steps}
    finally: m.emu.dispose()


def vector_growth(program, api, monitor):
    m = BoundedMachine(program, api, monitor, 0x43BB70)
    vec, value = m.alloc(bytes(16)), m.alloc(bytes(4))
    lengths = []
    try:
        for n in range(5):
            m.write(value, n); m.put("ECX", vec); m.put("ESP", m.stack); m.put("EIP", 0x43BB70)
            for i, v in enumerate((m.stop, m.read(vec + 8), 1, value)): m.write(m.stack + i * 4, v)
            m.execute_bounded(m.heap_boundary, pop=12)
            begin, end, capacity = (m.read(vec + i) for i in (4, 8, 12))
            if (end - begin) // 4 != n + 1 or end > capacity or [m.read(begin + i * 4) for i in range(n + 1)] != list(range(n + 1)):
                raise ValueError("Native vector indexing/growth mismatch")
            lengths.append(n + 1)
        return {"owner": "43BB70", "lengths": lengths, "allocation_sizes": [size for _, size in m.native_allocations],
                "redzones_intact": True}
    finally: m.emu.dispose()


def cleanup(program, api, monitor, ai=False):
    count = 4 if ai else 5
    m = BoundedMachine(program, api, monitor, 0x42A6B0 if ai else 0x43E020)
    obj = m.alloc(bytes(0xC8 if ai else 0x80)); vec = m.alloc(bytes(count * 4))
    items = [m.alloc(bytes(0xD4 if ai else 0x2C)) for _ in range(count)]
    for n, ptr in enumerate(items): m.write(vec + n * 4, ptr)
    begin = 0x88 if ai else 0x18
    m.write(obj + begin, vec); m.write(obj + begin + 4, vec + count * 4); m.write(obj + begin + 8, vec + count * 4)
    m.put("ECX", obj); destroyed = []
    def boundary(pc):
        if m.heap_boundary(pc): return True
        if pc == (0x42CDA0 if ai else 0x4436C0): destroyed.append(m.reg("ECX")); m.ret()
        elif ai and pc in (0x429F60, 0x42B4F0): m.ret()  # unrelated manager configuration collections
        else: return False
        return True
    try:
        m.execute_bounded(boundary)
        if destroyed != items or m.frees != items + [vec] or m.read(obj + begin) != 0 or m.read(obj + begin + 4) != 0:
            raise ValueError("Native destruction skipped/aliased a participant")
        return {"owner": "42A6B0" if ai else "43E020", "destroyed_indices": list(range(1, 5)) if ai else list(range(5)),
                "redzones_intact": True, "container_freed": True}
    finally: m.emu.dispose()


def progress_init(program, api, monitor, count):
    m = BoundedMachine(program, api, monitor, 0x48B520, (0,))
    obj = m.alloc(bytes(0x40)); m.put("ECX", obj)
    paths = []; current = ""; key_id = 0
    def boundary(pc):
        nonlocal current, key_id
        sp = m.reg("ESP")
        if m.heap_boundary(pc): return True
        if pc == 0x4ADA50: m.ret(0x720000)
        elif pc == 0x4AC040: m.ret(count)
        elif pc == 0x5C20BA:
            dest, fmt = m.read(sp + 4), m.text(m.read(sp + 8))
            text = fmt % m.read(sp + 12); m.emu.writeMemory(api.toAddr(dest), text.encode() + b"\0"); m.ret(len(text))
        elif pc == 0x4D0580:
            current = m.text(m.read(sp + 4)); paths.append(current); key_id += 1
            m.write(m.reg("ECX"), key_id); m.ret(m.reg("ECX"), 4)
        elif pc == 0x4D8EC0: m.ret(0x720000)
        elif pc == 0x4D7470: m.ret(0, 4)
        elif pc == 0x4D7ED0: m.ret(None, 8)
        elif pc == 0x4E51C0: m.ret(0x720000)
        elif pc == 0x4E4D20: m.ret(0, 4)
        else: return False
        return True
    try:
        m.execute_bounded(boundary, pop=4)
        sizes = [size for _, size in m.native_allocations]
        if sizes != [count] + [count * 4] * 6:
            raise ValueError("Progress physical allocation size mismatch: " + str(sizes))
        indices = sorted({int(match[1]) for path in paths if (match := re.search(r"Race/Car(\d+)/", path))})
        if indices != list(range(count)): raise ValueError("Progress init does not cover exact participant indices")
        # Stock destructor frees the byte array and four key/data arrays. Two
        # other allocated key arrays are retained/leaked by stock; no fixed-four
        # indexing is involved, and R-AI2 does not redesign their ownership.
        m.put("EIP", 0x48ADC0); m.put("ESP", m.stack); m.write(m.stack, m.stop); m.put("ECX", obj)
        m.execute_bounded(m.heap_boundary)
        if len(m.frees) != 5: raise ValueError("Progress destructor behavior changed")
        return {"owner": "48B520/48ADC0", "num_cars": count, "indices": indices, "allocation_sizes": sizes,
                "redzones_intact": True, "freed_blocks": len(m.frees), "stock_retained_key_arrays": 2}
    finally: m.emu.dispose()


def result_records(program, api, monitor, count):
    """Native allocation/append/rank loop; finish-time sorting is a boundary."""
    m = BoundedMachine(program, api, monitor, 0x47D6D0)
    obj = m.alloc(bytes(0x40)); m.put("ECX", obj)
    ranking = []; sort_calls = []
    def boundary(pc):
        sp = m.reg("ESP")
        if m.heap_boundary(pc): return True
        if pc == 0x4ADA50: m.ret(0x720000)
        elif pc == 0x4AC040: m.ret(count)
        elif pc in (0x4AC7B0, 0x4AC660, 0x4AC7F0):
            index = m.read(sp + 4)
            if not 0 <= index < count: raise ValueError("Result getter outside participant count")
            value = (30 if index == 0 else index - 1) if pc == 0x4AC7B0 else index if pc == 0x4AC660 else 0
            m.ret(value, 4)
        elif pc == 0x47D100:
            sort_calls.append(m.read(sp + 4)); m.ret(None, 4)
        elif pc == 0x4B0AF0: m.ret(0x720000)  # position publisher singleton, no arguments consumed
        elif pc == 0x4B08B0:
            ranking.append((m.read(sp + 4), m.read(sp + 8))); m.ret(None, 8)
        else: return False
        return True
    try:
        m.execute_bounded(boundary)
        begin, end, capacity = (m.read(obj + offset) for offset in (0x2C, 0x30, 0x34))
        if end - begin != count * 4 or end > capacity or ranking != [(i, i + 1) for i in range(count)] or sort_calls != [0]:
            raise ValueError("Results vector/rank publication omitted a participant")
        records = [m.read(begin + i * 4) for i in range(count)]
        if len(set(records)) != count: raise ValueError("Result record alias")
        for i, ptr in enumerate(records):
            expected = (i, 30 if i == 0 else i - 1, i, i)
            if tuple(m.read(ptr + offset) for offset in (0, 4, 8, 0x14)) != expected:
                raise ValueError("Result record identity/index mismatch")
        if sum(size == 0x1C for _, size in m.native_allocations) != count:
            raise ValueError("Result physical record allocation count mismatch")
        return {"owner": "47D6D0/47C6C0/47DBE0", "num_cars": count, "indices": list(range(count)),
                "rank_publication": ranking, "allocation_sizes": [size for _, size in m.native_allocations],
                "redzones_intact": True, "finish_time_sort_boundary": True, "result_record_cleanup_not_emulated": True}
    finally: m.emu.dispose()


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--install", required=True, type=Path); parser.add_argument("--project", required=True, type=Path)
    parser.add_argument("--source", required=True, type=Path); parser.add_argument("--candidate", required=True, type=Path)
    parser.add_argument("--output", required=True, type=Path); args = parser.parse_args()
    source = args.source.read_bytes(); c.build(source); c.verify(args.candidate.read_bytes())
    import pyghidra
    pyghidra.start(install_dir=args.install)
    from java.lang import Object
    from ghidra.program.flatapi import FlatProgramAPI
    project = pyghidra.open_project(args.project, "MasterRallye"); consumer = Object(); program = None; transaction = None
    try:
        program = project.getProjectData().getFile("/MRallye.exe").getReadOnlyDomainObject(consumer, -1, pyghidra.task_monitor())
        if str(program.getExecutableSHA256()) != c.RETAIL_SHA256: raise ValueError("Wrong pristine program")
        api = FlatProgramAPI(program); monitor = pyghidra.task_monitor(); transaction = program.startTransaction("R-AI2 unsaved five-car proof")
        chooser = emulate_general(program, api, monitor, source, five_car=True)
        for row in c.ranges():
            if row["va"] is None: continue
            addr = api.toAddr(row["va"]); data = row["replacement"]; memory = program.getMemory()
            if not memory.contains(addr):
                block = memory.createInitializedBlock("R_AI2_TEMP_" + str(addr), addr, len(data), 0, monitor, False); block.setExecute(True)
            api.clearListing(addr, addr.add(len(data) - 1)); memory.setBytes(addr, data); api.disassemble(addr)
        normal = dict(opponents=3, mode=2, split=False, ghost=0, player=0, track=10)
        states = [normal] + [{**normal, key: value} for key, value in
                            (("opponents", 0), ("opponents", 1), ("opponents", 2), ("mode", 1), ("mode", 3),
                             ("split", True), ("ghost", 1), ("player", 1), ("player", 7), ("track", 9))]
        hooks = [setup(program, api, monitor, state, direct=True) for state in states]
        hooks += [setup(program, api, monitor, state) for state in states if not state["split"]]
        storage = [vector_growth(program, api, monitor), cleanup(program, api, monitor), cleanup(program, api, monitor, ai=True),
                   progress_init(program, api, monitor, 4), progress_init(program, api, monitor, 5),
                   result_records(program, api, monitor, 4), result_records(program, api, monitor, 5)]
        result = {"status": "STATIC_FIVE_CAR_EMULATION_PASS", "runtime_game_test": False, "project_saved": False,
                  "source_sha256": c.RETAIL_SHA256, "candidate_sha256": c.CANDIDATE_SHA256,
                  "cases": chooser["cases"] + len(hooks) + len(storage), "chooser": chooser, "setup": hooks, "storage": storage,
                  "limits": "CPU setup/chooser/vector/progress-init/destruction/result allocation and rank loop with explicit Broker/heap/scene/finish-time-sort boundaries; no game physics or rendering"}
        output = c.ignored_output(args.output); output.parent.mkdir(parents=True, exist_ok=True)
        output.write_text(json.dumps(result, indent=2) + "\n"); print(result["status"], result["cases"], "cases")
    finally:
        if program is not None:
            if transaction is not None: program.endTransaction(transaction, False)
            program.release(consumer)
        project.close()


if __name__ == "__main__": main()
