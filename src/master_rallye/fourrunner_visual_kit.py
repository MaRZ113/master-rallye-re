"""Owner-rejected Visual Polish options are retained as explicit quality gates.

The historical implementation and private comparison candidates remain at
450eb5d. None of its five optional geometry/material experiments is qualified
for new production builds. Source Fidelity, glass and lower lamps are separate.
"""
import hashlib
from pathlib import Path

OPTIONS=('paint_reflection','mirror_insets','cabin','rear_glazing','underbody_frame')
REJECTED={
    'paint_reflection':'Partial whole-triangle atlas coverage creates patchy reflected body surfaces; continuous native paint pass unqualified.',
    'mirror_insets':'Three source cap triangles are not an independently qualified reflective mirror; original56-triangle meshes must remain intact.',
    'cabin':'Additional3D steering duplicates the baked dashboard wheel; original controls/artwork ownership unresolved.',
    'rear_glazing':'UV-only rear masks and an uncontained backing cuboid failed owner D3D8 review; retain original opaque rear glazing.',
    'underbody_frame':'Body-fixed beams do not connect moving wheels; no qualified spanning axle/suspension solver.'}


def options(value):
    if value is None:return dict.fromkeys(OPTIONS,False)
    if not isinstance(value,dict)or set(value)-set(OPTIONS)or any(type(v)is not bool for v in value.values()):
        raise ValueError('Unknown or non-boolean MR visual option')
    enabled=[key for key,v in value.items()if v]
    if enabled:
        raise ValueError('Owner-rejected D3D8 visual options cannot be enabled: '+
                         '; '.join(key+': '+REJECTED[key]for key in enabled))
    return dict.fromkeys(OPTIONS,False)


def apply(parts,result,retail_root,retail_sma,assets,value,semantic_report):
    """Keep the all-options-off assembly exact; reject before any output write."""
    opts=options(value)
    return list(parts),[0],{'schema':'mr-visual-kit/2','options':opts,'components':[],
        'qualification':'STABLE_OPTIONS_OFF_NEW_CANDIDATE_OWNER_TEST_PENDING',
        'owner_rejected_features':REJECTED.copy(),
        'physics_hubs_ride_height_unchanged':True,'original_source_unchanged':True,
        'source_scene_sha256':result['report']['source_scene_sha256'],
        'implementation_sha256':hashlib.sha256(Path(__file__).read_bytes()).hexdigest()}
