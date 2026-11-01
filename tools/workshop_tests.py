"""Explicit test tiers with timings and transparent selection (no deleted tests)."""
from pathlib import Path
import argparse
import json
import sys
import time
import unittest
ROOT=Path(__file__).resolve().parents[1]
sys.path[:0]=[str(ROOT/'src'),str(ROOT/'tests/synthetic'),str(ROOT)]
SMOKE=('test_preview_cache','test_editable_vehicle','test_source_scene_preview','test_universal_scene_bridge')
INTEGRATION=(*SMOKE,'test_native_family_scene','test_scene_semantics','test_universal_vehicle_scene','test_workshop_universal_source',
             'test_workshop','test_workshop_stabilization','test_dakar2_materials','test_material_derivation')
DEPENDENCIES={
    'roster_layout':('test_roster_layout','test_sdk_roster','test_sdk_capacity'),
    'roster_scene_layout':('test_roster_layout','test_sdk_roster'),
    'sdk_capacity_native':('test_roster_layout','test_sdk_capacity','test_sdk_roster'),
    'prepare_roster_order_pilot':('test_roster_layout','test_definitive_restoration'),
    'validate_roster_order_pilot':('test_roster_layout','test_sdk_capacity'),
    'demo_restoration':('test_demo_identity','test_demo_restoration','test_definitive_restoration','test_heritage_source','test_physics_profile','test_addon_ui_assets'),
    'demo_identity':('test_demo_identity','test_demo_restoration','test_workshop_vehicle'),
    'audit_demo_identity':('test_demo_identity',),
    'restore_demo_vehicle':('test_demo_restoration','test_heritage_source','test_sdk_roster'),
    'preview_cache':('test_preview_cache','test_source_scene_preview','test_workshop_universal_source'),
    'source_garage_ui':('test_preview_cache','test_source_scene_preview','test_workshop_universal_source'),
    'editable_vehicle':('test_editable_vehicle','test_scene_semantics','test_universal_scene_bridge'),
    'native_family_scene':('test_native_family_scene','test_editable_vehicle','test_universal_scene_bridge'),
    'universal_scene_bridge':('test_universal_scene_bridge','test_scene_semantics','test_workshop_universal_source'),
    'qt_editor':('test_editable_vehicle','test_preview_cache'),
    'audit_runtime_composition':('test_runtime_composition_audit',),
    'loose_package':('test_loose_package',),
    'historical_physics':('test_definitive_restoration','test_physics_profile'),
    'native_effect_reference':('test_definitive_restoration','test_heritage_source','test_glass_authoring'),
    'native_states':('test_definitive_restoration','test_heritage_source','test_auto_features'),
    'restore_demo_forester':('test_definitive_restoration','test_heritage_source','test_sdk_roster'),
    'build_sdk_roster':('test_sdk_roster','test_sdk_capacity','test_definitive_restoration'),
    'build_runtime_launcher':('test_sdk_roster','test_definitive_restoration'),
    'collision_comparison':('test_demo_vehicle_audit','test_dx_revision_upgrade'),
    'demo_dx':('test_demo_vehicle_audit','test_dx_revision_upgrade','test_dx_revision_upgrade_cli'),
    'demo_vehicle_audit':('test_demo_vehicle_audit','test_heritage_source'),
    'audit_demo_vehicles':('test_demo_vehicle_audit','test_heritage_source'),
    'heritage_source':('test_heritage_source','test_demo_vehicle_audit','test_auto_features')}


class TimedResult(unittest.TextTestResult):
    def startTest(self,test):self.started=time.perf_counter();super().startTest(test)
    def stopTest(self,test):
        self.timings.append({'test':test.id(),'seconds':time.perf_counter()-self.started});super().stopTest(test)
    def __init__(self,*args,**kwargs):super().__init__(*args,**kwargs);self.timings=[]


def run(tier,modules=(),changed=(),output=None):
    available=sorted(p.stem for p in(ROOT/'tests/synthetic').glob('test_*.py'))
    if tier=='full':selected=available
    elif tier=='focused':
        selected=set(modules)
        for path in changed:
            stem=Path(path).stem
            if stem in available:selected.add(stem)
            elif stem in DEPENDENCIES:selected.update(DEPENDENCIES[stem])
            else:raise ValueError('No dependency mapping for '+path+'; supply explicit --module tests')
        if not selected:raise ValueError('Focused requires --module or --changed')
        selected=sorted(selected)
    else:selected=list(SMOKE if tier=='smoke'else INTEGRATION)
    if any(n not in available for n in selected):raise ValueError('Unknown selected test module')
    suite=unittest.TestSuite(unittest.defaultTestLoader.loadTestsFromName(n)for n in selected)
    start=time.perf_counter();result=unittest.TextTestRunner(verbosity=1,resultclass=TimedResult).run(suite)
    report={'schema':'workshop-test-tier/1','tier':tier,'selected_modules':selected,
            'not_selected_modules':[n for n in available if n not in selected],
            'run':result.testsRun,'failed':len(result.failures),'errors':len(result.errors),
            'skipped':[{'test':t.id(),'reason':why}for t,why in result.skipped],
            'seconds':time.perf_counter()-start,'status':'PASS'if result.wasSuccessful()else'FAIL',
            'slowest':sorted(result.timings,key=lambda x:x['seconds'],reverse=True)[:20]}
    if output:
        output=Path(output)
        if output.exists():raise ValueError('Fresh test report path required')
        output.parent.mkdir(parents=True,exist_ok=True);output.write_text(json.dumps(report,indent=2)+'\n',encoding='utf-8')
    return report


if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('tier',choices=('focused','smoke','integration','full'))
    p.add_argument('--module',action='append',default=[]);p.add_argument('--changed',action='append',default=[])
    p.add_argument('--output',type=Path);args=p.parse_args()
    try:r=run(args.tier,args.module,args.changed,args.output)
    except ValueError as e:p.error(str(e))
    print(json.dumps({k:v for k,v in r.items()if k not in('slowest','not_selected_modules')},indent=2))
    sys.exit(0 if r['status']=='PASS'else 1)
