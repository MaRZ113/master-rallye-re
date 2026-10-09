"""Bounded read-only PS2 UI queries through the installed ghidra-bridge.

Uses the existing ignored PackFS project. R5900 LQ/SQ stack instructions may
be replaced by LD/SD in memory for scalar analysis; every change is rolled
back. This does not model R5900 packed graphics instructions or runtime state.
"""
import argparse
import hashlib
import json
import struct
from pathlib import Path
from elf_query import ROOT, LOCAL, PROJECT, SHA


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument('--elf', type=Path, required=True)
    ap.add_argument('--install', type=Path, required=True)
    ap.add_argument('--window', nargs=2, type=lambda s: int(s, 0), required=True)
    ap.add_argument('--addresses', nargs='+', type=lambda s: int(s, 0), required=True)
    ap.add_argument('--refs', nargs='*', type=lambda s: int(s, 0), default=[])
    ap.add_argument('--track', choices=['ui1', 'ui2', 'ambient1', 'grass1', 'water1', 'refl1', 'dressing1', 'treeblend1', 'ambient2'], default='ui1',
                    help='Ignored local export directory; defaults to the original UI1 track')
    ap.add_argument('--ee-scalar', action='store_true',
                    help='Normalize EE SQRT operand and MULT rd for scalar dataflow; requires no HI/LO reads in window')
    ap.add_argument('--ee-sqrt-only', action='store_true',
                    help='Normalize only EE SQRT operands; preserve MULT and HI/LO instructions')
    ap.add_argument('--ee-mult-sites', nargs='*', type=lambda s: int(s, 0), default=[],
                    help='Explicit audited EE MULT rd sites; low32 only, HI/LO are not modeled')
    a = ap.parse_args()
    b = a.elf.read_bytes()
    if hashlib.sha256(b).hexdigest() != SHA:
        raise ValueError('Unsupported ELF SHA256')
    lo, hi = a.window
    if not 0x100000 <= lo < hi <= 0x40da74 or hi-lo > 0x20000 or (lo|hi)&3:
        raise ValueError('Invalid or excessive UI query window')
    if any(not lo <= v < hi for v in a.addresses):
        raise ValueError('Function address outside query window')
    for va in a.ee_mult_sites:
        if not lo <= va < hi or va & 3:
            raise ValueError('EE MULT site outside aligned query window')
        word = struct.unpack_from('<I', b, va-0xff000)[0]
        if word >> 26 != 0 or word & 63 not in (24, 25) or not (word >> 11) & 31:
            raise ValueError('Explicit site is not EE MULT with nonzero rd')
    if a.ee_scalar and any((w := struct.unpack_from('<I', b, va-0xff000)[0]) >> 26 == 0
                           and w & 63 in (16, 18) for va in range(lo, hi, 4)):
        raise ValueError('EE scalar MULT surrogate cannot preserve HI/LO consumers')
    import pyghidra
    from pyghidra.launcher import HeadlessPyGhidraLauncher
    launcher = HeadlessPyGhidraLauncher(install_dir=a.install)
    launcher.add_vmargs('-Dapplication.settingsdir='+str(LOCAL/'settings'),
                        '-Dapplication.cachedir='+str(LOCAL/'cache'),
                        '-Dapplication.tempdir='+str(LOCAL/'temp'))
    launcher.start()
    from java.lang import Object
    from ghidra.framework.data import DefaultProjectData
    from ghidra.framework.model import ProjectLocator
    from ghidra.program.flatapi import FlatProgramAPI
    from ghidra.app.decompiler import DecompInterface
    from ghidra_ai_bridge.exporters.runner import export_single_function
    project = DefaultProjectData(ProjectLocator(str(LOCAL/'projects'/PROJECT), PROJECT), False, False)
    consumer = Object()
    program = project.getFile('/SLES_509.06').getReadOnlyDomainObject(consumer, -1, pyghidra.task_monitor())
    tx = decomp = ir = None
    output = ROOT/'data'/a.track/'elf'
    output.mkdir(parents=True, exist_ok=True)
    def save(name, value):
        (output/name).write_text(json.dumps(value, indent=2)+'\n', encoding='utf-8', newline='\n')
    try:
        if str(program.getExecutableSHA256()).lower() != SHA:
            raise ValueError('Ghidra program hash mismatch')
        api = FlatProgramAPI(program)
        fm, refs, listing = program.getFunctionManager(), program.getReferenceManager(), program.getListing()
        tx = program.startTransaction('Temporary UI query; rollback')
        for fn in list(fm.getFunctions(True)):
            if fn.hasNoReturn(): fn.setNoReturn(False)
            if lo <= int(fn.getEntryPoint().getOffset()) < hi: fm.removeFunction(fn.getEntryPoint())
        api.clearListing(api.toAddr(lo), api.toAddr(hi-1))
        changes = []
        for va in range(lo, hi, 4):
            word = struct.unpack_from('<I', b, va-0xff000)[0]
            replacement = None
            kind = None
            if word>>26 in (0x1e, 0x1f):
                replacement = ((0x37 if word>>26 == 0x1e else 0x3f)<<26)|(word&0x3ffffff)
                kind = 'LQ/SQ low64 only'
            elif (a.ee_scalar or va in a.ee_mult_sites) and word >> 26 == 0 and word & 63 in (24, 25) and (word >> 11) & 31:
                replacement = 0x70000002 | (word & 0x03fff800)
                kind = 'EE MULT rd low32 only; HI/LO not modeled'
            elif (a.ee_scalar or a.ee_sqrt_only) and word >> 21 == 0x230 and word & 63 == 4:
                replacement = (word & ~0x001ff800) | (((word >> 16) & 31) << 11)
                kind = 'EE SQRT ft to MIPS SQRT fs; positive finite scalar dataflow only'
            if replacement is not None:
                program.getMemory().setInt(api.toAddr(va), replacement if replacement<0x80000000 else replacement-0x100000000)
                changes.append({'va':hex(va),'original':hex(word),'surrogate':hex(replacement),'kind':kind})
        save('surrogates-%x-%x.json'%(lo,hi), changes)
        targets = set(a.addresses)
        for p in range(0x1000, 0x30ea74, 4):
            w = struct.unpack_from('<I', b, p)[0]
            v = (w&0x3ffffff)*4
            if w>>26 == 3 and lo<=v<hi: targets.add(v)
        for va in sorted(targets):
            api.disassemble(api.toAddr(va))
            if fm.getFunctionAt(api.toAddr(va)) is None: api.createFunction(api.toAddr(va),'ui_%08x'%va)
        save('refs-%x.json'%lo, {hex(v):[{'from':str(r.getFromAddress()),'owner':str(f.getEntryPoint()) if (f:=fm.getFunctionContaining(r.getFromAddress())) else None,'asm':str(listing.getInstructionAt(r.getFromAddress()))} for r in refs.getReferencesTo(api.toAddr(v))] for v in a.refs})
        decomp, ir = DecompInterface(), DecompInterface()
        decomp.openProgram(program)
        ir.setSimplificationStyle('normalize')
        ir.openProgram(program)
        for va in a.addresses:
            fn = fm.getFunctionAt(api.toAddr(va))
            if fn is None: raise ValueError('No function at %x'%va)
            export_single_function(fn,program,fm,refs,str(output),listing,decomp,ir)
            print('Exported',fn.getEntryPoint(),flush=True)
    finally:
        if decomp is not None: decomp.dispose()
        if ir is not None: ir.dispose()
        if tx is not None: program.endTransaction(tx,False)
        program.release(consumer)
        project.close()


if __name__ == '__main__':
    main()
