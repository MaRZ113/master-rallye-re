"""Compact source-backed coverage report; implementation and runtime separated."""
from pathlib import Path
from collections import Counter
import json
import re

PORT=Path(__file__).resolve().parents[1]
DOCS=PORT/'docs/vehicle-model-port1'

def main():
    complete=json.loads((DOCS/'ps2-format-lights/complete-inventory.json').read_text())
    prepared={r['family']:r for r in json.loads((DOCS/'private-model-preparation.json').read_text())['models']}
    partitions=json.loads((DOCS/'race-partitions/partition-evidence.json').read_text())
    parts={r['pc_family']:r for r in partitions['vehicles']}
    header=(PORT/'renderer/reflection_pilot.hpp').read_text()
    existing=Counter(re.findall(r'\{"([^"\n]+)",\s*(?:"[0-9a-f]{64}"|kTataBonnetGeometrySha|kKiaBonnetGeometrySha)',header))
    rows=[]
    for source in complete['inventory']:
        pair=source['pc_pair'];family=source['family']
        pc_family=pair['path'].split('/')[0] if isinstance(pair,dict) else None
        part=parts.get(pc_family)
        row={'ps2_family':family,'pc_family':pc_family,'complete_source_sha256':source['sha256'],
            'complete_decoder':'PASS','prepared_source':'PASS','source_faces':source['source_triangles'],
            'prepared_asset_sha256':prepared[family]['asset_sha256'],'prepared_textures':prepared[family]['texture_count'],
            'frontend_replacement':'BLOCKED_CURRENT_OWNER_JOIN' if family=='WOOLDAND' else 'NOT_IMPLEMENTED',
            'existing_reflection_registry_records':existing[pc_family] if pc_family else 0,
            'new_race_partitions':[],'runtime_validation_new_code':'PENDING_USER',
            'lights':'RESEARCH_ONLY_NO_OVERRIDE','live_poly_budget':'UNKNOWN'}
        if family=='FORESTER':row['pair_note']='DISTINCT_PS2_VEHICLE_NOT_PC_FORESTER_ALIAS'
        if part:
            for d in part['draws']:
                row['new_race_partitions'].append({'source_draw_index':d['draw_index'],
                    'geometry_sha256':d['geometry_sha256'],'source_faces':d['index_count']//3,
                    'carshiny_faces':d['source_face_counts'].get('carshiny',0),
                    'stock_face_categories':{k:v for k,v in d['source_face_counts'].items() if k!='carshiny'},
                    'source_order_runs':len(d['source_ordered_runs']),
                    'implementation':'OPT_IN_NATIVE_SOURCE_INDEX_PARTITION','runtime':'PENDING_USER'})
        rows.append(row)
    output={'schema_version':1,'phase':'PS2-VEHICLE-MODEL-PORT1','status':'PARTIAL',
        'coordinates':'MODEL_LOCAL_GAME_SOURCE','matching_tolerance':.001,'evidence_grade':'CONFIRMED_BY_BYTES_AND_EXE',
        'new_rendering_runtime':'NOT_PERFORMED','source_inventory':{'ps2_complete':29,'pc_complete':26},
        'matrix':rows,'limitations':['No frontend suppression enabled','Unknown/glass/flat/unmatched race faces retain PC Stock',
            'Original native PC attributes remain on race partitions','No lamp/glow implementation',
            'Conditional authored totals do not establish live visibility']}
    (DOCS/'vehicle-coverage.json').write_text(json.dumps(output,indent=2)+'\n')
    lines=['# Vehicle coverage','',
        'Source inventory and implementation are separate. New DLL runtime validation is pending.',
        'COMPLETE counts are authored source faces, not simultaneous menu draw budgets.','',
        '| PS2 family | PC candidate | COMPLETE faces | Private textures | Menu replacement | New race source records |',
        '|---|---|---:|---:|---|---|']
    for r in rows:
        cases=', '.join(str(d['source_draw_index']) for d in r['new_race_partitions']) or (
            'Previous reflection path preserved' if r['existing_reflection_registry_records'] else 'No verified CAR pilot')
        lines.append('|%s|%s|%s|%s|%s|%s|'%(r['ps2_family'],r['pc_family'] or 'UNPAIRED',r['source_faces'],
            r['prepared_textures'],r['frontend_replacement'],cases))
    lines+=['','Detailed per-source hashes/material counts are in `vehicle-coverage.json`.',
        'PS2 FORESTER is distinct from WOOLDAND/PCForester. Unpaired families are not substituted.','']
    (DOCS/'vehicle-coverage.md').write_text('\n'.join(lines))

if __name__=='__main__':main()
