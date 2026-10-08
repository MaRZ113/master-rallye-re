"""Compact GEOM1 metadata selection from ignored full comparison reports.

No complete coordinates or mesh export. Output stays ignored until reviewed
and deliberately copied into the research documentation by the phase author.
"""
from pathlib import Path
import argparse
import json
import geometry_delta as g


def compact(reports,anchors):
    features=[]
    for report in reports:
        course=report['course_pair'];records=report['groups']
        owners={r['source_id']:r['source'] for r in records}
        selected={}
        def add(record):selected[record['delta_id']]=record
        for r in records:
            if r['source_id'].startswith('PS2:') and (g.w.shader_contract(r['source']['material'])['water_mode'] is not None
                    or r['source']['node_offset']==anchors[course]['ps2_node_offset']):add(r)
        for prefix,relations in [('PS2:',('PS2_EXTRA_VISUAL_SOURCE','GEOMETRY_MODIFIED','SAME_SURFACE_DIFFERENT_TRIANGULATION')),
                                 ('PC:',('PC_EXTRA_COMPILED_DRAW',))]:
            for relation in relations:
                candidates=[r for r in records if r['source_id'].startswith(prefix) and r['geometry_relation']==relation]
                for r in sorted(candidates,key=lambda r:(-r['source_triangles'],r['source_id']))[:4]:add(r)
        for r in sorted(selected.values(),key=lambda r:r['delta_id']):
            ports=['REQUIRES_DEEPER_PS2_RE']
            water=r['source_id'].startswith('PS2:') and g.w.shader_contract(r['source']['material'])['water_mode'] is not None
            if water:
                ports=['MATERIAL_ONLY_PORT','RENDERER_ONLY_PORT']
                if course=='TURKEY3':ports.insert(0,'COURSE_VISUAL_GEOMETRY_PORT')
            elif r['geometry_relation']=='PS2_EXTRA_VISUAL_SOURCE':ports.append('COURSE_VISUAL_GEOMETRY_PORT')
            elif r['geometry_relation']=='EXACT_TRIANGLE_MATCH' and r['material_relation']=='SAME_OR_EQUIVALENT_MATERIAL':ports=['NO_PORT_NEEDED']
            features.append({**r,'feature_id':course+':'+r['delta_id'],'course':course,
                'opposite_groups':[{'source_id':k,**{field:value for field,value in owners[k].items()
                    if field not in ('strips','ancestors')}} for k in r['other_group_ids']],
                'source_family':r['source']['representation'],'ps2_geometry_source':report['ps2_source']['decoded_sha256'],
                'pc_geometry_source':report['pc_source']['sha256'],'coordinate_frame':'GAME_SOURCE',
                'matching_tolerance':report['thresholds'],'matching_method':'6-corner permutations or plane/normal-gated union subtraction',
                'transform_confidence':'Independent route anchor; identical authored identity matrices; live matrix UNKNOWN',
                'independent_validation':'Frozen WATER1 and direct source bytes for selected anchors; other surface results diagnostic inference',
                'portability':ports,'implementation_ready':False,
                'open_questions':['Live hierarchy/LOD selection','Collision is a separate representation',
                                  'Unmatched source is not a tree/building/instance count']})
    return {'schema':1,'phase':'PS2-GEOM1','records':features,'runtime_validation':'NOT_PERFORMED',
            'selection':'All selected water records, ordinary ground anchors, four largest records per candidate relation per course; full source coverage is in ignored diagnostics'}


def main():
    ap=argparse.ArgumentParser(description=__doc__)
    ap.add_argument('--directory',type=Path,required=True)
    ap.add_argument('--output',type=Path,required=True)
    args=ap.parse_args();directory=g.local_output(args.directory);out=g.local_output(args.output)
    reports=[json.loads((directory/(course+'.json')).read_text()) for course in g.COURSES]
    anchors=json.loads((directory/'nonwater-anchors.json').read_text())
    g.t.write_json(out,compact(reports,anchors))
    print(json.dumps({'output':str(out),'features':len(compact(reports,anchors)['records'])}))


if __name__=='__main__':main()
