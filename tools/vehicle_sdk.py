"""Small command hub over the existing Vehicle SDK tools; no game assets bundled.

Examples: vehicle_sdk.py create --help; import-gt4 --help; author-gt4 --help;
validate --help; build-project --help; preview --help; roster-build --help.
Project/profile JSON remains the editable source of truth, not hidden GUI state.
"""
import argparse,json,subprocess,sys
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
COMMANDS={
    'gt-garage':('gt_garage.py',),
    'gt-source-project':('gt_source_project.py',),
    'stock-project':('stock_vehicle_project.py',),
    'create':('mrtool.py','addon','init'),
    'import-gt4':('build_gt4_vehicle.py',),
    'import-gt3':('build_gt3_vehicle.py',),
    'auto-import-gt3':('gt_auto_import.py',),
    'author-gt4':('prepare_gt4_addon.py',),
    'validate':('mrtool.py','addon','project-validate'),
    'build-project':('mrtool.py','addon','project-build'),
    'preview':('preview_vehicle.py',),
    'audio-preview':('vehicle_audio_preview.py',),
    'normalize-textures':('normalize_vehicle_texture_residency.py',),
    'resource-diagnose':('diagnose_vehicle_resources.py',),
    'frontend-complexity':('vehicle_frontend_complexity.py',),
    'frontend-capture':('capture_frontend_performance.py',),
    'frontend-compare':('compare_frontend_perf_captures.py',),
    'reflection-diagnose':('audit_vehicle_reflection_continuity.py',),
    'fitment-diagnose':('diagnose_vehicle_fitment.py',),
    'fitment-overlay':('render_vehicle_fitment_overlay.py',),
    'camera-diagnose':('vehicle_camera_diagnostics.py',),
    'roster-build':('build_sdk_roster.py',),
}

def command(name,args):
    if name not in COMMANDS:raise ValueError('unknown SDK command')
    tool,*prefix=COMMANDS[name]
    return [sys.executable,str(ROOT/'tools'/tool),*prefix,*args]

def main():
    if len(sys.argv)<2 or sys.argv[1] in ('-h','--help'):
        print(__doc__);print('Commands: '+', '.join((*COMMANDS,'roster-validate')));return
    name=sys.argv[1]
    if name=='roster-validate':
        p=argparse.ArgumentParser(description='Reproduce and verify a source-bound combined roster without launching MR')
        p.add_argument('--config',type=Path,required=True);p.add_argument('--candidate',type=Path,required=True);a=p.parse_args(sys.argv[2:])
        from build_sdk_roster import derive,verify
        print(json.dumps(verify(a.candidate/'runtime',derive(json.loads(a.config.read_text()))),indent=2));return
    subprocess.run(command(name,sys.argv[2:]),check=True,cwd=ROOT)

if __name__=='__main__':main()
