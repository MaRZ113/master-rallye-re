"""Bounded independent input integrity checks; metadata outputs only."""
from pathlib import Path
import hashlib
import importlib.util
import json
import sys

PORT=Path(__file__).resolve().parents[1]
ROOT=PORT.parents[1]
DOCS=PORT/'docs/vehicle-model-port1'

def sha(path):return hashlib.sha256(path.read_bytes()).hexdigest()

def main():
    sys.path.insert(0,str(ROOT/'ps2-research/tools'))
    import water_runtime as w
    from course_delta import EXPECTED
    ps2=Path(r'D:/Game/Master Rallye PS2');w.verify_inputs(ps2)
    pc=Path(r'D:/Game/Master Rallye/corpora/retail/Data.sma_unpacked/DataGx/Vehicles')
    source=json.loads((DOCS/'frontend-identity/source-and-live-evidence.json').read_text())
    records=source['source_inventory']['complete_resources']
    # All26 COMPLETE plus the six changed CAR inputs are rehashed at closeout.
    expected={r['path']:r['sha256'] for r in records}
    race=json.loads((DOCS/'race-partitions/partition-evidence.json').read_text())
    for r in race['vehicles']:expected[r['pc_source']['path']]=r['pc_source']['sha256']
    checked=[]
    for path,digest in sorted(expected.items()):
        actual=sha(pc/path)
        if actual!=digest:raise ValueError('Original PC source changed: '+path)
        checked.append({'path':path,'sha256':actual})
    prepared=json.loads((DOCS/'private-model-preparation.json').read_text())
    spec=importlib.util.spec_from_file_location('private_models',PORT/'tools/prepare_vehicle_models.py')
    m=importlib.util.module_from_spec(spec);spec.loader.exec_module(m)
    for row in prepared['models']:
        path=PORT/row['asset']
        if sha(path)!=row['asset_sha256']:raise ValueError('Private prepared asset changed')
        if m.validate(path.read_bytes())['source_sha256']!=row['source_sha256']:raise ValueError('Private source mismatch')
    result={'schema_version':1,'canonical_ps2_inputs':{n:{'sha256':h,'size':(ps2/n).stat().st_size} for n,h in EXPECTED.items()},
        'checked_pc_sources':checked,'private_prepared_models_verified':len(prepared['models']),
        'result':'PASS','scope':'All26 PC COMPLETE and the6 changed CAR inputs; read-only protected retail originals',
        'runtime_proof':False}
    (DOCS/'source-integrity.json').write_text(json.dumps(result,indent=2)+'\n')
    print(json.dumps({'result':'PASS','ps2_inputs':len(EXPECTED),'pc_sources':len(checked),'private_models':len(prepared['models'])}))

if __name__=='__main__':main()
