"""Integrated Course Studio UI over the canonical SDK transaction model."""
from __future__ import annotations
import hashlib
import json
import math
from pathlib import Path

import bpy
from bpy.props import StringProperty, IntProperty, BoolProperty, EnumProperty, FloatProperty
from bpy_extras.io_utils import ImportHelper
from mathutils import Matrix, Vector

from .blender_mesh import create_collection, import_dx_resource
from .library import position_to_blender, blender_position_to_source, replace_texture
from .operators.export_course_race_logic import _apply_scene_edits

try:
    from master_rallye.course_studio import CourseStudio, bsp_ray_intervals, SUPPORT
    from master_rallye.course_rigid import read_rigid_asset, text as rigid_text
    from master_rallye import course_marker_builder as marker_builder
    from master_rallye.course_features import read_proxy_features, scene_features
except ModuleNotFoundError:
    from .vendor.master_rallye.course_studio import CourseStudio, bsp_ray_intervals, SUPPORT
    from .vendor.master_rallye.course_rigid import read_rigid_asset, text as rigid_text
    from .vendor.master_rallye import course_marker_builder as marker_builder
    from .vendor.master_rallye.course_features import read_proxy_features, scene_features

SESSIONS = {}
LAYERS = ('Visual Terrain', 'Static Objects', 'Collision', 'Start & Finish', 'Checkpoints', 'RaceLine', 'Limits', 'AI', 'Diagnostics')


def _root(context):
    name = context.scene.get('mr_studio_root', '')
    root = bpy.data.collections.get(name)
    if root is None or not root.get('mr_studio_source'):
        raise ValueError('Open a Course Studio project first')
    return root


def _session(context):
    root = _root(context)
    key = root.name
    if key not in SESSIONS:
        session = CourseStudio(root['mr_studio_source'], resource_root=root.get('mr_studio_resource_root') or None,
                               race_id=root.get('mr_studio_race_id', -1) if root.get('mr_studio_race_id', -1) >= 0 else None)
        if session.hashes != json.loads(root['mr_studio_hashes']):
            raise ValueError('Source provenance changed since this blend was saved; reload project')
        SESSIONS[key] = session
    return root, SESSIONS[key]


def _contract(obj):
    mesh = obj.data
    # Preserve native topology/order, UVs, materials, draw bindings and raw source attributes.
    result = [tuple(tuple(p.vertices) for p in mesh.polygons), tuple(p.material_index for p in mesh.polygons),
              tuple(m.name if m else '' for m in mesh.materials),
              tuple((uv.name, tuple(tuple(p.uv) for p in uv.data)) for uv in mesh.uv_layers)]
    for attr in mesh.attributes:
        if attr.name in ('position', '.select_vert', '.select_edge', '.select_poly', '.hide_vert', '.hide_edge', '.hide_poly'):
            continue
        values = []
        for value in attr.data:
            if hasattr(value, 'value'): values.append(value.value)
            elif hasattr(value, 'vector'): values.append(tuple(value.vector))
            elif hasattr(value, 'color'): values.append(tuple(value.color))
        result.append((attr.name, attr.domain, attr.data_type, values))
    return hashlib.sha256(repr(result).encode()).hexdigest()


def _sync(context):
    root, session = _session(context)
    if context.mode != 'OBJECT': raise ValueError('Return to Object Mode before validation/export')
    context.view_layer.update()
    meshes = [o for o in root.all_objects if o.get('mr_studio_geometry')]
    if len(meshes) != 1: raise ValueError('Visual Terrain object missing or duplicated')
    obj = meshes[0]
    if obj.modifiers: raise ValueError('Apply no modifiers: course writer supports same-order position edits only')
    if _contract(obj) != obj['mr_studio_mesh_contract']:
        raise ValueError('Unsupported topology, UV, material or native draw-binding edits; restore before export')
    session.set_visual_positions([blender_position_to_source(obj.matrix_world @ v.co) for v in obj.data.vertices])
    logic = [c for c in _walk(root) if c.get('mr_xml_collection_kind') == 'race_logic_root']
    if len(logic) != 1: raise ValueError('Project must have one intact RaceTest helper hierarchy')
    # New editor each time avoids stale pending mutations after undo.
    working=bpy.data.texts.get(root.get('mr_studio_working_xml',''))
    if working and hashlib.sha256(working.as_string().encode('utf-8')).hexdigest()!=root.get('mr_studio_working_sha'):
        raise ValueError('Working XML changed outside Marker Builder; reload before export')
    session.editor = type(session.editor)(working.as_string().encode('utf-8'),str(session.project.resources.race_test_xml)) if working else type(session.editor).from_path(session.project.resources.race_test_xml)
    session.structural_audit=json.loads(root.get('mr_studio_structural_audit','[]'))
    session.feature_metadata=json.loads(root.get('mr_studio_features','[]'))
    session.replacements={}
    for source,draft in json.loads(root.get('mr_studio_texture_drafts','{}')).items():session.stage_texture(source,draft)
    session.editor_routes=[]
    for route in root.all_objects:
        if route.get('mr_studio_route_role'):
            paths=[]
            for spline in route.data.splines:
                points=[blender_position_to_source(route.matrix_world@Vector(p.co[:3])) for p in spline.points]
                if len(points)<2 or not all(math.isfinite(v) for p in points for v in p):raise ValueError('Invalid editor route')
                paths.append(points)
            session.editor_routes.append(dict(name=route.name,role=route['mr_studio_route_role'],paths=paths,native_export=False))
    warnings = _apply_scene_edits(logic[0], session.editor)
    if warnings:
        raise ValueError('Unsupported helper transforms: ' + '; '.join(warnings))
    for o in root.all_objects:
        if o.get('mr_studio_inspect_matrix'):
            before=json.loads(o['mr_studio_inspect_matrix'])
            if any(abs(o.matrix_world[i][j]-before[i][j]) > max(1e-5, abs(before[i][j])*2e-7) for i in range(4) for j in range(4)):
                raise ValueError(f'{o.name}: INSPECT_ONLY object transform changed')
            if o.type=='MESH' and _inspect_contract(o)!=o['mr_studio_inspect_contract']:
                raise ValueError(f'{o.name}: INSPECT_ONLY mesh changed')
        if o.type == 'MESH' and not (o.get('mr_studio_geometry') or o.get('mr_editor_only') or o.get('mr_studio_inspect_matrix') or o.get('mr_course_helper_kind')):
            raise ValueError(f'{o.name}: unbound new mesh cannot be cooked by this export contract')
    return root, session, warnings


def _walk(root):
    yield root
    for child in root.children: yield from _walk(child)


def _inspect_contract(obj):
    return hashlib.sha256((_contract(obj) + repr([tuple(v.co) for v in obj.data.vertices])).encode()).hexdigest()


def _layer(root, name):
    return next(c for c in _walk(root) if c.get('mr_studio_layer') == name)


def _dispose(root):
    for child in list(root.children): _dispose(child)
    for obj in list(root.objects):
        data = obj.data
        bpy.data.objects.remove(obj, do_unlink=True)
        if data and data.users == 0:
            if isinstance(data, bpy.types.Mesh): bpy.data.meshes.remove(data)
            elif isinstance(data, bpy.types.Curve): bpy.data.curves.remove(data)
    bpy.data.collections.remove(root)


def _release_foreign(root):
    """Unlink user-added scene objects without deleting their datablocks."""
    collections=list(_walk(root));owned=set(c.as_pointer() for c in collections)
    for obj in list(root.all_objects):
        if obj.get('mr_studio_owner')==root.name:continue
        for collection in list(obj.users_collection):
            if collection.as_pointer() in owned:collection.objects.unlink(obj)
        if not obj.users_collection:bpy.context.scene.collection.objects.link(obj)


def _rehome(collection, parent):
    for p in bpy.data.collections:
        if collection.name in p.children: p.children.unlink(collection)
    if collection.name in bpy.context.scene.collection.children:
        bpy.context.scene.collection.children.unlink(collection)
    parent.children.link(collection)


def _report(context, findings):
    payload = json.dumps([dict(severity=f.severity, path=f.path, message=f.message) for f in findings], indent=2)
    text = bpy.data.texts.get('MR Course Validation') or bpy.data.texts.new('MR Course Validation')
    text.clear(); text.write(payload)
    context.scene['mr_studio_findings']=payload
    context.scene['mr_studio_validation'] = f'{sum(f.severity == "ERROR" for f in findings)} errors; {sum(f.severity == "WARNING" for f in findings)} warnings; {sum(f.severity == "UNKNOWN" for f in findings)} unknowns'


def _native_matrix(rows):
    native=Matrix(rows).transposed()
    conversion=Matrix(((1,0,0,0),(0,0,-1,0),(0,1,0,0),(0,0,0,1)))
    return conversion@native


def _egg_inspector(root,session):
    layer=create_collection('Native Eggs and Matrices',_layer(root,'Diagnostics'))
    for egg in session.project.race_logic.source_document.eggs:
        obj=bpy.data.objects.new(egg.name or f'Egg {egg.ordinal}',None);layer.objects.link(obj)
        obj.empty_display_type='PLAIN_AXES';obj.empty_display_size=1
        matrix=egg.matrix()
        if matrix and all(row is not None for row in matrix.rows):obj.matrix_world=_native_matrix(matrix.rows)
        bpy.context.view_layer.update()
        obj['mr_studio_inspect_matrix']=json.dumps([list(row) for row in obj.matrix_world])
        obj['mr_native_egg_path']=egg.xml_path;obj['mr_native_model']=egg.model_name or ''
        obj['mr_native_matrix']=json.dumps(dict(matrix.attributes)) if matrix else ''
        obj['mr_native_components']=json.dumps([c.tag for c in egg.components()]);obj['mr_support']='INSPECT_ONLY'
        obj.hide_set(True)
    features=scene_features(session.project)
    root['mr_studio_features']=json.dumps(features)
    for feature in features:
        if feature['kind']!='sound_trigger' or feature['center'] is None:continue
        helper=bpy.data.objects.new('Sound / '+str(feature['name']),None);layer.objects.link(helper)
        helper.location=position_to_blender(feature['center']);helper.empty_display_type='SPHERE';helper.empty_display_size=2
        helper['mr_feature_metadata']=json.dumps(feature);helper['mr_support']='INSPECT_ONLY'
        context=bpy.context;context.view_layer.update();helper['mr_studio_inspect_matrix']=json.dumps([list(row) for row in helper.matrix_world])
        # Glyph size is an editor icon, not an invented audible radius.
        helper['mr_preview_note']='sound anchor icon; source trigger fields retained; no radius inferred'
    for obj in _layer(root,'Visual Terrain').objects:
        for draw in session.project.render._parsed_model.physical_draws:
            slot=obj.get(f'mr_draw_material_slot_{draw.draw_index}')
            if slot is None or slot>=len(obj.data.materials):continue
            material=obj.data.materials[slot]
            numbers={candidate.number for candidate in draw.material_candidates}
            matching=[f for f in features if f['kind']=='surface_type' and f['material_number'] in numbers]
            if material:material['mr_surface_source_inventory']=json.dumps(matching)


def _restore_neutral_routes(root,session):
    for route in session.editor_routes:
        curve=bpy.data.curves.new(route['name'],'CURVE');curve.dimensions='3D';curve.bevel_depth=0.08
        for points in route['paths']:
            spline=curve.splines.new('POLY');spline.points.add(len(points)-1)
            for target,point in zip(spline.points,points):target.co=(*position_to_blender(point),1)
        obj=bpy.data.objects.new(route['name'],curve);_layer(root,'AI').objects.link(obj)
        obj['mr_studio_route_role']=route['role'];obj['mr_editor_only']=True;obj['mr_support']='EDITOR_ONLY'


def _organize(root):
    for c in list(_walk(root)):
        if c.get('mr_xml_collection_kind')=='egg_list:SplitTimes':_rehome(c,_layer(root,'Checkpoints'))
        if str(c.get('mr_xml_collection_kind','')).startswith('marker_list:'):
            names={str(o.get('mr_source_list_name',o.get('mr_race_logic_area',''))) for o in c.all_objects}
            target='Start & Finish' if names & {'StartArea','FinishArea'} else 'RaceLine' if 'RaceLine' in names else 'Limits' if any('Limit' in n for n in names) else None
            if target:_rehome(c,_layer(root,target))
    logic=next(c for c in _walk(root) if c.get('mr_xml_collection_kind')=='race_logic_root')
    root['mr_studio_logic']=logic.name
    for name in LAYERS:_rehome(_layer(root,name),logic)


def _reload_logic(context,root,session,payload):
    _release_foreign(root)
    # Move persistent layers out before disposing only generated race helpers.
    for name in LAYERS:_rehome(_layer(root,name),root)
    for name in ('Start & Finish','RaceLine','Limits','Checkpoints'):
        for child in list(_layer(root,name).children):_dispose(child)
    for child in list(root.children):
        if not child.get('mr_studio_layer'):_dispose(child)
    text=bpy.data.texts.get(root.get('mr_studio_working_xml',''))
    if text is None:text=bpy.data.texts.new(root.name+' / Working RaceTest');root['mr_studio_working_xml']=text.name
    text.clear();text.write(payload.decode('utf-8'))
    root['mr_studio_working_sha']=hashlib.sha256(payload).hexdigest()
    obj=next(o for o in root.all_objects if o.get('mr_studio_geometry'))
    bpy.ops.object.select_all(action='DESELECT');obj.select_set(True);context.view_layer.objects.active=obj
    before={o.as_pointer() for o in bpy.data.objects}
    result=bpy.ops.import_scene.master_rallye_course_xml_markers(filepath=str(session.project.resources.race_test_xml),studio_payload_text=text.name)
    if result!={'FINISHED'}:raise ValueError('Could not rebuild marker helpers from working XML')
    _organize(root)
    for obj in root.all_objects:
        if obj.as_pointer() not in before:obj['mr_studio_owner']=root.name


class MR_OT_studio_marker(bpy.types.Operator):
    bl_idname='mr.course_studio_marker'
    bl_label='Course Marker Builder'
    bl_options={'REGISTER','UNDO'}
    action:EnumProperty(items=[('START','Create Start Area','Four Marker Pos fields at cursor; existing direction fields preserved'),('FINISH','Create Finish Area','Four Marker Pos fields at cursor'),('SPLIT','Add SplitTime','Clone native trigger and visual companion template; preserve ExtraTime'),('CHECKPOINT','Create Checkpoint','Same native spherical SplitTime trigger and companions'),('DELETE','Delete Selected SplitTime','Remove only selected trigger Egg and its 0..3 companions'),('REORDER','Reorder Markers','Assign Split Time IDs in existing XML source order')])
    def execute(self,context):
        root=None;previous=None
        try:
            selected=context.object
            root,session,_=_sync(context);previous=session.editor.export()[0]
            center=blender_position_to_source(context.scene.cursor.location)
            if self.action in ('START','FINISH'):
                payload,audit=marker_builder.place_area(previous,'StartArea' if self.action=='START' else 'FinishArea',center,
                    half_width=context.scene.mr_studio_area_width/2,half_depth=context.scene.mr_studio_area_depth/2)
            elif self.action in ('SPLIT','CHECKPOINT'):
                payload,audit=marker_builder.add_split(previous,center,radius=context.scene.mr_studio_split_radius)
            elif self.action=='DELETE':
                if selected is None or 'mr_split_time_id' not in selected:raise ValueError('Select a native SplitTime center helper')
                payload,audit=marker_builder.remove_split(previous,int(selected['mr_split_time_id']))
            else:payload,audit=marker_builder.reorder_split_ids(previous)
            _reload_logic(context,root,session,payload)
            entries=json.loads(root.get('mr_studio_structural_audit','[]'));entries.append(audit)
            root['mr_studio_structural_audit']=json.dumps(entries)
            self.report({'INFO'},str(audit));return {'FINISHED'}
        except Exception as error:
            if root is not None and previous is not None:
                try:_reload_logic(context,root,session,previous)
                except Exception as recovery:print('COURSE_STUDIO_RECOVERY',str(recovery))
            self.report({'ERROR'},str(error));return {'CANCELLED'}


class MR_OT_studio_route_proposal(bpy.types.Operator):
    bl_idname='mr.course_studio_route_proposal'
    bl_label='Create Alternative Route Proposal'
    bl_options={'REGISTER','UNDO'}
    role:EnumProperty(items=[('AI_PROPOSAL','AI route proposal','Editor-only alternative; native route choice remains UNKNOWN'),('PLAYER_REGION','Player freedom region','Independent player movement/checkpoint planning; not a narrow AI corridor')])
    def execute(self,context):
        try:
            root,_,_=_sync(context)
            points=sorted((o for o in root.all_objects if o.get('mr_race_logic_object_type')=='route_marker'),key=lambda o:o.get('mr_marker_index_in_list',-1))
            if len(points)<2:raise ValueError('A source RaceLine with two points is required')
            curve=bpy.data.curves.new(self.role,'CURVE');curve.dimensions='3D';curve.bevel_depth=0.08
            spline=curve.splines.new('POLY');spline.points.add(len(points)-1)
            for point,obj in zip(spline.points,points):point.co=(*obj.matrix_world.translation,1)
            obj=bpy.data.objects.new('Editor / '+self.role,curve);_layer(root,'AI').objects.link(obj)
            obj['mr_studio_route_role']=self.role;obj['mr_editor_only']=True;obj['mr_support']='EDITOR_ONLY'
            obj['mr_studio_owner']=root.name
            bpy.ops.object.select_all(action='DESELECT');obj.select_set(True);context.view_layer.objects.active=obj
            self.report({'INFO'},'Edit curve points; saved to neutral editor-routes.json, no native AI route claim')
            return {'FINISHED'}
        except Exception as error:self.report({'ERROR'},str(error));return {'CANCELLED'}


class MR_OT_studio_texture(bpy.types.Operator,ImportHelper):
    bl_idname='mr.course_studio_texture'
    bl_label='Stage Course Texture from PNG'
    filter_glob:StringProperty(default='*.png',options={'HIDDEN'})
    def execute(self,context):
        try:
            root,session=_session(context);obj=context.object
            material=obj.active_material if obj and obj.type=='MESH' else None
            if material is None or not material.get('mr_dxt_source'):raise ValueError('Select a resolved native course texture material')
            if not context.scene.mr_studio_output:raise ValueError('Set the fresh export directory first')
            output=Path(bpy.path.abspath(context.scene.mr_studio_output)).resolve()
            source=Path(material['mr_dxt_source']).resolve()
            relative=source.relative_to(session.root)
            draft=output.parent/(output.name+'-texture-drafts')/relative
            report=replace_texture(source,Path(self.filepath),draft,expected_source_sha256=material['mr_dxt_sha256'])
            session.stage_texture(source,draft)
            drafts=json.loads(root.get('mr_studio_texture_drafts','{}'));drafts[str(source)]=str(draft)
            root['mr_studio_texture_drafts']=json.dumps(drafts)
            self.report({'INFO'},f'Staged {relative}; source header and bindings preserved');return {'FINISHED'}
        except Exception as error:self.report({'ERROR'},str(error));return {'CANCELLED'}


class MR_OT_studio_open(bpy.types.Operator, ImportHelper):
    bl_idname = 'mr.course_studio_open'
    bl_label = 'Open Course Project'
    bl_options = {'REGISTER', 'UNDO'}
    filter_glob: StringProperty(default='*.xml;*.dx;*.json', options={'HIDDEN'})
    resource_root: StringProperty(name='Resource root (DataGx/DataScene parent)', subtype='DIR_PATH')
    race_id: IntProperty(name='Registry Race ID (-1 requires unique entry)', default=-1, min=-1)
    load_textures: BoolProperty(name='Load textures', default=True)

    def execute(self, context):
        root = None
        before_materials=set(bpy.data.materials.keys());before_images=set(bpy.data.images.keys())
        try:
            source = Path(self.filepath)
            if source.name == '__folder__': source = source.parent
            session = CourseStudio(source, resource_root=self.resource_root or None, race_id=self.race_id if self.race_id >= 0 else None)
            if any(c.get('mr_studio_source') == str(session.source) for c in bpy.data.collections):
                raise ValueError('Project already open; close its owned collection before reimport')
            if session.project.render is None or session.editor is None:
                raise ValueError('Select a RaceTest XML or bound project with both render and race logic')
            root = create_collection('MR Course Studio - ' + session.project.identity)
            root['mr_resource_kind'] = 'course'; root['mr_course_identity'] = session.project.resources.race_test_xml.stem
            root['mr_studio_source'] = str(session.source); root['mr_studio_resource_root'] = str(session.root or '')
            root['mr_studio_race_id'] = self.race_id; root['mr_studio_hashes'] = json.dumps(session.hashes, sort_keys=True)
            for name in LAYERS:
                layer = create_collection('MR / ' + name, root); layer['mr_studio_layer'] = name
            result = import_dx_resource(session.project.resources.render_dx, _layer(root, 'Visual Terrain'),
                        parsed_model=session.project.render._parsed_model, resource_kind='course', show_collision=False, load_textures=self.load_textures)
            obj = result.object; obj['mr_studio_geometry'] = True
            obj['mr_studio_mesh_contract'] = _contract(obj)
            obj['mr_studio_writer'] = 'same-order position buffer; BSP/bounds preserved'
            bpy.ops.object.select_all(action='DESELECT'); obj.select_set(True); context.view_layer.objects.active = obj
            status = bpy.ops.import_scene.master_rallye_course_xml_markers(filepath=str(session.project.resources.race_test_xml))
            if status != {'FINISHED'}: raise ValueError('RaceTest helper import failed')
            for c in list(_walk(root)):
                kind = str(c.get('mr_xml_collection_kind', ''))
                if kind.startswith('marker_list:'):
                    names = {str(o.get('mr_source_list_name', o.get('mr_race_logic_area', ''))) for o in c.all_objects}
                    if names & {'StartArea', 'FinishArea'}: _rehome(c, _layer(root, 'Start & Finish'))
                    elif 'RaceLine' in names: _rehome(c, _layer(root, 'RaceLine'))
                    elif any('Limit' in name for name in names): _rehome(c, _layer(root, 'Limits'))
            # Race logic export follows all source helpers, even across semantic collections.
            logic = next(c for c in _walk(root) if c.get('mr_xml_collection_kind') == 'race_logic_root')
            root['mr_studio_logic'] = logic.name
            for name in LAYERS:
                _rehome(_layer(root, name), logic)
            _egg_inspector(root,session)
            _restore_neutral_routes(root,session)
            for owned_object in root.all_objects:owned_object['mr_studio_owner']=root.name
            for c in list(_walk(root)):
                if c.get('mr_xml_collection_kind')=='egg_list:SplitTimes':_rehome(c,_layer(root,'Checkpoints'))
            for material in bpy.data.materials:
                if not material.get('mr_studio_owner') and material.name not in before_materials:material['mr_studio_owner']=root.name
            for image in bpy.data.images:
                if not image.get('mr_studio_owner') and image.name not in before_images:image['mr_studio_owner']=root.name
            SESSIONS[root.name] = session; context.scene['mr_studio_root'] = root.name
            context.scene.mr_studio_name='';context.scene.mr_studio_registry='';context.scene.mr_studio_output=''
            _report(context, session.validate())
            self.report({'INFO'}, 'Course Studio opened; source resources preserved')
            return {'FINISHED'}
        except Exception as error:
            if root is not None: _dispose(root)
            self.report({'ERROR'}, str(error)); return {'CANCELLED'}


class MR_OT_studio_validate(bpy.types.Operator):
    bl_idname = 'mr.course_studio_validate'
    bl_label = 'Validate Course'
    def execute(self, context):
        try:
            _, session, warnings = _sync(context); findings = session.validate(); _report(context, findings)
            self.report({'WARNING'} if any(f.severity == 'ERROR' for f in findings) else {'INFO'}, context.scene['mr_studio_validation'] + ('; ' + '; '.join(warnings) if warnings else ''))
            return {'FINISHED'}
        except Exception as error:
            context.scene['mr_studio_validation'] = 'ERROR: ' + str(error)
            self.report({'ERROR'}, str(error)); return {'CANCELLED'}


class MR_OT_studio_close(bpy.types.Operator):
    bl_idname='mr.course_studio_close'
    bl_label='Close Course Project'
    bl_options={'REGISTER','UNDO'}
    def execute(self,context):
        try:
            root=_root(context);name=root.name;text_name=root.get('mr_studio_working_xml','')
            _release_foreign(root);_dispose(root);SESSIONS.pop(name,None)
            if 'mr_studio_root' in context.scene:del context.scene['mr_studio_root']
            text=bpy.data.texts.get(text_name)
            if text:bpy.data.texts.remove(text)
            for material in list(bpy.data.materials):
                if material.get('mr_studio_owner')==name and not material.users:bpy.data.materials.remove(material)
            for image in list(bpy.data.images):
                if image.get('mr_studio_owner')==name and not image.users:bpy.data.images.remove(image)
            self.report({'INFO'},'Course-owned scene data closed');return {'FINISHED'}
        except Exception as error:
            self.report({'ERROR'},str(error));return {'CANCELLED'}


class MR_OT_studio_select_issue(bpy.types.Operator):
    bl_idname='mr.course_studio_select_issue'
    bl_label='Select Validation Object'
    path:StringProperty()
    def execute(self,context):
        try:
            root=_root(context)
            matches=[o for o in root.all_objects if o.name==self.path or o.get('mr_source_xml_path')==self.path or o.get('mr_native_egg_path')==self.path
                     or (self.path=='Visual Terrain' and o.get('mr_studio_geometry'))]
            if not matches:raise ValueError('Resource-level finding; full path and explanation are in MR Course Validation')
            bpy.ops.object.select_all(action='DESELECT')
            for obj in matches:obj.hide_set(False);obj.select_set(True)
            context.view_layer.objects.active=matches[0];return {'FINISHED'}
        except Exception as error:self.report({'WARNING'},str(error));return {'CANCELLED'}


class MR_OT_studio_export(bpy.types.Operator):
    bl_idname = 'mr.course_studio_export'
    bl_label = 'Validate > Stage > Export'
    def execute(self, context):
        try:
            _, session, _ = _sync(context)
            registry = json.loads(Path(context.scene.mr_studio_registry).read_text()) if context.scene.mr_studio_registry else None
            report = session.export(bpy.path.abspath(context.scene.mr_studio_output), registry=registry,
                                    template_race_id=context.scene.mr_studio_template, name=context.scene.mr_studio_name or None)
            self.report({'INFO'}, f'Staged {len(report["files"])} resources; runtime acceptance pending')
            return {'FINISHED'}
        except Exception as error:
            self.report({'ERROR'}, str(error)); return {'CANCELLED'}


class MR_OT_studio_bsp(bpy.types.Operator):
    bl_idname = 'mr.course_studio_bsp'
    bl_label = 'Inspect BSP Region / Plane'
    def execute(self, context):
        try:
            root, session = _session(context); bsp = session.collision()
            index = context.scene.mr_studio_bsp_index
            if index >= len(bsp.nodes): raise ValueError(f'Node index must be below {len(bsp.nodes)}')
            node = bsp.nodes[index]
            info = dict(index=node.index, offset=node.offset, depth=node.depth, parent=node.parent_index,
                        child=node.first_child_index, sibling=node.next_sibling_index, field_0=node.field_0,
                        field_1=node.field_1, plane=node.optional_record.values if node.optional_record else None,
                        code=node.optional_record.code if node.optional_record else None, status='INSPECT_ONLY',
                        note='Plane patch is an inspection glyph, not a collision triangle or bounded solid face')
            doc = bpy.data.texts.get('MR BSP Inspector') or bpy.data.texts.new('MR BSP Inspector'); doc.clear(); doc.write(json.dumps(info, indent=2))
            context.scene['mr_studio_bsp_navigation']=json.dumps({k:info[k] for k in ('parent','child','sibling')})
            layer = _layer(root, 'Collision')
            old = next((o for o in layer.objects if o.get('mr_studio_plane')), None)
            if old:
                mesh = old.data; bpy.data.objects.remove(old, do_unlink=True)
                if mesh.users == 0: bpy.data.meshes.remove(mesh)
            if node.optional_record:
                a,b,c,d = node.optional_record.values; n = Vector((a,b,c)); length = n.length
                if length < 1e-9: raise ValueError('Degenerate BSP plane')
                center = Vector(blender_position_to_source(context.scene.cursor.location)); center -= n*((n.dot(center)+d)/(length*length))
                unit = n.normalized(); u = unit.cross(Vector((1,0,0)) if abs(unit.x)<0.9 else Vector((0,0,1))).normalized()*25; v=unit.cross(u)
                points = [position_to_blender(center + su*u + sv*v) for su,sv in ((-1,-1),(1,-1),(1,1),(-1,1))]
                mesh = bpy.data.meshes.new('BSP plane glyph'); mesh.from_pydata(points, [(0,1),(1,2),(2,3),(3,0)], [])
                obj = bpy.data.objects.new('BSP plane (unbounded) '+str(index), mesh); layer.objects.link(obj)
                obj['mr_studio_plane'] = True; obj['mr_editor_only'] = True; obj['mr_bsp_node'] = index
                obj['mr_studio_owner']=root.name
                obj['mr_bsp_metadata'] = json.dumps(info); obj.show_in_front = True
            self.report({'INFO'}, f'Node {index}/{len(bsp.nodes)}; details in MR BSP Inspector')
            return {'FINISHED'}
        except Exception as error:
            self.report({'ERROR'}, str(error)); return {'CANCELLED'}


class MR_OT_studio_bsp_nav(bpy.types.Operator):
    bl_idname='mr.course_studio_bsp_nav'
    bl_label='Navigate BSP Node'
    target:IntProperty(default=0,min=0)
    def execute(self,context):
        context.scene.mr_studio_bsp_index=self.target
        return bpy.ops.mr.course_studio_bsp()


class MR_OT_studio_probe(bpy.types.Operator):
    bl_idname = 'mr.course_studio_probe'
    bl_label = 'Probe Actual BSP at 3D Cursor'
    def execute(self, context):
        try:
            root, session = _session(context); bsp = session.collision()
            x,y,z = blender_position_to_source(context.scene.cursor.location)
            spans = bsp_ray_intervals(bsp, (x,y,z), (0,1,0), -500, 500)
            points=[]; edges=[]
            for lo,hi,solid,index in spans:
                if solid:
                    offset=len(points); points.extend([position_to_blender((x,y+lo,z)),position_to_blender((x,y+hi,z))]); edges.append((offset,offset+1))
            layer=_layer(root,'Collision')
            old=next((o for o in layer.objects if o.get('mr_studio_probe')),None)
            if old:
                mesh=old.data; bpy.data.objects.remove(old,do_unlink=True)
                if not mesh.users: bpy.data.meshes.remove(mesh)
            mesh=bpy.data.meshes.new('BSP solid ray intervals'); mesh.from_pydata(points,edges,[])
            obj=bpy.data.objects.new('BSP solid intervals at cursor',mesh);layer.objects.link(obj);obj.show_in_front=True
            obj['mr_studio_probe']=True;obj['mr_editor_only']=True;obj['mr_bsp_ray_intervals']=json.dumps(spans)
            obj['mr_studio_owner']=root.name
            self.report({'INFO'},f'{len(spans)} exact BSP ray intervals; solid intervals shown as lines')
            return {'FINISHED'}
        except Exception as error:
            self.report({'ERROR'},str(error));return {'CANCELLED'}


class MR_OT_studio_rigid(bpy.types.Operator, ImportHelper):
    bl_idname='mr.course_studio_rigid'
    bl_label='Show PS2 Physical Objects'
    filter_glob:StringProperty(default='*.ps2rgd',options={'HIDDEN'})
    def execute(self,context):
        created=None
        try:
            root,session=_session(context);asset=read_rigid_asset(self.filepath)
            relative=session.project.resources.render_dx.relative_to(session.root).as_posix().casefold()
            courses=[c for c in asset['courses'] if rigid_text(c[1]).replace('\\','/').casefold()==relative]
            if len(courses)!=1:raise ValueError('Asset has no unique exact course DX binding')
            if any(c.get('mr_rigid_source') for c in _walk(root)):raise ValueError('Physical object asset already loaded')
            course=courses[0];created=create_collection('PS2 Physical Objects',_layer(root,'Static Objects'))
            created['mr_rigid_source']=asset['source'];created['mr_support']='INSPECT_ONLY'
            materials=[]
            for texture_index,(width,height,bgra) in enumerate(asset['textures']):
                image=bpy.data.images.new(f'PS2 Rigid {texture_index}',width=width,height=height,alpha=True)
                rgba=[]
                for i in range(0,len(bgra),4):rgba.extend((bgra[i+2]/255,bgra[i+1]/255,bgra[i]/255,bgra[i+3]/255))
                image.pixels.foreach_set(rgba);image.pack();image['mr_studio_owner']=root.name
                material=bpy.data.materials.new(f'PS2 Rigid {texture_index}');material.use_nodes=True;material['mr_studio_owner']=root.name
                shader=material.node_tree.nodes.get('Principled BSDF');node=material.node_tree.nodes.new('ShaderNodeTexImage');node.image=image
                material.node_tree.links.new(node.outputs['Color'],shader.inputs['Base Color'])
                material.node_tree.links.new(node.outputs['Alpha'],shader.inputs['Alpha'])
                materials.append(material)
            conversion=Matrix(((1,0,0,0),(0,0,-1,0),(0,1,0,0),(0,0,0,1)))
            for prop_index in range(course[3],course[3]+course[4]):
                prop=asset['props'][prop_index];model=asset['models'][prop[1]];vertices=[];faces=[]
                uv_values=[];face_materials=[]
                for draw in range(model[2]):
                    texture,first,count=model[3+3*draw:6+3*draw]
                    for vertex in asset['vertices'][first:first+count]:vertices.append(vertex[:3])
                    uv_values.extend(v[4:6] for v in asset['vertices'][first:first+count]);face_materials.extend([texture]*(count//3))
                faces=[(i,i+1,i+2) for i in range(0,len(vertices),3)]
                mesh=bpy.data.meshes.new(rigid_text(model[0]));mesh.from_pydata(vertices,[],faces)
                uv=mesh.uv_layers.new(name='MR UV 0')
                for polygon in mesh.polygons:
                    for loop in polygon.loop_indices:uv.data[loop].uv=uv_values[mesh.loops[loop].vertex_index]
                for material in materials:mesh.materials.append(material)
                for polygon,texture in zip(mesh.polygons,face_materials):polygon.material_index=texture
                obj=bpy.data.objects.new(rigid_text(prop[0]),mesh);created.objects.link(obj)
                obj['mr_studio_owner']=root.name
                m=prop[8:20];native=Matrix(((m[0],m[3],m[6],m[9]),(m[1],m[4],m[7],m[10]),(m[2],m[5],m[8],m[11]),(0,0,0,1)))
                obj.matrix_world=conversion@native
                context.view_layer.update()
                obj['mr_studio_inspect_matrix']=json.dumps([list(row) for row in obj.matrix_world])
                obj['mr_studio_inspect_contract']=_inspect_contract(obj)
                obj['mr_rigid_prop_index']=prop_index;obj['mr_rigid_mass']=prop[3];obj['mr_rigid_moi']=prop[4:7]
                obj['mr_rigid_trigger_distance']=prop[7];obj['mr_support']='INSPECT_ONLY'
                first,count,fp,np=model[10:14]
                obj['mr_rigid_hull_points']=json.dumps(asset['points'][first:first+count]);obj['mr_rigid_hull_planes']=json.dumps(asset['planes'][fp:fp+np])
                hull_points=asset['points'][first:first+count];hull_faces=[]
                for plane in asset['planes'][fp:fp+np]:
                    ids=[i for i,p in enumerate(hull_points) if abs(sum(plane[k]*p[k] for k in range(3))+plane[3])<1e-3]
                    if len(ids)<3:continue
                    center=sum((Vector(hull_points[i]) for i in ids),Vector())/len(ids)
                    n=Vector(plane[:3]);u=(Vector(hull_points[ids[0]])-center).normalized();v=n.cross(u)
                    ids.sort(key=lambda i:math.atan2((Vector(hull_points[i])-center).dot(v),(Vector(hull_points[i])-center).dot(u)))
                    hull_faces.append(ids)
                hull_mesh=bpy.data.meshes.new('Native PS2 convex hull');hull_mesh.from_pydata(hull_points,[],hull_faces)
                hull=bpy.data.objects.new(obj.name+' / Native hull',hull_mesh);created.objects.link(hull)
                hull['mr_studio_owner']=root.name
                hull.matrix_world=obj.matrix_world;hull.display_type='WIRE';hull.show_in_front=True
                context.view_layer.update();hull['mr_studio_inspect_matrix']=json.dumps([list(row) for row in hull.matrix_world])
                hull['mr_studio_inspect_contract']=_inspect_contract(hull);hull['mr_support']='INSPECT_ONLY';hull['mr_rigid_prop_index']=prop_index
            self.report({'INFO'},f'{course[4]} PS2 physical objects with native hull metadata; inspect only')
            return {'FINISHED'}
        except Exception as error:
            if created:_dispose(created)
            self.report({'ERROR'},str(error));return {'CANCELLED'}


class MR_OT_studio_feature(bpy.types.Operator, ImportHelper):
    bl_idname='mr.course_studio_feature'
    bl_label='Load PS2 Spline / Birds / Grass / Shrubs'
    filter_glob:StringProperty(default='*.ps2spl;*.ps2bird;*.ps2grass',options={'HIDDEN'})
    def execute(self,context):
        created=None
        try:
            root,session=_session(context)
            relative=session.project.resources.render_dx.relative_to(session.root).as_posix()
            features=read_proxy_features(self.filepath,relative)
            source=str(Path(self.filepath).resolve())
            if any(c.get('mr_feature_source')==source for c in _walk(root)):raise ValueError('This feature asset is already loaded')
            created=create_collection('PS2 / '+Path(self.filepath).stem,_layer(root,'Static Objects'));created['mr_feature_source']=source
            summaries=json.loads(root.get('mr_studio_features','[]'))
            for feature in features:
                mesh=bpy.data.meshes.new(feature['name']);points=feature['points']
                edges=[(i,i+1) for i in range(len(points)-1)] if feature['kind']=='spline_object' else []
                if feature.get('config',{}).get('loop') and len(points)>1:edges.append((len(points)-1,0))
                display_points=[position_to_blender(p) for p in points]
                if feature['kind']!='spline_object':
                    count=len(display_points);display_points.extend((p[0],p[1],p[2]+0.25) for p in list(display_points))
                    edges=[(i,i+count) for i in range(count)]
                mesh.from_pydata(display_points,edges,[])
                obj=bpy.data.objects.new(feature['kind']+' / '+feature['name'],mesh);created.objects.link(obj)
                obj['mr_studio_owner']=root.name
                obj.show_in_front=True;obj.display_type='WIRE';context.view_layer.update()
                summary={k:v for k,v in feature.items() if k!='points'};summary['point_count']=len(points)
                summary['source_sha256']=hashlib.sha256(Path(source).read_bytes()).hexdigest()
                expected=feature.get('source_pc_sha256');actual=session.hashes.get(relative)
                summary['course_source_match']=expected==actual
                obj['mr_feature_metadata']=json.dumps(summary);obj['mr_support']='INSPECT_ONLY'
                obj['mr_studio_inspect_matrix']=json.dumps([list(row) for row in obj.matrix_world]);obj['mr_studio_inspect_contract']=_inspect_contract(obj)
                summaries.append(summary)
            root['mr_studio_features']=json.dumps(summaries)
            self.report({'INFO'},f'{len(features)} feature groups loaded; native source placements/controls, inspect only')
            return {'FINISHED'}
        except Exception as error:
            if created:_dispose(created)
            self.report({'ERROR'},str(error));return {'CANCELLED'}


class MR_OT_studio_collision_check(bpy.types.Operator):
    bl_idname='mr.course_studio_collision_check'
    bl_label='Check Marker / BSP Clearance'
    def execute(self,context):
        try:
            root,session,_=_sync(context);bsp=session.collision()
            anchors=[o for o in root.all_objects if o.get('mr_race_logic_object_type') in ('area_marker','split_center')]
            findings=[]
            for obj in anchors:
                point=blender_position_to_source(obj.matrix_world.translation)
                spans=bsp_ray_intervals(bsp,point,(0,1,0),-50,50)
                crossings=[left[1] for left,right in zip(spans,spans[1:]) if left[2] and not right[2] and abs(left[1]-right[0])<1e-5]
                nearest=min(crossings,key=abs) if crossings else None
                if nearest is None or abs(nearest)>10:
                    findings.append(dict(severity='WARNING',object=obj.name,source_position=point,nearest_ground_delta=nearest,
                        message='No nearby upward solid/empty BSP boundary; inspect missing ground or marker elevation; not a physics verdict'))
            doc=bpy.data.texts.get('MR Collision Diagnostics') or bpy.data.texts.new('MR Collision Diagnostics');doc.clear();doc.write(json.dumps(findings,indent=2))
            self.report({'INFO'},f'{len(anchors)} native marker rays; {len(findings)} clearance warnings in MR Collision Diagnostics')
            return {'FINISHED'}
        except Exception as error:
            self.report({'ERROR'},str(error));return {'CANCELLED'}


class MR_PT_course_studio(bpy.types.Panel):
    bl_label='Course Studio'
    bl_idname='MR_PT_course_studio'
    bl_space_type='VIEW_3D';bl_region_type='UI';bl_category='Master Rallye'
    def draw(self,context):
        layout=self.layout;scene=context.scene
        box=layout.box();box.label(text='Project');box.operator('mr.course_studio_open')
        try:root=_root(context)
        except ValueError:return
        box.label(text=root.name);box.label(text='Source: '+Path(root['mr_studio_source']).name)
        box.operator('mr.course_studio_close')
        box=layout.box();box.label(text='Terrain & Objects / Layers')
        for child in _walk(root):
            if child.get('mr_studio_layer'):box.prop(child,'hide_viewport',text=child['mr_studio_layer'],toggle=True)
        box.operator('mr.course_studio_rigid');box.label(text='Geometry: same-order positions only')
        box.operator('mr.course_studio_feature')
        box=layout.box();box.label(text='Materials');box.operator('object.master_rallye_reload_textures');box.operator('object.master_rallye_texture_users')
        box.operator('object.master_rallye_export_texture');box.operator('mr.course_studio_texture')
        if context.object and context.object.type=='MESH' and context.object.active_material:
            for item in json.loads(context.object.active_material.get('mr_surface_source_inventory','[]'))[:5]:
                box.label(text='Surface: '+', '.join(item['surface'])+' / '+', '.join(item['ground']))
            box.label(text='Surface behavior: INSPECT_ONLY')
        box=layout.box();box.label(text='Collision - INSPECT_ONLY');box.prop(scene,'mr_studio_bsp_index');box.operator('mr.course_studio_bsp');box.operator('mr.course_studio_probe')
        row=box.row()
        for key,value in json.loads(scene.get('mr_studio_bsp_navigation','{}')).items():
            if value is not None:row.operator('mr.course_studio_bsp_nav',text=key.title()).target=value
        box.operator('mr.course_studio_collision_check')
        box=layout.box();box.label(text='Markers');box.prop(scene,'mr_studio_area_width');box.prop(scene,'mr_studio_area_depth')
        for action,label in (('START','Create Start Area'),('FINISH','Create Finish Area')):
            op=box.operator('mr.course_studio_marker',text=label);op.action=action
        box.prop(scene,'mr_studio_split_radius')
        for action,label in (('SPLIT','Add SplitTime'),('CHECKPOINT','Create Checkpoint'),('DELETE','Delete Selected SplitTime'),('REORDER','Reorder Markers')):
            op=box.operator('mr.course_studio_marker',text=label);op.action=action
        selected=context.object
        if selected and 'mr_split_radius' in selected:
            box.prop(selected,'["mr_split_radius"]',text='Native Radius');box.prop(selected,'["mr_split_time_id"]',text='Native Split ID')
        box.label(text='ExtraTime: preserved; semantics UNKNOWN')
        box=layout.box();box.label(text='Routes & AI');box.label(text='RaceLine / Limits: move existing points');box.label(text='AI line does not restrict player freedom');box.operator('mr.course_studio_validate',text='Validate Route')
        box.operator('mr.course_studio_route_proposal')
        box=layout.box();box.label(text='Validation & Export');box.operator('mr.course_studio_validate');box.label(text=scene.get('mr_studio_validation','Not validated'))
        for finding in json.loads(scene.get('mr_studio_findings','[]'))[:12]:
            row=box.row();row.label(text=finding['severity']+' / '+Path(finding['path']).name)
            row.operator('mr.course_studio_select_issue',text='',icon='RESTRICT_SELECT_OFF').path=finding['path']
            box.label(text=finding['message'][:70])
        box.prop(scene,'mr_studio_output');box.prop(scene,'mr_studio_registry');box.prop(scene,'mr_studio_template');box.prop(scene,'mr_studio_name');box.operator('mr.course_studio_export')


CLASSES=(MR_OT_studio_open,MR_OT_studio_marker,MR_OT_studio_route_proposal,MR_OT_studio_texture,MR_OT_studio_validate,MR_OT_studio_close,MR_OT_studio_select_issue,MR_OT_studio_export,MR_OT_studio_bsp,MR_OT_studio_bsp_nav,MR_OT_studio_probe,MR_OT_studio_rigid,MR_OT_studio_feature,MR_OT_studio_collision_check,MR_PT_course_studio)


def register():
    for cls in CLASSES:bpy.utils.register_class(cls)
    bpy.types.Scene.mr_studio_output=StringProperty(name='Fresh staging directory',subtype='DIR_PATH')
    bpy.types.Scene.mr_studio_registry=StringProperty(name='COURSE-CAP2 catalog (optional)',subtype='FILE_PATH')
    bpy.types.Scene.mr_studio_template=IntProperty(name='Template Race ID',default=0,min=0)
    bpy.types.Scene.mr_studio_name=StringProperty(name='New race name')
    bpy.types.Scene.mr_studio_bsp_index=IntProperty(name='BSP node index',default=0,min=0)
    bpy.types.Scene.mr_studio_area_width=FloatProperty(name='Area width',default=30,min=0.01)
    bpy.types.Scene.mr_studio_area_depth=FloatProperty(name='Area depth',default=10,min=0.01)
    bpy.types.Scene.mr_studio_split_radius=FloatProperty(name='New checkpoint radius',default=30,min=0.01)


def unregister():
    SESSIONS.clear()
    for name in ('mr_studio_output','mr_studio_registry','mr_studio_template','mr_studio_name','mr_studio_bsp_index','mr_studio_area_width','mr_studio_area_depth','mr_studio_split_radius'):
        if hasattr(bpy.types.Scene,name):delattr(bpy.types.Scene,name)
    for cls in reversed(CLASSES):bpy.utils.unregister_class(cls)
