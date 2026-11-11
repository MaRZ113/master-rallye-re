"""Build capacity-specific Extra Options DLLs without installing any files."""
from __future__ import annotations
import argparse
import hashlib
import json
from pathlib import Path
from build_extra_options_candidate import ROOT, RETAIL, package_header, build_core
from build_extra_sdk_binding import build as build_proxy


def build(output: Path, sdk_runtime: Path | None, sdk_root: Path | None, menu_builder: bool = False):
    output=output.resolve()
    independent=sdk_runtime is None
    if not independent:sdk_runtime=sdk_runtime.resolve();sdk_root=sdk_root.resolve()
    allowed=(ROOT/'.research-output/extra-set1').resolve()
    if not output.is_relative_to(allowed) or output==allowed or output.exists():
        raise ValueError('select a fresh isolated extra-set1 output')
    output.mkdir(parents=True)
    header,_,_=package_header(sdk_runtime,roster_independent=independent)
    core=build_core(output)
    result=build_proxy(output/'proxy',RETAIL,None if independent else sdk_runtime/'native-patch-manifest.json',core,sdk_root,
                       checkpoint='g1',extra_header=header,menu_builder=menu_builder)
    plan=None if independent else json.loads((sdk_runtime/'addon-plan.json').read_text())
    source_files=[*sorted((ROOT/'src/native/rmod1').glob('*.cpp')),*sorted((ROOT/'src/native/rmod1').glob('*.hpp')),
                  ROOT/'tools/build_extra_capacity_candidate.py',ROOT/'tools/build_extra_sdk_binding.py',
                  ROOT/'tools/extra_options_sdk_binding.py',ROOT/'tools/build_extra_options_candidate.py',ROOT/'tools/r_mod1_native_plan.py']
    report={'schema':'extra-options-capacity-build/1','status':'OWNER_TEST_CANDIDATE',
            'record_count':plan['registry_layout']['record_count'] if plan else 'installed roster',
            'registry_transport':'MR_VEHICLE_REGISTRY_DESCRIPTOR child environment; MRVC v1',
            'marker_abi':'0x4d525601','renderer_abi':'0x45583201',
            'sdk_binding':result,'installed_files_written':[],
            'source_files':{str(p.relative_to(ROOT)).replace('\\','/'):hashlib.sha256(p.read_bytes()).hexdigest() for p in source_files},
            'files':{str(p.relative_to(output)).replace('\\','/'):hashlib.sha256(p.read_bytes()).hexdigest()
                     for p in (core,output/'proxy/dinput8.dll')},'gameplay_qualified':False}
    (output/'capacity-build.json').write_text(json.dumps(report,indent=2)+'\n')
    return report


if __name__=='__main__':
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output',type=Path,required=True)
    parser.add_argument('--sdk-runtime',type=Path,help='legacy: compile one roster SDK profile in; omit for a roster-independent loader')
    parser.add_argument('--sdk-root',type=Path)
    parser.add_argument('--menu-builder',action='store_true',help='also link the Menu Builder runtime (exports @14..16)')
    args=parser.parse_args()
    print(json.dumps(build(args.output,args.sdk_runtime,args.sdk_root,args.menu_builder),indent=2))
