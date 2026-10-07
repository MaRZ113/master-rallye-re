"""Hash-locked PS2 ELF queries through the installed ghidra-bridge exporter.

The original ELF is only read. Import/auto-analysis writes an ignored local
Ghidra project; subsequent queries open it read-only and roll back temporary
function discovery. Raw decompilation is local, never a source deliverable.
"""
from __future__ import annotations
import argparse
import hashlib
import json
import re
import struct
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
LOCAL = ROOT / 'data' / 'packfs-local'
SHA = 'b15a80c516986bfd7f9fcfcfa2ec5fbf37643778c6363dde460006d7001a78f2'
PROJECT = 'PS2PackFS_MIPS3'

def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument('mode', choices=['import', 'query'])
    ap.add_argument('--elf', type=Path, required=True)
    ap.add_argument('--install', type=Path, required=True)
    ap.add_argument('--addresses', nargs='*', type=lambda s: int(s, 0), default=[])
    ap.add_argument('--refs', nargs='*', type=lambda s: int(s, 0), default=[])
    ap.add_argument('--stack-surrogate', action='store_true', help='Temporary SQ/LQ low-64-bit SD/LD analysis surrogate, rolled back')
    args = ap.parse_args()
    binary = args.elf.read_bytes()
    if hashlib.sha256(binary).hexdigest() != SHA:
        raise ValueError('Unsupported ELF SHA256')
    LOCAL.mkdir(parents=True, exist_ok=True)
    import pyghidra
    from pyghidra.launcher import HeadlessPyGhidraLauncher
    launch = HeadlessPyGhidraLauncher(install_dir=args.install)
    launch.add_vmargs('-Dapplication.settingsdir=' + str(LOCAL / 'settings'),
                      '-Dapplication.cachedir=' + str(LOCAL / 'cache'),
                      '-Dapplication.tempdir=' + str(LOCAL / 'temp'))
    launch.start()
    if args.mode == 'import':
        with pyghidra.open_program(args.elf, project_location=LOCAL / 'projects',
                                  project_name=PROJECT, analyze=True,
                                  language='MIPS:LE:64:64-32addr', compiler='o32'):
            print('Import/analysis complete', flush=True)
        return
    from java.lang import Object
    from ghidra.framework.data import DefaultProjectData
    from ghidra.framework.model import ProjectLocator
    from ghidra.program.flatapi import FlatProgramAPI
    from ghidra.app.decompiler import DecompInterface
    from ghidra_ai_bridge.exporters.runner import export_single_function
    project = DefaultProjectData(ProjectLocator(str(LOCAL / 'projects' / PROJECT), PROJECT), False, False)
    consumer = Object()
    program = project.getFile('/SLES_509.06').getReadOnlyDomainObject(consumer, -1, pyghidra.task_monitor())
    decomp = ir = None
    tx = None
    output = LOCAL / 'exports'
    output.mkdir(exist_ok=True)
    def save(name, value):
        (output / name).write_text(json.dumps(value, indent=2) + '\n', encoding='utf-8')
    try:
        if str(program.getExecutableSHA256()).lower() != SHA:
            raise ValueError('Ghidra program hash mismatch')
        api = FlatProgramAPI(program)
        fm = program.getFunctionManager()
        refs = program.getReferenceManager()
        listing = program.getListing()
        tx = program.startTransaction('Temporary query; rollback')
        if args.stack_surrogate:
            lo, hi = 0x2b0000, 0x2c1100
            for fn in list(fm.getFunctions(True)):
                if fn.hasNoReturn(): fn.setNoReturn(False)
                if lo <= int(fn.getEntryPoint().getOffset()) < hi:
                    fm.removeFunction(fn.getEntryPoint())
            api.clearListing(api.toAddr(lo), api.toAddr(hi-1))
            transforms = []
            for va in range(lo, hi, 4):
                word = struct.unpack_from('<I', binary, va-0xff000)[0]
                op = word >> 26
                if op in (0x1e, 0x1f):  # R5900 LQ/SQ, lower halves contain o32 pointers.
                    replacement = ((0x37 if op == 0x1e else 0x3f) << 26) | (word & 0x3ffffff)
                    signed = replacement if replacement < 0x80000000 else replacement - 0x100000000
                    program.getMemory().setInt(api.toAddr(va), signed)
                    transforms.append({'va': hex(va), 'original': hex(word), 'surrogate': hex(replacement)})
            save('stack-surrogates.json', transforms)
            targets = set(args.addresses)
            for p in range(0x1000, 0x30ea74, 4):
                word = struct.unpack_from('<I', binary, p)[0]
                target = (word & 0x3ffffff) * 4
                if word >> 26 == 3 and lo <= target < hi: targets.add(target)
            for va in sorted(targets):
                if fm.getFunctionAt(api.toAddr(va)) is None:
                    api.disassemble(api.toAddr(va))
                    api.createFunction(api.toAddr(va), 'query_%08x' % va)
        def ref_rows(va):
            return [{'from': str(r.getFromAddress()), 'owner': str(f.getEntryPoint()) if (f := fm.getFunctionContaining(r.getFromAddress())) else None,
                     'type': str(r.getReferenceType()), 'asm': str(listing.getInstructionAt(r.getFromAddress()))}
                    for r in refs.getReferencesTo(api.toAddr(va))]
        strings = []
        for m in re.finditer(rb'[ -~]{4,}', binary):
            if any(k in m.group().lower() for k in (b'packfs', b'compressor', b'lzo', b'.pak', b'.000', b'1.07')):
                va = m.start() + 0xff000  # canonical PT_LOAD: offset 0x1000 -> VA 0x100000
                strings.append({'va': hex(va), 'value': m.group().decode('ascii'), 'refs': ref_rows(va)})
        save('strings.json', strings)
        save('references.json', {hex(va): ref_rows(va) for va in args.refs})
        save('layout.json', {'language': str(program.getLanguageID()), 'blocks': [{'name': str(b.getName()), 'start': str(b.getStart()), 'end': str(b.getEnd()), 'execute': bool(b.isExecute())} for b in program.getMemory().getBlocks()]})
        decomp = DecompInterface()
        decomp.openProgram(program)
        ir = DecompInterface()
        ir.setSimplificationStyle('normalize')
        ir.openProgram(program)
        for va in args.addresses:
            fn = fm.getFunctionContaining(api.toAddr(va))
            if fn is None:
                api.disassemble(api.toAddr(va))
                fn = api.createFunction(api.toAddr(va), 'query_%08x' % va)
            if fn is None:
                raise ValueError('No function at %08x' % va)
            export_single_function(fn, program, fm, refs, str(output), listing, decomp, ir)
            print('Exported', fn.getEntryPoint(), flush=True)
    finally:
        if decomp is not None: decomp.dispose()
        if ir is not None: ir.dispose()
        if tx is not None: program.endTransaction(tx, False)
        program.release(consumer)
        project.close()

if __name__ == '__main__':
    main()
