"""Opt-in RAV4 derived resources; accepted pilot/default authoring unchanged."""
from pathlib import Path
from . import universal_vehicle_scene as u
from .dxt import parse_dxt_bytes
from .addon_sdk.auto_features import feed
from .michelin_native_pilot import profile,qualified,semantic_parts,PANES,SCENES
from .universal_scene_bridge import compile_scene
from .michelin_lamp_coverage import rav4_coverage
from .material_derivation import transparent_edge_padding,lens_textures


def wheel_resources(scene_path, original_assets):
    """Change only the one original indexed rim's zero-alpha RGB samples."""
    scene=qualified(scene_path);result=compile_scene(scene_path,profile(scene_path))
    material=next(m for m in scene['meshes'] if m['id']=='wheel-texture-003')['material_id']
    row=result['report']['materials'][material]
    texture_id=row['source_texture_id'];tex=next(t for t in scene['textures']if t['id']==texture_id)
    if not tex['source_channels'].get('native_index0_coverage'):
        raise ValueError('Original qualified indexed rim coverage required')
    name=row['native_textures'][0]+'.dxt'
    raw=u.read_bounded(Path(original_assets)/name,u.MAX_OUTPUT_BYTES)
    if u.sha(raw)!=row['native_dxt_sha256']:raise ValueError('Accepted wheel texture differs from source baseline')
    decoded=parse_dxt_bytes(raw)
    pixels,report=transparent_edge_padding(decoded.bgra,decoded.width,decoded.height,radius=8)
    if decoded.bgra[3::4]!=pixels[3::4]:raise ValueError('Wheel alpha changed')
    for i in range(decoded.width*decoded.height):
        if decoded.bgra[4*i+3] and decoded.bgra[4*i:4*i+4]!=pixels[4*i:4*i+4]:raise ValueError('Visible wheel pixels changed')
    return {name:feed(pixels,decoded.width,decoded.height)},dict(report,source_texture_id=texture_id,
        source_rgba_sha256=tex['rgba_sha256'],native_before_sha256=u.sha(raw),geometry_uv_material_state_changed=False)


def lamp_resources(scene_path, original_assets):
    """Preserve original opaque surface in both cases; alpha-mask ON overlays."""
    from .scene_dx_writer import write_scene_dx
    from .addon_sdk.native_states import author_states
    scene=qualified(scene_path);coverage=rav4_coverage(scene,u.sha(Path(scene_path).read_bytes()))
    result=compile_scene(scene_path,profile(scene_path));parts,panes,old_lamp,_=semantic_parts(result)
    rear_index=next(i for i,r in enumerate(result['report']['body_draws'])if r['mesh_id']==coverage['mesh_id'])
    rear=result['body_parts'][rear_index]
    # Reunite the old recipe's78+12 partition into its unchanged90-face surface.
    parts=[p for p in parts if p.textures!=rear.textures]
    lamp_index=len(parts);parts.append(rear)
    tex=parse_dxt_bytes(u.read_bounded(Path(original_assets)/(rear.textures[0]+'.dxt'),u.MAX_OUTPUT_BYTES))
    lit,glow,pixels=lens_textures(tex.bgra,tex.width,tex.height,coverage['contours'])
    # The base surface remains visible. The unlit overlay must have zero alpha
    # outside the exact contour, including white paint on shared large faces.
    lit=bytearray(lit);allowed=set(pixels)
    for i in range(tex.width*tex.height):
        if i not in allowed:lit[4*i:4*i+4]=bytes(4)
    lit_name='mr-rav4-red-lens-v2-lit-tga';glow_name='mr-rav4-red-lens-v2-glow-tga'
    current=u.read_bounded(Path(original_assets)/'car.dx',u.MAX_OUTPUT_BYTES)
    raw=write_scene_dx(current,parts)
    recipe={'source_sha256':u.sha(raw),'panes':[{'label':name,'source_draw':i,
        'triangles':list(range(len(parts[i].geometry.triangles))),
        'broken_uv_axes':[0,1]if name in('screenfront','screenrear')else[2,1],
        'broken_texture':'mr-michelin-rav4-cracks-tga'}for name,i in panes.items()],
        'brake':{'source_draw':lamp_index,'triangles':coverage['source_face_ids'],
            'lit_texture':lit_name,'glow_texture':glow_name,'mode':'masked_overlay',
            'evidence':coverage['evidence']}}
    native,states=author_states(raw,recipe)
    resources={'car.dx':native,lit_name+'.dxt':feed(lit,tex.width,tex.height),
               glow_name+'.dxt':feed(glow,tex.width,tex.height)}
    return resources,{'coverage':coverage,'states':states,'recipe':recipe,
        'original_off_surface_preserved':True,'original_complete_frontend_unchanged':True,
        'depth_overlay_runtime':'D3D8 OWNER COMPARISON PENDING'}
