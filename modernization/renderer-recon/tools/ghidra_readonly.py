"""Read-only renderer queries using the installed ghidra-bridge exporter.

Never opens a writable project or saves a program. Missing functions may be
disassembled in an in-memory transaction, which is always rolled back.
"""
from __future__ import annotations
import argparse
import hashlib
import json
from pathlib import Path

SHA256 = 'bf8aef32407eb6552c05045b8abef149f32983cedd9503b865069b444c5f96b4'
ROOT = Path(__file__).resolve().parents[1]

def guarded_output(path):
    result = Path(path).resolve()
    if not result.is_relative_to(ROOT / '.analysis'):
        raise ValueError('Raw Ghidra output must be inside renderer-recon/.analysis')
    return result

def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument('--install', type=Path, required=True)
    ap.add_argument('--project', type=Path, required=True)
    ap.add_argument('--program', default='/MRallye.exe')
    ap.add_argument('--binary', type=Path, required=True)
    ap.add_argument('--java', type=Path, required=True)
    ap.add_argument('--output', type=guarded_output, required=True)
    ap.add_argument('--scan', action='store_true')
    ap.add_argument('--addresses', nargs='*', type=lambda s: int(s, 16), default=[])
    ap.add_argument('--data', nargs='*', type=lambda s: int(s, 16), default=[])
    ap.add_argument('--references', nargs='*', type=lambda s: int(s, 16), default=[])
    a = ap.parse_args()
    if hashlib.sha256(a.binary.read_bytes()).hexdigest() != SHA256:
        raise ValueError('Not the pristine retail executable')
    import pyghidra
    from pyghidra.launcher import HeadlessPyGhidraLauncher
    a.output.mkdir(parents=True, exist_ok=True)
    launcher = HeadlessPyGhidraLauncher(install_dir=a.install)
    launcher.java_home = a.java
    launcher.add_vmargs('-Dapplication.settingsdir=' + str(a.output / 'settings'),
                        '-Dapplication.cachedir=' + str(a.output / 'cache'),
                        '-Dapplication.tempdir=' + str(a.output / 'temp'))
    launcher.start()
    from java.lang import Object
    from ghidra.framework.data import DefaultProjectData
    from ghidra.framework.model import ProjectLocator
    from ghidra.program.flatapi import FlatProgramAPI
    from ghidra.app.decompiler import DecompInterface
    from ghidra_ai_bridge.exporters.runner import export_single_function
    # Constructor documentation: isInWritableProject=False, resetOwner=False.
    project = DefaultProjectData(ProjectLocator(str(a.project), 'MasterRallye'), False, False)
    consumer = Object()
    program = decomp = ir = None
    tx = None
    a.output.mkdir(parents=True, exist_ok=True)
    def save(name, value):
        (a.output / name).write_text(json.dumps(value, indent=2) + '\n', encoding='utf-8')
    try:
        domain = project.getFile(a.program)
        if domain is None:
            def names(folder):
                return [str(f.getPathname()) for f in folder.getFiles()] + [n for child in folder.getFolders() for n in names(child)]
            raise ValueError('Program missing; available: ' + str(names(project.getRootFolder())))
        program = domain.getReadOnlyDomainObject(consumer, -1, pyghidra.task_monitor())
        if str(program.getExecutableSHA256()).lower() != SHA256:
            raise ValueError('Ghidra program build mismatch')
        api = FlatProgramAPI(program)
        fm = program.getFunctionManager()
        refs = program.getReferenceManager()
        listing = program.getListing()
        if a.scan:
            functions = []
            indirect = []
            renderer = []
            strings = []
            for fn in fm.getFunctions(True):
                va = fn.getEntryPoint().getOffset()
                callers = [{'va': str(r.getFromAddress()), 'owner': str(f.getEntryPoint()) if (f := fm.getFunctionContaining(r.getFromAddress())) else None} for r in refs.getReferencesTo(fn.getEntryPoint())]
                functions.append({'va': int(va), 'end': int(fn.getBody().getMaxAddress().getOffset()), 'name': str(fn.getName()), 'callers': callers})
            context = []
            for inst in listing.getInstructions(True):
                va = int(inst.getAddress().getOffset())
                row = {'va': va, 'asm': str(inst)}
                if 0x00530000 <= va < 0x005a4000:
                    fn = fm.getFunctionContaining(inst.getAddress())
                    row['owner'] = int(fn.getEntryPoint().getOffset()) if fn else None
                    renderer.append(row)
                if inst.getMnemonicString() == 'CALL' and '[' in str(inst):
                    fn = fm.getFunctionContaining(inst.getAddress())
                    indirect.append(dict(row, owner=int(fn.getEntryPoint().getOffset()) if fn else None, context=context[-18:]))
                context.append(row)
                if len(context) > 18:
                    context.pop(0)
            for datum in listing.getDefinedData(True):
                if 'string' in str(datum.getDataType()).lower():
                    value = str(datum.getValue())
                    if any(k in value.lower() for k in ('direct', 'render', 'sky', 'fog', 'light', 'camera', 'screen', 'particle', 'shader', 'texture', 'gamma', 'wire', 'viewport', 'fullscreen', 'resolution', 'near', 'farclip', 'sun', 'lod', 'drawdistance', 'fov')):
                        strings.append({'va': int(datum.getAddress().getOffset()), 'value': value, 'refs': [str(r.getFromAddress()) for r in refs.getReferencesTo(datum.getAddress())]})
            save('functions.json', functions)
            save('indirect.json', indirect)
            save('renderer-instructions.json', renderer)
            save('strings.json', strings)
            print('Scan:', len(functions), 'functions;', len(indirect), 'indirect calls;', len(renderer), 'renderer instructions', flush=True)
        if a.data:
            save('data.json', {hex(va): [hex(int(program.getMemory().getInt(api.toAddr(va + i * 4))) & 0xffffffff) for i in range(64)] for va in a.data})
        if a.references:
            save('references.json', {hex(va): [
                {'from_va': str(r.getFromAddress()), 'type': str(r.getReferenceType()),
                 'owner': str(f.getEntryPoint()) if (f := fm.getFunctionContaining(r.getFromAddress())) else None,
                 'instruction': str(listing.getInstructionAt(r.getFromAddress()))}
                for r in refs.getReferencesTo(api.toAddr(va))] for va in a.references})
        tx = program.startTransaction('R-GFX1 temporary queries; rollback only')
        decomp = DecompInterface()
        decomp.openProgram(program)
        ir = DecompInterface()
        ir.setSimplificationStyle('normalize')
        ir.openProgram(program)
        query_errors = []
        for va in a.addresses:
            addr = api.toAddr(va)
            fn = fm.getFunctionAt(addr)
            if fn is None:
                api.disassemble(addr)
                fn = api.createFunction(addr, 'R_GFX1_%08x' % va)
            if fn is None:
                query_errors.append('No function at %08x' % va)
                print(query_errors[-1], flush=True)
                continue
            export_single_function(fn, program, fm, refs, str(a.output), listing, decomp, ir)
            print('Exported %08x' % va, flush=True)
        save('query-errors.json', query_errors)
        save('provenance.json', {'sha256': SHA256, 'ghidra': str(a.install), 'project_writable': False, 'program_saved': False, 'transaction': 'ROLLED_BACK', 'exporter': 'ghidra_ai_bridge.exporters.runner.export_single_function'})
    finally:
        if decomp is not None:
            decomp.dispose()
        if ir is not None:
            ir.dispose()
        if tx is not None:
            program.endTransaction(tx, False)
        if program is not None:
            program.release(consumer)
        project.close()

if __name__ == '__main__':
    main()
