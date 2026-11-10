"""Blender integration qualification; source XML, fresh output, report after --."""
import json
import hashlib
import sys
from pathlib import Path
import bpy

repo = Path(__file__).resolve().parents[2]
args = sys.argv[sys.argv.index('--')+1:]
if len(args)==4:
    sys.path.insert(0,args[3])
else:
    sys.path[:0] = [str(repo / 'src'), str(repo / 'blender')]
import master_rallye_io
from master_rallye_io.course_studio import _session, _sync, _root, _contract, CourseStudio
if len(args)==4:assert CourseStudio.__module__.startswith('master_rallye_io.vendor.')

qualified_sources=[repo/'src/master_rallye'/name for name in ('course_studio.py','course_marker_builder.py','course_rigid.py','course_features.py','course_sdk.py')]
qualified_sources += [repo/'blender/master_rallye_io'/name for name in ('__init__.py','course_studio.py','operators/import_course_xml.py')]
source_hashes={str(p.relative_to(repo)):hashlib.sha256(p.read_bytes()).hexdigest() for p in qualified_sources}

source, staging, report = args[:3]
master_rallye_io.register()
assert bpy.ops.mr.course_studio_open(filepath=source, load_textures=True) == {'FINISHED'}
print('STUDIO_SMOKE imported',flush=True)
root, session = _session(bpy.context)
assert bpy.ops.mr.course_studio_validate() == {'FINISHED'}
assert bpy.ops.mr.course_studio_bsp() == {'FINISHED'}
assert bpy.ops.mr.course_studio_probe() == {'FINISHED'}
assert bpy.ops.mr.course_studio_rigid(filepath=r'D:\Game\Master Rallye\PS2Grass\PS2RigidProps.ps2rgd') == {'FINISHED'}
_, session, _ = _sync(bpy.context)
no_op = session.editor.export()[0] == session.project.resources.race_test_xml.read_bytes()
assert no_op
obj = next(o for o in root.all_objects if o.get('mr_studio_geometry'))
marker = next(o for o in root.all_objects if o.get('mr_race_logic_object_type') == 'area_marker' and o.get('mr_race_logic_editable'))
marker.location.x += 1.0
_, session, _ = _sync(bpy.context)
assert session.editor.mutation_count == 1
obj.data.vertices[0].co.x += 0.25
_, session, _ = _sync(bpy.context)
assert session.geometry != session.project.resources.render_dx.read_bytes()
route = next(o for o in root.all_objects if o.get('mr_race_logic_object_type') == 'route_marker' and o.get('mr_marker_position_editable'))
route.location.x += 0.5
limit = next(o for o in root.all_objects if o.get('mr_race_logic_object_type') == 'limit_marker' and o.get('mr_marker_position_editable'))
limit.location.x += 0.25
_, session, _ = _sync(bpy.context)
assert session.editor.mutation_count == 3
saved_rotation=route.rotation_euler.copy()
route.rotation_euler.z+=0.1
try:
    _sync(bpy.context)
    raise AssertionError('Unsupported Marker Dir rotation was accepted')
except ValueError as error:
    assert 'Unsupported helper transforms' in str(error)
route.rotation_euler=saved_rotation
_sync(bpy.context)
print('STUDIO_SMOKE bounded marker/geometry/route edits',flush=True)
# Structural operations rebuild only the native helper hierarchy, retaining edits.
bpy.context.scene.cursor.location = (100, -100, 20)
assert bpy.ops.mr.course_studio_marker(action='SPLIT') == {'FINISHED'}
_, session, _ = _sync(bpy.context)
assert len(session.editor.split_status) == 4
selected = next(o for o in root.all_objects if o.get('mr_race_logic_object_type') == 'split_center' and o.get('mr_split_time_id') == 3)
bpy.context.view_layer.objects.active = selected
assert bpy.ops.mr.course_studio_marker(action='DELETE') == {'FINISHED'}
assert bpy.ops.mr.course_studio_marker(action='REORDER') == {'FINISHED'}
_, session, _ = _sync(bpy.context)
assert len(session.editor.split_status) == 3
assert bpy.ops.mr.course_studio_route_proposal(role='AI_PROPOSAL') == {'FINISHED'}
for asset in ('PS2SplineObjects.ps2spl', 'PS2Birds.ps2bird', 'France1Grass.ps2grass', 'France1Shrubs.ps2grass'):
    assert bpy.ops.mr.course_studio_feature(filepath=str(Path(r'D:\Game\Master Rallye\PS2Grass') / asset)) == {'FINISHED'}
assert bpy.ops.mr.course_studio_collision_check() == {'FINISHED'}
bpy.context.scene.mr_studio_output = staging
from master_rallye_io.library import parse_dxt,write_png
material_index=next(i for i,m in enumerate(obj.data.materials) if m and m.get('mr_dxt_source'))
bpy.context.view_layer.objects.active=obj;obj.active_material_index=material_index
texture_png=Path(report).with_suffix('.png')
write_png(parse_dxt(Path(obj.active_material['mr_dxt_source'])),texture_png)
assert bpy.ops.mr.course_studio_texture(filepath=str(texture_png)) == {'FINISHED'}
assert bpy.ops.mr.course_studio_export() == {'FINISHED'}
assert (Path(staging)/'editor-routes.json').is_file()
print('STUDIO_SMOKE staged',flush=True)
blend = Path(report).with_suffix('.blend')
for image in bpy.data.images:
    if image.get('mr_studio_owner') and not image.packed_file:
        image.pack()
bpy.ops.wm.save_as_mainfile(filepath=str(blend))
checks = dict(status='PASS', no_op_xml_byte_identical=no_op, exported_resources=len(session.files),
              vertices=len(obj.data.vertices), objects=len(root.all_objects), marker_mutations=session.editor.mutation_count,
              bsp_nodes=len(session.collision().nodes), source=source)
master_rallye_io.unregister()
master_rallye_io.register()
_, reopened, _ = _sync(bpy.context)
assert len(reopened.editor.split_status) == 3
checks['register_unregister_reload'] = 'PASS'
checks['marker_add_delete_reorder'] = 'PASS'
checks['ps2_spline_birds_grass_shrubs'] = 'PASS'
foreign=bpy.data.objects.new('Unrelated owner object',None)
next(c for c in root.children).objects.link(foreign)
assert bpy.ops.mr.course_studio_close() == {'FINISHED'}
assert not any(o.get('mr_studio_geometry') for o in bpy.data.objects)
checks['close_owned_scene'] = 'PASS'
checks['native_texture_preview_and_staging']='PASS'
checks['neutral_alternative_route']='PASS'
checks['unsupported_helper_rotation_rejected']='PASS'
checks['packaged_vendor_import']=CourseStudio.__module__
assert bpy.data.objects.get('Unrelated owner object') is foreign
checks['foreign_object_preserved']='PASS'
checks['source_sha256']=source_hashes
assert source_hashes=={str(p.relative_to(repo)):hashlib.sha256(p.read_bytes()).hexdigest() for p in qualified_sources}
master_rallye_io.unregister()
Path(report).write_text(json.dumps(checks, indent=2))
print('COURSE_STUDIO_BLENDER_PASS', json.dumps(checks))
