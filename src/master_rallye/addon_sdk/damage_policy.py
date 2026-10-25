"""Keep coverage alpha distinct from native damage's reflection-weight alpha.

The original deformer moves positions and darkens RGB coherently, but also
fades diffuse alpha for RemoveEnvMap. Imported alpha-test/blend draws can use
that same byte for surface coverage. This metadata never disables deformation.
"""
import hashlib
from master_rallye.dx import parse_dx_bytes


def alpha_ownership(data: bytes) -> dict:
    model=parse_dx_bytes(data)
    if not model.diagnostics.validated or len(model.uv_sets)!=1:
        raise ValueError('damage policy requires a valid single-UV vehicle')
    mask=bytearray(model.vertex_count);opaque=set();coverage=set()
    for draw in model.physical_draws:
        ids=set(model.draw_global_indices(draw))
        if draw.flags_0x20[0] and draw.flags_0x20[2]:coverage.update(ids)
        else:opaque.update(ids)
    for i in coverage:mask[i]=1
    if not coverage:raise ValueError('no coverage-alpha vertices need a damage adapter')
    return {'schema_version':1,'model_sha256':hashlib.sha256(data).hexdigest(),
        'vertex_count':model.vertex_count,'coverage_vertex_count':len(coverage),
        'opaque_vertex_count':len(opaque),'mixed_vertex_count':len(coverage&opaque),
        'mask_hex':mask.hex(),'policy':'restore original alpha for coverage vertices after native damage; preserve moved positions, RGB darkening and opaque reflection fading',
        'mixed_policy':'coverage wins; shared opaque reflection fading is approximated only on overlapping vertices'}
