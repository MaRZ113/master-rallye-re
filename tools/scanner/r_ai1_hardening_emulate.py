"""Execute native Loading and Broker Dump in a read-only pristine Ghidra project.

OS/stat, allocation, enString intern lookup and log sink are synthetic boundaries.
The native decoder, branches, list iteration, metadata, braces and cleanup execute.
This does not run the game or recover from an access violation.
"""
from __future__ import annotations

import argparse
import json
import re
import struct
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
import r_ai1_hardening as h
from r_ai1_observe import load_profile


def install(program, api, monitor, hardened):
    memory = program.getMemory()
    for row in h.hardening_ranges():
        if row["va"] is None:
            continue
        address = api.toAddr(row["va"])
        code = row["replacement"] if hardened else row["original"]
        if not memory.contains(address):
            block = memory.createInitializedBlock("R_AI11_GUARD_" + str(address), address,
                                                  len(code), 0, monitor, False)
            block.setExecute(True)
        api.clearListing(address, address.add(len(code) - 1))
        memory.setBytes(address, code)
        api.disassemble(address)


class Machine:
    def __init__(self, program, api, monitor, start, arguments=()):
        from ghidra.app.emulator import EmulatorHelper
        self.emu, self.api, self.monitor = EmulatorHelper(program), api, monitor
        self.stack, self.stop, self.heap = 0x7F1000, 0x7FFFF0, 0x780000
        self.steps, self.visited = 0, set()
        self.emu.writeMemory(api.toAddr(self.stack - 2048), bytes(4096))
        self.emu.writeMemory(api.toAddr(0), bytes(16))
        self.saved = {"EBX": 0x11223344, "EBP": 0x22334455,
                      "ESI": 0x33445566, "EDI": 0x44556677}
        for name, value in {**self.saved, "ESP": self.stack, "EIP": start,
                            "FS_OFFSET": 0, "DF": 0}.items():
            self.put(name, value)
        for n, value in enumerate((self.stop, *arguments)):
            self.write(self.stack + n * 4, value)

    def reg(self, name):
        return int(str(self.emu.readRegister(name))) & 0xFFFFFFFF

    def put(self, name, value):
        self.emu.writeRegister(name, value & 0xFFFFFFFF)

    def read(self, address):
        return struct.unpack("<I", bytes(self.emu.readMemory(self.api.toAddr(address), 4)))[0]

    def write(self, address, value):
        self.emu.writeMemory(self.api.toAddr(address), struct.pack("<I", value & 0xFFFFFFFF))

    def alloc(self, data):
        address = self.heap
        self.heap += (len(data) + 15) // 16 * 16
        self.emu.writeMemory(self.api.toAddr(address), data)
        return address

    def cstring(self, text):
        return self.alloc(text.encode("cp1252") + b"\0")

    def text(self, address):
        chars = bytearray()
        for n in range(4096):
            byte = bytes(self.emu.readMemory(self.api.toAddr(address + n), 1))[0]
            if byte == 0:
                return chars.decode("cp1252")
            chars.append(byte)
        raise ValueError("Unterminated synthetic/native string")

    def ret(self, value=None, pop=0):
        sp = self.reg("ESP")
        target = self.read(sp)
        if value is not None:
            self.put("EAX", value)
        self.put("ESP", sp + 4 + pop)
        self.put("EIP", target)

    def execute(self, boundary):
        while self.emu.getExecutionAddress().getOffset() != self.stop:
            pc = self.emu.getExecutionAddress().getOffset()
            self.visited.add(pc)
            if not boundary(pc) and not self.emu.step(self.monitor):
                raise ValueError(f"Native x86 failed at {pc:#x}: {self.emu.getLastError()}")
            self.steps += 1
            if self.steps > 20000:
                raise ValueError(f"Instruction budget at {pc:#x}")
        for name, value in self.saved.items():
            if self.reg(name) != value:
                raise ValueError(f"Callee-saved register changed: {name}")
        if self.reg("ESP") != self.stack + 8 or self.read(0) != 0:
            raise ValueError("Stack/RET4/SEH restoration failed")


def loading(program, api, monitor, counter, stat_result, size):
    m = Machine(program, api, monitor, 0x464E40, (0,))
    writes, checks = [], []
    obj = m.alloc(bytes(32))
    m.put("ECX", obj)
    m.write(0x6F6030, counter)
    m.write(0x6FDF90, ord("d"))  # native default from 5B0660; optional registry CDDrive overrides it
    def boundary(pc):
        sp = m.reg("ESP")
        if pc == 0x5C1CB4:
            m.ret(m.alloc(bytes(m.read(sp + 4))))
        elif pc == 0x45D610:
            m.ret(m.reg("ECX"), 4)
        elif pc == 0x5C39D5:
            name, stat_buffer = m.text(m.read(sp + 4)), m.read(sp + 8)
            if name != "d:\\SETUP.DLL":
                raise ValueError("Native media decode changed: " + name)
            checks.append(name)
            m.write(stat_buffer + 0x14, size)
            m.ret(stat_result)
        elif pc == 0x4D0580:
            m.write(m.reg("ECX"), m.read(sp + 4))
            m.ret(m.reg("ECX"), 4)
        elif pc == 0x4D8EC0:
            m.ret(0x720000)  # parameters remain for the following Broker setter
        elif pc in (0x4D8000, 0x4D7AA0):
            key = m.text(m.read(m.read(sp + 4)))
            writes.append((key, m.read(sp + 8)))
            m.ret(None, 8)
        elif pc == 0x4ADA50:
            m.ret(0x720000)
        elif pc == 0x4AC1C0:
            writes.append(("Race/Type", m.read(sp + 4)))
            m.ret(None, 4)
        else:
            return False
        return True
    try:
        m.execute(boundary)
        if m.read(0x6F6030) != counter + 1:
            raise ValueError("Loading counter changed")
        return {"writes": writes, "checks": checks, "steps": m.steps}
    finally:
        m.emu.dispose()


def dump(program, api, monitor, points, xml=None):
    m = Machine(program, api, monitor, 0x601D00)
    calls, fragments = [], []
    def wrapper(text):
        return m.alloc(struct.pack("<I", m.cstring(text)))
    def list_value(items):
        if items is None:
            return 0
        array = m.alloc(b"".join(struct.pack("<I", m.cstring(item)) for item in items) or bytes(4))
        return m.alloc(struct.pack("<IIII", 0, array, array + len(items) * 4, array + len(items) * 4))
    fixtures = [("Frontend/RaceResults/ResultsType", 4, wrapper("RACE TIME")),
                ("Frontend/RaceResults/NameList", 9, list_value(["Human", "AI1", "AI2", "AI3"])),
                ("Frontend/RaceResults/TimeList", 9, list_value(["03:10", "03:11", "03:12", "03:13"])),
                ("Frontend/RaceResults/PointsList", 9, list_value(points))]
    if xml is not None:
        # XmlData may be NULL, non-NULL with no root, or the getter may return NULL
        # for a non-NULL payload/name mismatch (explicit native contract).
        vtable = m.alloc(struct.pack("<IIII", 0, 0, 0, 0x7E0000))
        payload = 0 if xml == "null" else m.alloc(struct.pack("<I", vtable))
        fixtures.append(("Research/XmlData", 10, payload))
    fixtures.append(("Research/AfterPoints", 2, m.alloc(struct.pack("<I", 1))))
    entries = m.alloc(b"".join(struct.pack("<IIIIIII", m.cstring(path), payload, kind, 0,
                                           n + 1, 0, m.cstring("unspecified"))
                              for n, (path, kind, payload) in enumerate(fixtures)))
    broker = m.alloc(bytes(32))
    m.write(broker + 4, entries)
    m.write(broker + 8, entries + len(fixtures) * 0x1C)
    m.write(broker + 12, entries + len(fixtures) * 0x1C)
    filenames = m.alloc(bytes(4))
    m.write(filenames, filenames)
    m.write(broker + 20, filenames)
    m.write(m.stack + 4, broker)
    m.write(0x6F7B84, 0)
    def boundary(pc):
        sp = m.reg("ESP")
        if (pc in (0x60201E, h.STRING_CAVE + 8) and m.reg("EBX") == 0 and
                bytes(m.emu.readMemory(api.toAddr(pc), 1)) == b"\x8b"):
            raise ValueError("CONFIRMED_PRISTINE_NULL_STRINGLIST_60201E")
        if (pc in (0x602153, h.XML_CAVE + 10) and m.reg("EAX") == 0 and
                bytes(m.emu.readMemory(api.toAddr(pc), 1)) == b"\x8b"):
            raise ValueError("CONFIRMED_PRISTINE_NULL_XMLDATA_602153")
        if pc == 0x4D1690:
            destination, fmt = m.read(sp + 4), m.read(sp + 8)
            m.write(destination, m.cstring(m.text(fmt)))
            m.ret(destination)
        elif pc == 0x4D0570:
            m.ret(m.read(m.reg("ECX")))  # intern lookup only, not native formatter logic
        elif pc == 0x4D0580:
            m.write(m.reg("ECX"), m.read(sp + 4))
            m.ret(m.reg("ECX"), 4)
        elif pc == 0x4DDB30:
            m.ret(m.read(m.reg("ECX") + 4))
        elif pc == 0x4DDA10 and (xml == "mismatch" or m.read(m.reg("ECX") + 4) != 0):
            # Non-NULL XML filename/virtual object internals are a bounded fixture.
            m.ret(0 if xml == "mismatch" else m.read(m.reg("ECX") + 4), 4)
        elif pc == 0x7E0000:
            m.ret(0)  # native existing no-root path; XML rendering is outside this test
        elif pc == 0x5B4C00:
            m.ret()
        elif pc == 0x4D0620:
            fmt_address = m.read(sp + 4)
            fmt = m.text(fmt_address)
            values = []
            for n, token in enumerate(re.findall(r"%[-+0-9.]*[sd]", fmt)):
                value = m.read(sp + 8 + n * 4)
                values.append(m.text(value) if token.endswith("s") else value)
            text = fmt % tuple(values)
            calls.append((fmt_address, values, m.read(0x6F7B84)))
            # Sink indentation is a formatting boundary; preserve native text tokens.
            fragments.append(text)
            m.ret()
        else:
            return False
        return True
    try:
        m.execute(boundary)
        if m.read(0x6F7B84) != 0:
            raise ValueError("Dump indentation was not restored")
        raw = "".join(fragments).encode("cp1252")
        if raw.count(b"{") != raw.count(b"}") or b"Research/AfterPoints" not in raw:
            raise ValueError("Dump not balanced or following entry missing")
        return {"calls": calls, "raw": raw, "steps": m.steps}
    finally:
        m.emu.dispose()


def emulate(program, api, monitor, parser, output):
    loading_rows, dump_rows, baselines = [], [], {}
    scenarios = [(1, 0), (0, 0), (0, 0x20001234), (0, 0x20001235), (0, 0xFFFFFFFF)]
    for hardened in (False, True):
        install(program, api, monitor, hardened)
        for counter in range(4):
            for stat, size in scenarios:
                result = loading(program, api, monitor, counter, stat, size)
                failed = stat != 0 or size <= 0x20001234 or size >= 0x80000000
                expected = [] if counter % 2 == 0 else (
                    [("Race/AttractMode", 1), ("Race/Type", 1)] if failed and not hardened
                    else [("Race/Starter", 1)])
                if result["writes"] != expected or len(result["checks"]) != counter % 2:
                    raise ValueError("Loading branch/writes do not match reconstructed semantics")
                loading_rows.append({"hardened": hardened, "counter": counter, "stat": stat,
                                     "size": size, **result})
        for name, points, xml in (("populated", ["10", "9"], None), ("empty", [], None),
                                   ("null", None, None), ("xml-null", [], "null"),
                                   ("xml-no-root", [], "no-root"), ("xml-mismatch", [], "mismatch")):
            try:
                result = dump(program, api, monitor, points, xml)
            except ValueError as exc:
                if (hardened or name not in ("null", "xml-null", "xml-mismatch") or
                        not str(exc).startswith("CONFIRMED_PRISTINE_NULL_")):
                    raise
                dump_rows.append({"hardened": False, "fixture": name, "expected_unsafe": str(exc)})
                continue
            snapshot = parser(result["raw"], {"capture_kind": "synthetic-native-x86-emulation"})
            values = {row["path"]: row["value"] for row in snapshot["entries"]}
            if (values.get("Research/AfterPoints") != 1 or
                    values.get("Frontend/RaceResults/PointsList") != [f'"{item}"' for item in (points or [])]):
                output.with_name("failed-fixture.dump.bin").write_bytes(result["raw"])
                raise ValueError(f"Existing Observatory parser rejected expected fixture values: {values}")
            if not hardened:
                baselines[name] = result
            elif name in baselines and any(result[key] != baselines[name][key] for key in ("calls", "raw")):
                raise ValueError("Non-NULL native output/logger arguments changed")
            if hardened and name == "null" and any(result[key] != baselines["empty"][key]
                                                     for key in ("calls", "raw")):
                raise ValueError("NULL StringList did not emit exact stock allocated-empty representation")
            path = output.parent / ("hardened-" if hardened else "stock-")
            path = path.with_name(path.name + name + ".dump.bin")
            path.write_bytes(result["raw"])
            dump_rows.append({"hardened": hardened, "fixture": name, "steps": result["steps"],
                              "raw_sha256": h.sha256(result["raw"]), "entries": len(values),
                              "following_entry": True, "balanced": True, "parser_accepts": True,
                              "non_null_stock_output_equal": name in baselines})
    return {"status": "STATIC_NATIVE_HARDENING_EMULATION_PASS", "runtime_game_test": False,
            "project_saved": False, "loading_cases": len(loading_rows), "dump_cases": len(dump_rows),
            "loading": loading_rows, "dump": dump_rows,
            "boundaries": ["stat", "allocation/free", "Broker setters", "enString intern lookup",
                           "log sink printf", "non-NULL XML internals/no-root virtual method"]}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    for option in ("install", "project", "candidate", "observatory", "output"):
        parser.add_argument("--" + option, required=True, type=Path)
    args = parser.parse_args()
    h.verify(args.candidate.read_bytes())
    output = h.ignored_output(args.output)
    output.parent.mkdir(parents=True, exist_ok=True)
    observe = load_profile(args.observatory, args.candidate)
    import pyghidra
    pyghidra.start(install_dir=args.install)
    from java.lang import Object
    from ghidra.program.flatapi import FlatProgramAPI
    project = pyghidra.open_project(args.project, "MasterRallye")
    consumer = Object()
    program = project.getProjectData().getFile("/MRallye.exe").getReadOnlyDomainObject(
        consumer, -1, pyghidra.task_monitor())
    transaction = None
    try:
        if str(program.getExecutableSHA256()) != h.RETAIL_SHA256:
            raise ValueError("Analyzed program differs from pristine")
        transaction = program.startTransaction("R-AI11 hardening unsaved emulation")
        result = emulate(program, FlatProgramAPI(program), pyghidra.task_monitor(),
                         observe.core.parse_dump_bytes, output)
        output.write_text(json.dumps(result, indent=2) + "\n")
        print(result["status"], result["loading_cases"], "loading;", result["dump_cases"], "Dump cases")
    finally:
        if transaction is not None:
            program.endTransaction(transaction, False)
        program.release(consumer)
        project.close()


if __name__ == "__main__":
    main()
