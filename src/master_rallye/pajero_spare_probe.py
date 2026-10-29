"""Small optional source-owned spare instance; no livery or native authoring."""
from copy import deepcopy
from collections import Counter
from . import universal_vehicle_scene as u
from .source_scene_preview import _mul, _point


def inspect(scene):
    nodes = {n['id']:n for n in scene['nodes']}; meshes = {m['id']:m for m in scene['meshes']}
    materials = {m['id']:m for m in scene['materials']}
    def world(n):
        return _mul(world(nodes[n['parent_id']]),n['local_transform']) if n['parent_id'] else n['local_transform']
    rows = []
    for n in nodes.values():
        if 'SPAREWHEEL' not in n['name'] and n.get('role')!='wheel': continue
        points = [_point(world(n),p) for mid in n['mesh_ids'] for p in meshes[mid]['positions']]
        edges = Counter()
        for mid in n['mesh_ids']:
            m = meshes[mid]
            for tri in m['triangles']:
                p = [tuple(round(v,6)for v in m['positions'][i])for i in tri]
                for i in range(3):edges[tuple(sorted((p[i],p[(i+1)%3])))] += 1
        rows.append({'node':deepcopy(n),'parent_name':nodes[n['parent_id']]['name'] if n['parent_id'] else None,
                     'world_transform':world(n),'world_bounds':[[min(p[i]for p in points),max(p[i]for p in points)]for i in range(3)],
                     'triangles':sum(len(meshes[mid]['triangles'])for mid in n['mesh_ids']),
                     'six_decimal_position_boundary_edges':sum(v==1 for v in edges.values()),
                     'materials':[deepcopy(materials[meshes[mid]['material_id']])for mid in n['mesh_ids']]})
    return {'schema':'pajero-spare-probe/1','nodes':rows,
            'visibility':'Original HIR flags retained. Active runtime equipment choice UNKNOWN.',
            'wheel_backing':'DEFERRED: original transparent wheel submaterials plus incomplete shader semantics; boundary edges do not alone prove absent back geometry. No source cull/alpha repair or black cap invented.'}


def overlay(scene, enabled):
    if type(enabled)is not bool: raise ValueError('Explicit overlay boolean')
    result = deepcopy(scene)
    if not enabled: return result
    sources = [n for n in scene['nodes']if n['name']=='PAJ_SPAREWHEEL2']
    if len(sources)!=1: raise ValueError('Missing/ambiguous qualified spare node')
    original = sources[0]; meshes = {m['id']:m for m in scene['meshes']}
    points = [p for mid in original['mesh_ids']for p in meshes[mid]['positions']]
    if not points: raise ValueError('Empty source spare')
    centre = [(min(p[i]for p in points)+max(p[i]for p in points))/2 for i in range(3)]
    # An explicitly authored rear mount: +90deg Y, original thickness along Z.
    target = [0.,0.45,-2.02]
    matrix = [0.,0.,1.,target[0]-centre[2],0.,1.,0.,target[1]-centre[1],-1.,0.,0.,target[2]+centre[0],0.,0.,0.,1.]
    n = deepcopy(original);n.update(id='derived-rear-spare',name='MR-inspired rear spare — original Xbox mesh copy',parent_id=None,
                                  local_transform=matrix,source_local_transform=None,source_visible=False,visible=True)
    n['source_transform_record'] = {'derived_from':original['id'],'target_center':target,'authored_rotation_y_degrees':90,
                                    'original_source_record':original['source_transform_record']}
    n['transform_evidence'] = 'USER-AUTHORED visual overlay, not original Xbox equipment selection or recovered MR mesh'
    result['nodes'].append(n)
    result['metadata']['display_name'] = 'Xbox Pajero — optional MR-inspired rear spare / WARN'
    result['metadata']['spare_overlay'] = {'enabled':True,'original_node':original['id'],'new_geometry':False,'source_mesh_ids':original['mesh_ids'],
                                         'backing':'NOT GENERATED','native_candidate':'NOT CREATED'}
    u.validate_scene(result)
    return result
