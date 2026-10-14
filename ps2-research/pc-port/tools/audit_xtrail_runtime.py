"""Bounded retained A/B evidence; current runtime pointers are never constants."""
from pathlib import Path
import hashlib,json
PORT=Path(__file__).resolve().parents[1];DOCS=PORT/'docs/xtrail-fidelity'
LOGS=Path(r'D:/Game/Master Rallye Pristine/MRRRenderer/logs')
FILES={'race_model_1':'session-20261014-052545-27240.jsonl','race_model_0':'session-20261014-052705-4888.jsonl'}

def sha(data):return hashlib.sha256(data).hexdigest()

def inspect(path):
    session=None;events=[];bad=0
    for line in path.read_text().splitlines():
        try:r=json.loads(line)
        except json.JSONDecodeError:bad+=1;continue
        if r.get('type')=='session':session={k:r.get(k) for k in ('exe_sha256','proxy_sha256','schema_version')}
        if r.get('type') in ('ps2_vehicle_material_partition','ps2_reflection_material') and r.get('vehicle')=='Xtrail':
            if len(events)<16:events.append(r)
    if not session:raise ValueError('Missing session identity')
    return {'file':path.name,'sha256':sha(path.read_bytes()),'session':session,'events':events,'unparsed_lines':bad,
        'identity_rule':'RETAINED_OBSERVATION_NOT_PERSISTENT_POINTER_OR_ORDINAL'}

def main():
    images=[Path(r'C:/Users/MaRZ/Documents/ShareX/Screenshots/2026-10/MRallye_racemodel_0.jpg'),
        Path(r'C:/Users/MaRZ/Documents/ShareX/Screenshots/2026-10/MRallye_racemodel_1.jpg'),
        Path(r'C:/Games/PCSX2_Nightly/snaps/Master Rallye_SLES-50906_20261014153132.png'),
        Path(r'C:/Games/PCSX2_Nightly/snaps/Master Rallye_SLES-50906_20261014153112-crop.png')]
    result={'schema_version':1,'sessions':{name:inspect(LOGS/file) for name,file in FILES.items()},
        'supplied_images':[{'file':p.name,'sha256':sha(p.read_bytes()),'grade':'USER_RUNTIME_OBSERVATION'} for p in images],
        'new_dll_runtime':'NOT_PERFORMED','limits':['Screenshots not frame-ID joined','PS2 menu is COMPLETE; cropped PS2 scene is CAR',
            'Different skies and camera/lighting prevent pixel/parity measurement','F10 source layout does not prove uploaded bytes for unhandled meshes']}
    (DOCS/'runtime-ab-evidence.json').write_text(json.dumps(result,indent=2)+'\n')
    print('Saved compact A/B identity/state evidence; no original logs or images copied')

if __name__=='__main__':main()
