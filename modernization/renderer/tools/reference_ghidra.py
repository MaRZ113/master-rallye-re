"""Read-only input import into a NEW ignored Ghidra scratch project.

Uses ghidra-bridge's exporter. Never executes the patcher or opens old databases.
"""
import argparse
import hashlib
import json
from pathlib import Path
from ghidra_readonly import guarded_output

PATCHER_SHA = 'e0de5489b3b512d174024397eac0d54dc2afd8f3f2c13933a0c3881f75860814'

def main():
    p = argparse.ArgumentParser(description=__doc__)
    for key in ('install', 'binary', 'java'):
        p.add_argument('--'+key, type=Path, required=True)
    p.add_argument('--output', type=guarded_output, required=True)
    a = p.parse_args()
    if hashlib.sha256(a.binary.read_bytes()).hexdigest() != PATCHER_SHA:
        raise ValueError('Not the supplied widescreen reference patcher')
    from pyghidra.launcher import HeadlessPyGhidraLauncher
    import pyghidra
    a.output.mkdir(parents=True, exist_ok=True)
    launcher = HeadlessPyGhidraLauncher(install_dir=a.install)
    launcher.java_home = a.java
    for key in ('settings', 'cache', 'temp'):
        launcher.add_vmargs('-Dapplication.'+{'settings':'settingsdir','cache':'cachedir','temp':'tempdir'}[key]+'='+str(a.output/key))
    launcher.start()
    from ghidra.app.decompiler import DecompInterface
    from ghidra_ai_bridge.exporters.runner import export_single_function
    scratch = Path(__file__).resolve().parents[1]/'research/r-gfx5/scratch'
    scratch.mkdir(parents=True, exist_ok=True)
    with pyghidra.open_program(a.binary.resolve(), project_location=scratch, project_name='WidescreenReference', analyze=True) as api:
        program = api.getCurrentProgram()
        if str(program.getExecutableSHA256()).lower() != PATCHER_SHA:
            raise ValueError('Scratch program identity mismatch')
        decomp = DecompInterface()
        try:
            decomp.openProgram(program)
            fn = program.getFunctionManager().getFunctionAt(api.toAddr(0x401500))
            if fn is None:
                raise ValueError('COFF main entry not recovered')
            export_single_function(fn, program, program.getFunctionManager(), program.getReferenceManager(), str(a.output), program.getListing(), decomp, None)
            (a.output/'provenance.json').write_text(json.dumps({'sha256':PATCHER_SHA,'main_va':'0x00401500','main_rva':'0x00001500','input_execution':False,'existing_projects_opened':False,'exporter':'ghidra_ai_bridge.exporters.runner.export_single_function'}, indent=2)+'\n')
        finally:
            decomp.dispose()

if __name__ == '__main__':
    main()
