"""Versioned authored layer above immutable UVS, with explicit edit transactions.

Source Fidelity keeps the old bridge unchanged. Classic/Customized deliberately
replace source rendering only on explicitly assigned faces. A derived material
is never reported as recovered source shader equivalence. Native safety uses
the same UVS/ScenePart/DX validators as before.
"""
from __future__ import annotations
import copy
import os
from pathlib import Path
from . import universal_vehicle_scene as u

SCHEMA='editable-vehicle-project/1'
MODES=('Source Fidelity','MR Classic','User Customized')
ROLES=('opaque_body','glass','frame','tyre','rim','wheel_interior','equipment','cabin_crew','reflective_paint')
MAX_OPS=512


def _index(value,count):
    if type(value)is not int or not 0<=value<count:raise ValueError('Edit index outside current geometry')
    return value


def _initial(source):
    scene=copy.deepcopy(source)
    scene['source']={'root':source['source']['root'],'protected_roots':source['source'].get('protected_roots',[])}
    for mesh in scene['meshes']:
        original=mesh['source'];mesh['source']={'derived_from_mesh':mesh['id'],'original_geometry':original}
        # Original typed/raw streams remain in the immutable parent. Derived
        # topology cannot claim correspondence to unchanged binary streams.
        mesh.pop('uv_channels',None);mesh.pop('animation_frames',None)
        mesh['face_ids']=[mesh['id']+':face:'+str(i)for i in range(len(mesh['triangles']))]
    for texture in scene['textures']:texture.pop('source',None)
    scene['metadata']['authoring_boundary']='Derived editable state; original shader claims remain in the immutable parent'
    return scene


def _apply(scene,op,ordinal):
    name=op.get('op');meshes={m['id']:m for m in scene['meshes']};nodes={n['id']:n for n in scene['nodes']}
    mid=op.get('mesh');mesh=meshes.get(mid);prefix='authored-'+str(ordinal)
    nv=sum(len(m['positions'])for m in scene['meshes']);nt=sum(len(m['triangles'])for m in scene['meshes'])
    if name in('vertex','uv','normal','add_vertex','delete_vertex','add_face','delete_faces','duplicate','split','material','reset_material','glow','orient_winding','flip_faces')and mesh is None:
        raise ValueError('Edit references missing mesh')
    if name in('vertex','normal','uv'):
        key={'vertex':'positions','normal':'normals','uv':'uvs'}[name];index=_index(op['index'],len(mesh[key]));u.vector(op['value'],2 if name=='uv'else 3)
        if name=='normal'and sum(x*x for x in op['value'])<1e-12:raise ValueError('Zero authored normal')
        mesh[key][index]=list(op['value'])
    elif name=='add_vertex':
        for key,length in(('positions',3),('normals',3),('uvs',2)):
            u.vector(op[key],length);mesh[key].append(list(op[key]))
        if 'preview_colors_bgra'in mesh:mesh['preview_colors_bgra'].append([255]*4)
    elif name=='delete_vertex':
        index=_index(op['index'],len(mesh['positions']))
        if any(index in face for face in mesh['triangles']):raise ValueError('Delete receiving faces before deleting their vertex')
        for key in('positions','normals','uvs','preview_colors_bgra'):
            if key in mesh:mesh[key].pop(index)
        mesh['triangles']=[[i-(i>index)for i in face]for face in mesh['triangles']]
    elif name=='add_face':
        ids=op['vertices']
        if not isinstance(ids,list)or len(ids)!=3 or len(set(ids))!=3:raise ValueError('Three distinct face vertices required')
        for i in ids:_index(i,len(mesh['positions']))
        mesh['triangles'].append(ids[:]);mesh['face_ids'].append(prefix+':face')
    elif name in('delete_faces','split','material','reset_material'):
        selected=op.get('faces',mesh['face_ids'])
        if not isinstance(selected,list)or not selected or len(set(selected))!=len(selected)or set(selected)-set(mesh['face_ids']):
            raise ValueError('Stale or invalid face selection; select current stable face IDs')
        chosen=[i for i,f in enumerate(mesh['face_ids'])if f in selected]
        if name=='delete_faces':
            mesh['triangles']=[t for i,t in enumerate(mesh['triangles'])if i not in chosen];mesh['face_ids']=[f for i,f in enumerate(mesh['face_ids'])if i not in chosen]
        else:
            if len(chosen)!=len(mesh['face_ids']):
                part=copy.deepcopy(mesh);part['id']=prefix+'-section';part['face_ids']=[mesh['face_ids'][i]for i in chosen];part['triangles']=[mesh['triangles'][i]for i in chosen]
                mesh['triangles']=[t for i,t in enumerate(mesh['triangles'])if i not in chosen];mesh['face_ids']=[f for i,f in enumerate(mesh['face_ids'])if i not in chosen]
                scene['meshes'].append(part)
                for node in scene['nodes']:
                    if mid in node['mesh_ids']:node['mesh_ids'].append(part['id'])
                mesh=part
            if name=='material':
                rule=copy.deepcopy(op['rule']);role=rule.get('role');mode=rule.get('mode')
                if role not in ROLES or mode not in('opaque','alpha_test','alpha_blend'):raise ValueError('Supported authored material role/mode required')
                if mode=='alpha_blend'and role not in('glass',):raise ValueError('Transparent assignment requires explicit isolated glass role')
                if role=='reflective_paint'and mode!='opaque':raise ValueError('Reflection requires opaque base')
                if not isinstance(rule.get('evidence'),str)or not rule['evidence'].strip():raise ValueError('Authoring intent required')
                old=next(m for m in scene['materials']if m['id']==mesh['material_id']);material={'id':prefix+'-material','diffuse_texture_id':old['diffuse_texture_id'],
                    'raw_fields':[],'flags':{'transparent_raw':'0'if mode=='opaque'else'1','reflective_raw':'1'if role=='reflective_paint'else'0'},
                    'unsupported':['Intentional native adaptation; original shader preserved in parent'],'authored_rule':rule}
                if op.get('texture')is not None:
                    if op['texture']not in {t['id']for t in scene['textures']}:raise ValueError('Missing authored texture')
                    material['diffuse_texture_id']=op['texture']
                material['preview']={'opacity':rule.get('opacity',1)};scene['materials'].append(material);mesh['material_id']=material['id']
            elif name=='reset_material':mesh['material_id']=op['original_material']
    elif name=='flip_faces':
        faces=op.get('faces')
        if not isinstance(faces,list)or not faces or len(set(faces))!=len(faces)or set(faces)-set(mesh['face_ids']):raise ValueError('Select current stable faces to flip')
        for face_id,face in zip(mesh['face_ids'],mesh['triangles']):
            if face_id in faces:face[1],face[2]=face[2],face[1]
    elif name=='orient_winding':
        # Explicit user operation, never an automatic donor decoder correction.
        # Stable face IDs survive a corner permutation; material/controller
        # ownership remains the same face. Ambiguous faces stay unchanged.
        for face in mesh['triangles']:
            a,b,c=[mesh['positions'][i]for i in face];ab=[b[i]-a[i]for i in range(3)];ac=[c[i]-a[i]for i in range(3)]
            cross=[ab[1]*ac[2]-ab[2]*ac[1],ab[2]*ac[0]-ab[0]*ac[2],ab[0]*ac[1]-ab[1]*ac[0]]
            normal=[sum(mesh['normals'][v][i]for v in face)for i in range(3)]
            if sum(x*y for x,y in zip(cross,normal))< -1e-10:face[1],face[2]=face[2],face[1]
    elif name=='glow':
        faces=op.get('faces');trigger=op.get('trigger')
        if not isinstance(faces,list)or not faces or len(set(faces))!=len(faces)or set(faces)-set(mesh['face_ids']):raise ValueError('Glow requires exact current faces')
        if trigger not in('always','brake'):raise ValueError('Glow trigger must be always or brake')
        rgba=op.get('rgba')
        if not isinstance(rgba,list)or len(rgba)!=4 or any(type(x)is not int or not 0<=x<=255 for x in rgba):raise ValueError('Glow RGBA byte color required')
        effects=scene.setdefault('authored_effects',{})
        for face in faces:effects[face]={'trigger':trigger,'rgba':rgba[:],'origin':'User-authored native effect, not original donor behavior'}
    elif name=='remove_glow':
        effects=scene.setdefault('authored_effects',{})
        for face in op['faces']:effects.pop(face,None)
    elif name=='duplicate':
        if nv+len(mesh['positions'])>u.MAX_VERTICES or nt+len(mesh['triangles'])>u.MAX_TRIANGLES:raise ValueError('Derived geometry allocation budget')
        part=copy.deepcopy(mesh);part['id']=prefix+'-mesh';part['name']=op.get('name',part['id']);part['face_ids']=[prefix+':face:'+str(i)for i in range(len(part['triangles']))]
        part['source']={'user_created':True,'duplicated_from':mid};scene['meshes'].append(part)
        owners=[n for n in scene['nodes']if mid in n['mesh_ids']]
        if op.get('source_node')is not None:owners=[n for n in owners if n['id']==op['source_node']]
        if len(owners)!=1:raise ValueError('Duplicate requires one explicit source instance')
        node=copy.deepcopy(owners[0]);node.update(id=prefix+'-node',name=part['name'],mesh_ids=[part['id']],role='equipment')
        scene['nodes'].append(node)
    elif name=='add_mesh':
        geometry=op['geometry']
        if nv+len(geometry['positions'])>u.MAX_VERTICES or nt+len(geometry['triangles'])>u.MAX_TRIANGLES:raise ValueError('Derived geometry allocation budget')
        part=copy.deepcopy(op['geometry']);part['id']=prefix+'-mesh';part['source']={'user_created':True};part['face_ids']=[prefix+':face:'+str(i)for i in range(len(part['triangles']))]
        if part['material_id']not in {m['id']for m in scene['materials']}:raise ValueError('New component needs an existing material assignment')
        matrix=op.get('matrix',u.IDENTITY[:]);u.matrix(matrix)
        scene['meshes'].append(part);scene['nodes'].append({'id':prefix+'-node','name':op.get('name',prefix),'mesh_ids':[part['id']],
            'parent_id':op.get('parent_id'),'local_transform':matrix[:],'source_local_transform':None,'visible':True,'source_visible':True,
            'role':'equipment','transform_evidence':'User-created independent component'})
    elif name=='transform':
        if op['node']not in nodes:raise ValueError('Missing transform node')
        u.matrix(op['matrix']);nodes[op['node']]['local_transform']=list(op['matrix'])
    elif name=='visibility':
        if op['node']not in nodes or type(op['visible'])is not bool:raise ValueError('Explicit node visibility required')
        nodes[op['node']]['visible']=op['visible']
    elif name=='merge':
        other=meshes.get(op['other'])
        if mesh is None or other is None or other is mesh or mesh['material_id']!=other['material_id']:raise ValueError('Merge requires different meshes with the same material')
        owners=lambda key:[n['id']for n in scene['nodes']if key in n['mesh_ids']]
        if owners(mid)!=owners(other['id']):raise ValueError('Merge requires identical owning instances; transform components first')
        count=len(mesh['positions'])
        for key in('positions','normals','uvs'):mesh[key]+=copy.deepcopy(other[key])
        if ('preview_colors_bgra'in mesh)!=('preview_colors_bgra'in other):raise ValueError('Merge color layouts differ')
        if 'preview_colors_bgra'in mesh:mesh['preview_colors_bgra']+=copy.deepcopy(other['preview_colors_bgra'])
        mesh['triangles'] += [[v+count for v in face]for face in other['triangles']];mesh['face_ids']+=other['face_ids']
        scene['meshes'].remove(other)
        for node in scene['nodes']:node['mesh_ids']=[m for m in node['mesh_ids']if m!=other['id']]
    else:raise ValueError('Unsupported authored operation '+str(name))
    # Empty authored sections are normal after deletion; remove dangling owner
    # references rather than retaining stale face ordinals or emitting draws.
    empty={m['id']for m in scene['meshes']if not m['triangles']}
    scene['meshes']=[m for m in scene['meshes']if m['id']not in empty]
    for node in scene['nodes']:node['mesh_ids']=[m for m in node['mesh_ids']if m not in empty]
    valid_faces={face for m in scene['meshes']for face in m['face_ids']}
    scene['authored_effects']={f:e for f,e in scene.get('authored_effects',{}).items()if f in valid_faces}
    if (sum(len(m['positions'])for m in scene['meshes'])>u.MAX_VERTICES or
            sum(len(m['triangles'])for m in scene['meshes'])>u.MAX_TRIANGLES or
            len(scene['meshes'])>4096 or len(scene['nodes'])>4096 or len(scene['materials'])>4096):
        raise ValueError('Derived scene allocation budget')


class EditableVehicle:
    def __init__(self,document,source):
        self.document=copy.deepcopy(document);self.document.setdefault('transactions',list(range(1,len(document.get('operations',[]))+1)))
        self.source=copy.deepcopy(source);self._evaluated=None;self._evaluation_key=None;self.evaluate()

    @classmethod
    def create(cls,path,mode='User Customized',*,preview_cache=False):
        path=Path(path).absolute()
        if preview_cache:
            from .workshop.preview_cache import SCENES
            source,_=SCENES.load(path)
        else:source=u.load_scene(path)
        if mode not in MODES:raise ValueError('Explicit workflow required')
        return cls({'schema':SCHEMA,'source_path':str(path),'source_sha256':u.sha(path.read_bytes()),
                    'manifest_sha256':u.sha((path.parent/'manifest.json').read_bytes()),'mode':mode,'operations':[],'cursor':0},source)

    @classmethod
    def open(cls,path):
        doc=u.load_json(u.read_bounded(Path(path),u.MAX_JSON_BYTES))
        if not isinstance(doc,dict)or doc.get('schema')!=SCHEMA:raise ValueError('Unsupported editable project version; immutable UVS opens via Create derived')
        source=Path(doc['source_path']);u._hash(doc['source_sha256']);u._hash(doc['manifest_sha256'])
        if u.sha(u.read_bounded(source,u.MAX_JSON_BYTES))!=doc['source_sha256']or u.sha(u.read_bounded(source.parent/'manifest.json',2*1024*1024))!=doc['manifest_sha256']:
            raise ValueError('Immutable original project identity changed')
        return cls(doc,u.load_scene(source))

    def evaluate(self):
        doc=self.document;ops=doc.get('operations');cursor=doc.get('cursor')
        if doc.get('schema')!=SCHEMA or doc.get('mode')not in MODES or not isinstance(ops,list)or len(ops)>MAX_OPS or type(cursor)is not int or not 0<=cursor<=len(ops):raise ValueError('Invalid bounded editable journal')
        ends=doc['transactions']
        if not isinstance(ends,list)or any(type(x)is not int or not 1<=x<=len(ops)for x in ends)or ends!=sorted(set(ends))or (ops and(not ends or ends[-1]!=len(ops)))or cursor not in(0,*ends):raise ValueError('Invalid transaction boundaries')
        if doc['mode']=='Source Fidelity'and cursor:raise ValueError('Source Fidelity cannot apply authored edits; select a derived workflow')
        key=u.sha(u.canonical(doc))
        if key==self._evaluation_key:return copy.deepcopy(self._evaluated)
        if doc['mode']=='Source Fidelity':return copy.deepcopy(self.source)
        scene=_initial(self.source)
        for i,op in enumerate(ops[:cursor]):
            if not isinstance(op,dict):raise ValueError('Typed edit operation required')
            _apply(scene,op,i)
        u.validate_scene(scene);self._evaluated=copy.deepcopy(scene);self._evaluation_key=key;return scene

    def edit(self,op):
        self.edit_many([op])

    def edit_many(self,operations):
        if not isinstance(operations,list)or not operations:raise ValueError('Nonempty edit transaction required')
        previous=copy.deepcopy(self.document);cursor=previous['cursor']
        self.document['operations']=previous['operations'][:cursor]+copy.deepcopy(operations);self.document['cursor']=cursor+len(operations)
        self.document['transactions']=[x for x in previous['transactions']if x<=cursor]+[cursor+len(operations)]
        try:self.evaluate()
        except Exception:self.document=previous;raise

    def undo(self):self.document['cursor']=max([0,*[x for x in self.document['transactions']if x<self.document['cursor']]])
    def redo(self):
        target=min([len(self.document['operations']),*[x for x in self.document['transactions']if x>self.document['cursor']]])
        if self.document['mode']=='Source Fidelity'and target:raise ValueError('Choose a derived workflow before redoing edits')
        previous=self.document['cursor'];self.document['cursor']=target
        try:self.evaluate()
        except Exception:self.document['cursor']=previous;raise
    def restore(self):self.document['cursor']=0

    def save(self,path):
        self.evaluate();path=Path(path).absolute();u.unlinked(path)
        for root in(Path(self.document['source_path']).parent,Path(self.source['source']['root']),*map(Path,self.source['source'].get('protected_roots',[]))):
            if path.resolve().is_relative_to(root.resolve()):raise ValueError('Derived project cannot overwrite protected source')
        if path.exists():
            existing=u.load_json(u.read_bounded(path,u.MAX_JSON_BYTES))
            if existing.get('schema')!=SCHEMA or existing.get('source_sha256')!=self.document['source_sha256']:raise ValueError('Refusing to replace unrelated project')
        raw=u.canonical(self.document)
        if len(raw)>u.MAX_JSON_BYTES:raise ValueError('Editable journal byte budget')
        path.parent.mkdir(parents=True,exist_ok=True);temporary=path.with_name('.'+path.name+'.pending')
        with temporary.open('xb')as stream:stream.write(raw);stream.flush();os.fsync(stream.fileno())
        try:os.replace(temporary,path)
        finally:
            if temporary.exists():temporary.unlink()

    def diagnostics(self):
        from .scene_semantics import features
        scene=self.evaluate();materials={m['id']:m for m in scene['materials']};unassigned=[]
        for mesh in scene['meshes']:
            if 'authored_rule'not in materials[mesh['material_id']]:unassigned.append(mesh['id'])
        return {'source_fidelity':'PASS'if not self.document['cursor']else'INTENTIONAL DIFFERENCE',
                'editable_project':'PASS','mode':self.document['mode'],'native_compatibility':'REQUIRES MATERIAL ASSIGNMENT'if unassigned else'REQUIRES NATIVE BUILD',
                'unassigned_meshes':unassigned,'runtime_qualification':'NOT TESTED','original_source_changed':False,
                'source_effects_retained_in_parent':len(features(self.source)),
                'source_runtime_equivalence':'NOT CLAIMED by derived MR material substitutions'}

    def export_scene(self,output):
        scene=self.evaluate();root=Path(self.document['source_path']).parent
        assets={name:u.read_bounded(root/name,size)for name,size,_ in u._bindings(scene)}
        return u.save_scene(scene,Path(output),assets,protected_roots=[root])


def authored_profile(project,scene_path,*,normalized_to_mr,scale):
    """Explicit donor-neutral Classic/Customized selection, not source fidelity."""
    from .universal_scene_bridge import SCHEMA as PROFILE
    if project.document['mode']=='Source Fidelity':raise ValueError('Use the existing qualified source profile for Source Fidelity')
    if type(scale)not in(int,float)or not 0<scale<=100:raise ValueError('Explicit bounded authoring scale required')
    scene=u.load_scene(Path(scene_path));materials={m['id']:m for m in scene['materials']};rules={};claims=[]
    selected=[n for n in scene['nodes']if n['visible']and n['mesh_ids']];wheels={n['id']:n['id']for n in selected if n.get('role')=='wheel'}
    if not wheels:raise ValueError('Explicit wheel instances required for shared native bridge')
    for mesh in scene['meshes']:
        if not any(mesh['id']in n['mesh_ids']for n in selected):continue
        material=materials[mesh['material_id']];rule=material.get('authored_rule')
        if rule is None:raise ValueError('Assign a native material to derived mesh '+mesh['id'])
        approved={k:copy.deepcopy(v)for k,v in rule.items()if k!='opacity'}
        approved.update(interpretation='mr_authoring')
        approved.setdefault('allow_alpha_flatten',approved['mode']=='opaque')
        rules[material['id']]=approved
        claims.append({'mesh_id':mesh['id'],'material_id':mesh['material_id'],'triangles':'all','role':rule['role'],
                       'interpretation':'mr_authoring','evidence':rule['evidence']})
    factor=u.IDENTITY[:]
    for i in(0,5,10):factor[i]=scale
    return {'schema':PROFILE,'source_scene_sha256':u.sha(Path(scene_path).read_bytes()),'normalized_to_mr':normalized_to_mr,
            'authoring_transform':factor,'transform_evidence':'Explicit user authoring scale/basis; not recovered original physical units',
            'body_node_ids':[n['id']for n in selected if n.get('role')!='wheel'],'wheel_slots':wheels,
            'canonical_wheel_slot':next(iter(wheels)),'materials':rules,'texture_row_policy':'preserve','uv_v_policy':'preserve',
            'semantics':{'schema':'universal-vehicle-semantics/1','source_scene_sha256':u.sha(Path(scene_path).read_bytes()),'claims':claims}}


def build_fixture(project,output,template,*,scale,normalized_to_mr=None,references=None):
    """Existing shared bridge/writers, standalone geometry proof, no game install.

    Constant-color unlit overlays use exact selected faces. They preserve the
    opaque base; this is generic authored Glow, not recovery of donor lighting.
    Brake uses existing qualified blight OFF/ON grammar. Textured emission masks
    and controller integration with pre-existing native candidates are separate.
    """
    from dataclasses import replace
    from .universal_scene_bridge import compile_scene
    from .scene_dx_writer import write_scene_dx,ScenePart
    from .addon_sdk.native_states import wrap_states,validate_state_scene
    from .glass_authoring import subset
    from .topology_writer import DrawGeometry
    source=Path(project.document['source_path'])
    if u.sha(u.read_bounded(source,u.MAX_JSON_BYTES))!=project.document['source_sha256']or u.sha(u.read_bounded(source.parent/'manifest.json',2*1024*1024))!=project.document['manifest_sha256']:
        raise ValueError('Immutable parent changed before native build')
    u.load_scene(source) # Full private-sidecar verification; preview caches are not native approval.
    output=u.output_directory(Path(output),[Path(project.document['source_path']).parent,Path(project.source['source']['root'])])
    project.export_scene(output/'evaluated')
    path=output/'evaluated/scene.json';scene=u.load_scene(path)
    profile=authored_profile(project,path,normalized_to_mr=normalized_to_mr or u.IDENTITY[:],scale=scale)
    compiled=compile_scene(path,profile,references=references)
    native={};effects=scene.get('authored_effects',{});meshes={m['id']:m for m in scene['meshes']}
    white='authored-glow-white-tga'
    if effects:
        from .universal_scene_bridge import _dxt
        compiled['textures'][white+'.dxt']=_dxt(1,1,bytes([255]*4),'preserve')
    def emit(parts,records):
        items=[];brake_off=[];brake_on=[]
        for part,record in zip(parts,records):
            mesh=meshes[record['mesh_id']];groups={}
            for local,source in enumerate(record['source_triangle_ids']):
                effect=effects.get(mesh['face_ids'][source]);key=None if effect is None else(effect['trigger'],tuple(effect['rgba']))
                groups.setdefault(key,[]).append(local)
            for key,ids in groups.items():
                base=replace(part,geometry=subset(part.geometry,ids))
                if key is None:items.append(base);continue
                trigger,rgba=key;r,g,b,a=rgba
                geometry=DrawGeometry(tuple(replace(v,color=bytes((b,g,r,a)))for v in base.geometry.vertices),base.geometry.triangles)
                glow=ScenePart(geometry,(white,'Null','Null'),alpha=a!=255,alpha_test=False,environment=False,diffuse=False)
                if trigger=='always':items.extend((base,glow))
                else:brake_off.append(base);brake_on.extend((base,glow))
        if brake_off:
            # Existing blight has a bounded17-draw case limit. Do not silently
            # expand this controller or steal a runtime slot to evade the bound.
            items.append(('blight',brake_off,brake_on))
        data=wrap_states(template,items)if brake_off else write_scene_dx(template,items,allow_unlit=bool(effects))
        if brake_off:validate_state_scene(template,data)
        return data
    native['car.dx']=emit(compiled['body_parts'],compiled['report']['body_draws'])
    native['complete.dx']=emit(compiled['complete_parts'],compiled['report']['complete_draws'])
    native['wheel.dx']=write_scene_dx(template,compiled['wheel_parts'])
    native.update(compiled['textures']);folder=output/'native';folder.mkdir()
    for name,blob in native.items():(folder/u.relative_name(name)).write_bytes(blob)
    report={'schema':'editable-native-fixture/1','source_sha256':project.document['source_sha256'],
            'project_sha256':u.sha(u.canonical(project.document)),'mode':project.document['mode'],
            'files':{n:u.sha(b)for n,b in sorted(native.items())},'diagnostics':project.diagnostics(),
            'native_materials':compiled['report']['materials'],'source_changed':False,'runtime_qualified':False,
            'boundaries':['Geometry/material fixture only; no CarID, installation, physics or collision adaptation',
                          'Template collision retained; not fitted to edited geometry',
                          'Glow is exact-face constant-color authoring; source textures and ordinary diffuse base retained',
                          'Glass role affects rendering only, not native damage-zone creation']}
    from .scene_semantics import features
    report['original_source_features_retained_in_parent']=features(project.source)
    (output/'manifest.json').write_bytes(u.canonical(report));return report


def copy_native_material(path,draw_index,role):
    """Copy only the native fields expressible by the common ScenePart writer.

    The reference is user-selected/hash-pinned, not donor-source identity. This
    does not copy controllers, physics, undocumented state words or textures
    implicitly. Preserve the derived livery unless separately assigning texture.
    """
    from .dx import parse_dx_bytes
    path=Path(path).absolute();raw=u.read_bounded(path,128*1024*1024);model=parse_dx_bytes(raw)
    if not model.diagnostics.validated:raise ValueError('Invalid native material reference')
    index=_index(draw_index,len(model.physical_draws));draw=model.physical_draws[index]
    if draw.tag!=2 or len(draw.texture_tuple)!=3 or tuple(draw.flags_0x20)not in((0,0,1,1),(1,0,1,1),(1,1,1,1))or draw.unknown_0x24 not in(3,7):
        raise ValueError('Reference state cannot be represented by the current native writer')
    if role not in ROLES:raise ValueError('Explicit receiving surface role required')
    mode='opaque'if not draw.flags_0x20[0]else'alpha_test'if draw.flags_0x20[1]else'alpha_blend'
    if mode=='alpha_blend'and role!='glass':raise ValueError('Native blended reference requires isolated glass surfaces')
    rule={'mode':mode,'role':role,'interpretation':'mr_authoring','evidence':'User-selected native reference '+str(path)+' sha256='+u.sha(raw)+' draw='+str(index)}
    # Interpretation is already supplied by authored_profile, not a second key
    # or permission to waive unknown original shader behavior.
    rule.pop('interpretation')
    references={}
    if mode=='alpha_test':rule['alpha_ref']=128
    if draw.unknown_0x24&4:
        if role!='reflective_paint' or mode!='opaque':raise ValueError('Environment reference requires isolated opaque reflective paint')
        name=draw.texture_tuple[1]
        if Path(name).name!=name or '/'in name or '\\'in name or ':'in name:raise ValueError('Invalid local native environment name')
        texture=path.parent/(name+'.dxt');blob=u.read_bounded(texture,u.MAX_TEXTURE_BYTES)
        from .dxt import parse_dxt_bytes
        parse_dxt_bytes(blob);references[str(texture)] =blob;rule['environment_reference']={'key':str(texture),'sha256':u.sha(blob)}
    return rule,references
