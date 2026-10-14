"""Read-only PC face-to-original-PS2 material partition audit.

No meshes, textures, renderer sources or game data are written.  Face hashes are
the existing unsigned float32 geometry keys; source ordinals are provenance,
never a persistent runtime draw identifier.  Attributes remain PC native data.
"""
from collections import Counter, defaultdict
import hashlib
import importlib.util
import itertools
import json
from pathlib import Path
import struct

HERE = Path(__file__).resolve().parent
PORT = HERE.parents[2]
FAMILIES = {'LandCruiser': [8, 9], 'Bruno': [4], 'SeatBuggy': [7],
            'ChevyBlazer': [7], 'Xtrail': [1], 'Forester': [8, 9, 2]}
TOL = .001


def scalar_bits(v):
    if v == 0: v = 0.0
    return struct.pack('<f', v)


def face_hash(face):
    words = [tuple(struct.unpack('<I', scalar_bits(v))[0] for v in point) for point in face]
    return hashlib.sha256(b''.join(struct.pack('<III', *point) for point in sorted(words))).hexdigest()


def classification(matches):
    """Fail closed for contradictory source ownership, even at the same XYZ."""
    categories = {m['category'] for m in matches}
    return next(iter(categories)) if len(categories) == 1 else ('UNMATCHED' if not categories else 'AMBIGUOUS')


def ordered_runs(labels):
    runs = []
    for ordinal, label in enumerate(labels):
        if not runs or runs[-1]['category'] != label:
            runs.append({'first_source_face': ordinal, 'source_face_count': 1, 'category': label})
        else:
            runs[-1]['source_face_count'] += 1
    return runs


def classify_runtime_hashes(expected_full_digest, expected_counts, current_hashes):
    """Diagnostic algorithm: no runtime order assumptions, multiplicity checked."""
    current = Counter(current_hashes)
    digest = hashlib.sha256(''.join(sorted(current_hashes)).encode('ascii')).hexdigest()
    if digest != expected_full_digest or current != Counter({key: v['multiplicity'] for key, v in expected_counts.items()}):
        return None
    labels = []
    for key in current_hashes:
        label = expected_counts[key]['category']
        if label in ('AMBIGUOUS', 'UNMATCHED', 'DEGENERATE'): return None
        labels.append(label)
    return ordered_runs(labels)


def ps2_faces(scene, mesh):
    """Retain source strip provenance; exact source strip winding is UNKNOWN."""
    for sn, strip in enumerate(mesh['strips']):
        for newest in range(strip['start']+2, strip['start']+strip['count']):
            if scene.control(newest) & 1: continue
            indices = (newest-2, newest-1, newest)
            face = tuple(scene.position(i) for i in indices)
            if a.w.area_normal(face)[0] <= 1e-7: continue
            yield sn, newest-strip['start']-2, indices, face


def pc_attribute_digest(model, indices):
    # Original source normal/UV values only. Native data is not reconstructed
    # from these digests, and PS2 attributes are never copied into a PC vertex.
    output = bytearray()
    for index in indices:
        output.extend(b''.join(scalar_bits(v) for v in model.vertices.positions[index]))
        output.extend(b''.join(scalar_bits(v) for v in model.vertices.normals[index]))
        output.extend(model.vertices.colors[index*4:index*4+4])
        output.extend(b''.join(scalar_bits(v) for v in model.uv_sets[0].values[index]))
    return hashlib.sha256(output).hexdigest()


def main():
    global a
    spec=importlib.util.spec_from_file_location('source_vehicle_audit',PORT/'docs/full-coverage/vehicles/audit.py')
    a=importlib.util.module_from_spec(spec)
    spec.loader.exec_module(a)
    a.w.verify_inputs(a.PS2)
    manifest, _ = a.t.load_pak(a.PS2/'TNG.PAK')
    entries = {e['path'].replace('\\','/').split('/')[-2].upper(): e for e in manifest['entries']
               if e['kind']=='file' and '/VEHICLES/' in e['path'].replace('\\','/').upper()
               and e['path'].upper().endswith('CAR.PSM')}
    report = {'schema_version': 1, 'phase': 'PS2-VEHICLE-MODEL-PORT1_RACE_PARTITIONS',
              'tolerance': TOL, 'coordinate_system': 'MODEL_LOCAL_GAME_SOURCE',
              'runtime_validation': 'NOT_IMPLEMENTED_OR_TESTED', 'vehicles': []}
    for family, selected in FAMILIES.items():
        ps2_family = 'WOOLDAND' if family=='Forester' else family.upper()
        entry = entries[ps2_family]
        payload, provenance = a.t.read_payload(entry, a.PS2/'TNG.000')
        scene = a.r.decode_vehicle(payload)
        path = a.PC/family/'car.dx'
        model = a.parse_dx(path)
        item = {'pc_family': family, 'ps2_family': ps2_family,
                'ps2_source': {'path': entry['path'], 'sha256': a.sha(payload), 'provenance': provenance},
                'pc_source': {'path': str(path.relative_to(a.PC)).replace('\\','/'), 'sha256': a.sha(path.read_bytes())},
                'draws': []}
        report['vehicles'].append(item)
        index = defaultdict(list)
        for mesh in scene.meshes:
            if mesh['path'].count('.') != 1: continue
            slots = a.slot(mesh)
            contract = a.r.material_contract(mesh['material'], slots[1] if len(slots)>1 else '')
            category = contract['interned_shader'] or 'UNTAGGED_AUTHORED_MAPS'
            if contract['rubber_substring_preserved']: category = 'CARSHINY_RUBBER_AUTHORED_MAP'
            meta = {'path': mesh['path'], 'node_offset': mesh['node_offset'],
                    'material_offset': mesh['material_offset'], 'material': mesh['material'],
                    'textures': slots, 'category': category, 'handler': contract['handler']}
            for sn, fn, ids, face in ps2_faces(scene, mesh):
                value = (meta, sn, fn, ids, face)
                for key in {tuple(int(v//TOL) for v in p) for p in face}: index[key].append(value)
        for di in selected:
            draw = model.physical_draws[di]
            ids = model.draw_global_indices(draw)
            faces = a.faces(model, draw)
            labels = []; rows = []; count_keys = defaultdict(list)
            for ordinal, face in enumerate(faces):
                key = tuple(int(v//TOL) for v in face[0]); found=[]
                for delta in itertools.product((-1,0,1), repeat=3):
                    for meta, sn, fn, pids, candidate in index.get(tuple(key[i]+delta[i] for i in range(3)), ()):
                        error = a.w.corner_error(face, candidate)
                        if error <= TOL:
                            permutations = [p for p in itertools.permutations(range(3))
                                            if max(abs(face[i][k]-candidate[p[i]][k]) for i in range(3) for k in range(3)) <= TOL]
                            # Attribute residuals do not authorize importing attributes.
                            attr=[]
                            for perm in permutations:
                                normals=[]; uvs=[]
                                for corner in range(3):
                                    pi=ids[ordinal*3+corner]; si=pids[perm[corner]]
                                    pn=struct.unpack_from('<3f',payload,32+si*52)
                                    pu=struct.unpack_from('<2f',payload,32+si*52+20)
                                    normals.append(max(abs(model.vertices.normals[pi][k]-pn[k]) for k in range(3)))
                                    uvs.append(max(abs(model.uv_sets[0].values[pi][k]-pu[k]) for k in range(2)))
                                attr.append({'normal_max_abs':max(normals), 'uv_max_abs':max(uvs)})
                            best=min(attr, key=lambda row:(row['normal_max_abs'],row['uv_max_abs']))
                            found.append({**meta, 'source_strip': sn, 'source_strip_face': fn, 'corner_error': error, **best})
                label = 'DEGENERATE' if a.w.area_normal(face)[0] <= 1e-7 else classification(found)
                digest=face_hash(face);labels.append(label)
                rows.append({'source_face':ordinal,'face_hash':digest,'category':label,'matches':found})
                count_keys[digest].append(label)
            counts={key:{'multiplicity':len(values),'category':classification([{'category':v} for v in values])}
                    for key,values in sorted(count_keys.items())}
            bindings = {}
            for row in rows:
                for match in row['matches']:
                    bid = match['path']
                    if bid not in bindings:
                        bindings[bid] = {k:match[k] for k in ('path','node_offset','material_offset','material','textures','category','handler')}
                        bindings[bid].update({'source_face_ordinals':set(),'corner_max_abs':0.,'normal_max_abs':0.,'uv_max_abs':0.})
                    binding=bindings[bid]
                    binding['source_face_ordinals'].add(row['source_face'])
                    binding['corner_max_abs']=max(binding['corner_max_abs'],match['corner_error'])
                    binding['normal_max_abs']=max(binding['normal_max_abs'],match['normal_max_abs'])
                    binding['uv_max_abs']=max(binding['uv_max_abs'],match['uv_max_abs'])
            for binding in bindings.values():
                binding['matching_pc_faces']=len(binding.pop('source_face_ordinals'))
            item['draws'].append({'draw_index':draw.draw_index,'record_path':draw.record_path,'record_offset':draw.offset,
                'vertex_base':draw.vertex_base,'vertex_count':draw.local_vertex_max+1,'index_start':draw.index_start,
                'index_count':draw.index_count,'pc_material_slots':[s.value for s in draw.texture_slots],
                'pc_flags':draw.flags_0x20.hex(),'geometry_sha256':a.geometry_signature(faces),
                'pc_ordered_attribute_sha256':pc_attribute_digest(model,ids),
                'attribute_fingerprint_contract':'Per-index original DX XYZ + normal XYZ + raw four color bytes + UV0, packed little-endian float32; not proven current native upload bytes',
                'source_face_counts':dict(sorted(Counter(labels).items())), 'source_ordered_runs':ordered_runs(labels),
                'face_hash_categories':counts,'ps2_source_bindings':list(bindings.values()),
                'pc_ordered_face_hash_sha256':hashlib.sha256(''.join(r['face_hash'] for r in rows).encode('ascii')).hexdigest(),
                'stable_identity':a.sha(path.read_bytes())+':record:'+str(draw.offset),
                'source_winding':'Original PC ordered indices retained; exact PS2 strip orientation/cull semantics UNKNOWN'})
        print(family, [(d['draw_index'],d['source_face_counts'],len(d['source_ordered_runs'])) for d in item['draws']],flush=True)
    targets={d['geometry_sha256'] for v in report['vehicles'] for d in v['draws']}
    counts={d['index_count'] for v in report['vehicles'] for d in v['draws']}
    hits={h:[] for h in sorted(targets)}; failures=[];files=0
    for directory in sorted(a.PC.iterdir()):
        if not directory.is_dir(): continue
        for path in sorted(directory.iterdir()):
            if path.suffix.lower()!='.dx':continue
            files+=1
            try: other=a.parse_dx(path)
            except Exception as error:
                failures.append({'path':str(path.relative_to(a.PC)).replace('\\','/'),'error':str(error)})
                continue
            for draw in other.physical_draws:
                if draw.index_count not in counts:continue
                digest=a.geometry_signature(a.faces(other,draw))
                if digest in hits:hits[digest].append({'path':str(path.relative_to(a.PC)).replace('\\','/'),'draw_index':draw.draw_index})
    report['negative_controls']={'pc_dx_files':files,'unsupported':failures,'exact_shape_hits':hits,
                                 'menu_repeats_require_race_context':'Same family COMPLETE/CAR source overlap is not independently sufficient admission.'}
    for vehicle in report['vehicles']:
        for draw in vehicle['draws']:
            draw['exact_geometry_owner_families']=sorted({h['path'].split('/')[0] for h in hits[draw['geometry_sha256']]})
            draw['unique_geometry_vehicle_family']=draw['exact_geometry_owner_families']==[vehicle['pc_family']]
    (HERE/'partition-evidence.json').write_text(json.dumps(report,indent=2,allow_nan=False)+'\n',encoding='utf8')


if __name__=='__main__': main()
