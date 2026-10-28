"""Explicit core-shell selection, affine fit of existing qualified tag101.

This is not an automatic hull generator. Authors select structural body draws
and exclude antennas, spoiler tips, mirrors, crew, wheels and effects. The old
convex topology is retained, with all low-level area/bounds audits unchanged.
"""
import hashlib
from ..dx import parse_dx_bytes
from ..collision_scale import scale_dx_collision
from ..collision_writer import patch_dx_collision_translation
from ..bounds import compute_bounds1339,replace_bounds1339


def rebase_unchanged_core(before,after,definition):
    """Re-pin appearance/crew edits only when collision and core are identical.

    Original whole-file qualification remains mandatory. A replacement body,
    altered core indices/positions, or changed collision cannot authorize a fit.
    """
    import copy
    if hashlib.sha256(before).hexdigest()!=definition['source_sha256']:
        raise ValueError('collision rebase baseline hash differs')
    from ..errors import MasterRallyeError
    try:old,new=parse_dx_bytes(before),parse_dx_bytes(after)
    except MasterRallyeError as error:raise ValueError('collision rebase requires validated models')from error
    if not old.diagnostics.validated or not new.diagnostics.validated:
        raise ValueError('collision rebase requires validated models')
    if before[old.trailing.offset:old.collision.unparsed_offset]!=after[new.trailing.offset:new.collision.unparsed_offset]:
        raise ValueError('collision rebase changed native collision')
    def selected(model):
        records=[]
        for index in definition['core_draw_indices']:
            matches=[d for d in model.physical_draws if d.draw_index==index and d.tag==2]
            if len(matches)!=1:raise ValueError('collision rebase core draw changed')
            draw=matches[0]
            ids=model.draw_global_indices(draw)
            records.append(tuple(model.vertices.positions[i]for i in ids))
        return records
    if selected(old)!=selected(new):raise ValueError('collision rebase changed selected core geometry')
    result=copy.deepcopy(definition);result['source_sha256']=hashlib.sha256(after).hexdigest()
    return result

def fit_collision(raw,definition):
    if hashlib.sha256(raw).hexdigest()!=definition['source_sha256']:raise ValueError('collision fitting source hash differs')
    model=parse_dx_bytes(raw);hull=model.collision.convex_hull
    if not model.diagnostics.validated or not hull:raise ValueError('collision fitting requires validated tag101')
    selected=[]
    for index in definition['core_draw_indices']:
        matches=[d for d in model.physical_draws if d.draw_index==index and d.tag==2]
        if len(matches)!=1:raise ValueError('collision core draw is absent or not a leaf')
        d=matches[0];selected.extend(model.vertices.positions[d.vertex_base+i] for i in model.local_indices[d.index_start:d.index_start+d.index_count])
    bounds=lambda points:[[f(p[k] for p in points) for k in range(3)] for f in (min,max)]
    before=bounds(hull.representation_a.geometry_a.vertices);target=bounds(selected)
    target=[[target[j][k]+(-1 if j==0 else 1)*definition['padding_m'][k] for k in range(3)] for j in range(2)]
    factors=[(target[1][k]-target[0][k])/(before[1][k]-before[0][k]) for k in range(3)]
    if any(not .5<=s<=1.5 for s in factors):raise ValueError('collision fit exceeds conservative [0.5,1.5] affine guard')
    scaled=scale_dx_collision(raw,factors,before[0]);delta=[target[0][k]-before[0][k] for k in range(3)]
    translated=patch_dx_collision_translation(scaled['data'],delta);final=parse_dx_bytes(translated.data)
    footer=compute_bounds1339(final.vertices.positions,final.collision.convex_hull,offset=final.collision.unparsed_offset)
    out=replace_bounds1339(translated.data,footer,footer_offset=final.collision.unparsed_offset)
    parsed=parse_dx_bytes(out)
    if not parsed.diagnostics.validated or parsed.vertices!=model.vertices or parsed.uv_sets!=model.uv_sets or parsed.physical_draws!=model.physical_draws or parsed.local_indices!=model.local_indices:raise ValueError('collision fit altered render structure')
    after=bounds(parsed.collision.convex_hull.representation_a.geometry_a.vertices)
    if any(abs(after[j][k]-target[j][k])>2e-5 for j in range(2) for k in range(3)):raise ValueError('collision target bounds mismatch')
    return out,{'source_sha256':definition['source_sha256'],'output_sha256':hashlib.sha256(out).hexdigest(),
        'core_draw_indices':definition['core_draw_indices'],'evidence':definition['evidence'],'before_aabb_m':before,'after_aabb_m':after,
        'scale':factors,'translation_m':delta,'render_bytes_unchanged':True,'topology_preserved':True,
        'boundary':'affine donor hull approximation to explicitly selected core shell; obstacle, grounding and damage contacts require gameplay confirmation'}
