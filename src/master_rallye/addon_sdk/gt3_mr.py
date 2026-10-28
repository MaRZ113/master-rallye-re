"""Explicit GT3-to-common-MR material boundary; no per-vehicle source branches."""
import copy

LIGHTING='GT3 VU lighting parameters require renderer translation'
ENVIRONMENT='runtime external environment texture'

def prepare(scene,policy):
    if set(policy)!={'source_sha256','lighting_fallback','evidence'}or policy['source_sha256']!=scene['source_sha256']:raise ValueError('GT3 translation policy/source mismatch')
    if policy['lighting_fallback']!='native_mr_lighting' or not isinstance(policy['evidence'],str)or not policy['evidence'].strip():raise ValueError('GT3 requires an explicit documented MR lighting approximation')
    draws=[];audit=[]
    for draw in scene['draws']:
        d=dict(draw);d['state']=copy.deepcopy(draw['state']);issues=list(d['issues']);fallbacks=[]
        if LIGHTING in issues:
            issues.remove(LIGHTING)
            fallbacks.append({'mode':'native MR lighting replaces original GT3 VU lighting','source_parameters':d['state']['gt3_parameters']})
        if ENVIRONMENT in issues:
            issues.remove(ENVIRONMENT);issues.append('runtime-generated external texture / texgen unavailable')
            fallbacks.append({'mode':'source environment pass retained for shared exact-triangle pairing; unmatched effects remain unsupported'})
        d['issues']=issues;draws.append(d)
        if fallbacks:audit.append({'shape':d['source_shape'],'packet':d['packet'],'fallbacks':fallbacks})
    return draws,{'source_format':'GT3 ModelSet1','source_sha256':scene['source_sha256'],'policy':policy,'material_approximations':audit,'boundary':'No GT3 VU or runtime texgen parity. Shared MR writer/coverage proofs are reused; source geometry, UVs and alpha remain inputs.'}
