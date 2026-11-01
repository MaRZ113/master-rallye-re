"""Private V-DEF3 selectable capacity fixture, not a Demo WildCat restoration.

All real vehicle author inputs are frozen. The extra slot is explicitly a
retail Wildcat clone with independent resources, disabled AI and probe labels.
No original executable, archive, resource, accepted project or save is written.
"""
from pathlib import Path
import argparse,json,sys
ROOT=Path(__file__).resolve().parents[1]
sys.path[:0]=[str(ROOT/'src'),str(ROOT/'tools')]
from master_rallye.addon_sdk.heritage_source import create_author
from master_rallye.addon_sdk.project import build_project
from master_rallye.addon_sdk.roster_layout import BASE
from master_rallye.workshop.service import WorkshopProject,write_json
import addon_runtime


def prepare(baseline_candidate,output,retail_root,retail_sma):
    output=addon_runtime._under_research_output(output)
    if output.exists():raise ValueError('Choose a fresh pilot directory')
    config=json.loads((baseline_candidate/'roster-config.json').read_text())
    if config.get('experimental_record_count')!=32:raise ValueError('Expected the accepted 32-record baseline')
    output.mkdir(parents=True)
    author=output/'probe-author'
    create_author(retail_sma.parent,'Wildcat',author,name='T3 SLOT32 PROBE',
        runtime_family='RosterProbe32',physics_donor='Wildcat',stock_audio_profile_id=14,
        retail_sma=retail_sma,family_folder=retail_root/'DataGx/Vehicles/Wildcat',features=None)
    addon=json.loads((author/'addon.json').read_text())
    addon.update(addon_id='roster-t3-slot32-probe',description='V-DEF3 technical retail Wildcat clone. NOT restored Demo TOMCAT. No historical identity claim.')
    addon['frontend'].update(manufacturer='SDK PROBE',model='T3 SLOT32',combined='SDK PROBE T3 SLOT32')
    addon['results']['display_name']='SDK SLOT32 PROBE'
    addon['ai_eligibility']={key:{'enabled':False,'reason':'Selectable capacity canary only; new T3 AI pool not qualified.'}for key in addon['ai_eligibility']}
    write_json(author/'addon.json',addon)
    # Ordinary author compiler remains unchanged (its technical slot27 is
    # rebound by the common roster builder). No new standalone compiler.
    build_project(author,ROOT/'research/vehicles/sdk/capabilities/retail-2001.json',output/'probe-author-build',
                  retail_data_sma=retail_sma,retail_data_root=retail_root)
    config['projects'].append({'project':str(author),'build':str(output/'probe-author-build'),
                               'physical_id':32,'vehicle_class':'T3'})
    config['experimental_record_count']=33
    layout={'T1':BASE['T1'][:],'T2':[7,8,30,9,10,11,12,31,13,27,28,29],
            'T3':[14,32]+list(range(15,26))}
    write_json(output/'runtime-plan/roster-config.json',config)
    # Exercise the same copy-on-write configuration API exposed in Workshop.
    project=WorkshopProject.create(author,output/'workshop',kind='addon')
    project.configure_build({'roster_candidate':str(output/'runtime-plan'),
                             'retail_sma':str(retail_sma),'retail_root':str(retail_root)})
    project.configure_roster(layout,{'32':'T3'})
    return project.build(output/'workshop/builds/first',sdk_root=ROOT,log=print)


if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__)
    for key in ('baseline-candidate','output','retail-root','retail-sma'):p.add_argument('--'+key,type=Path,required=True)
    a=p.parse_args();result=prepare(a.baseline_candidate,a.output,a.retail_root,a.retail_sma)
    print(json.dumps(result,indent=2))
