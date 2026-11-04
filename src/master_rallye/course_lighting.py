"""Optional Course SDK material lighting metadata; no per-object geometry hashes.

Generated LSM1 is an external capability table, not a runtime authorization by
itself. The proxy still verifies the current race/pass, texture identity, shader
state, buffer provenance and geometry. Unknown/ambiguous materials are excluded.
"""
from __future__ import annotations
from collections import defaultdict
import hashlib
import json
from pathlib import Path
import re
import struct
import math

NOISE, PLAIN, ALPHA_TEST, TWO_SIDED, DENY, ENVIRONMENT, ENV_TEXTURE = 1, 2, 4, 8, 16, 32, 64
STATIC_ENVIRONMENTS = ('aluminium-tga','whitepaint-tga','silverpaint-tga')
ROLES = {'road': 1, 'terrain': 2, 'vegetation': 3, 'static': 4, 'signage': 4, 'exclude': 0}


def material_role(name: str, textures: tuple[str, ...], explicit: str | None = None) -> tuple[int, int]:
    label = name.lower().removesuffix('-tga')
    # Exclusions outrank even author-supplied capabilities. Reflective secondary
    # resources and unsupported shader combinations cannot become a plain pass.
    excluded = ('water', 'glass', 'window', 'windscreen', 'windshield', 'perspex', 'glow', 'flare', 'lamp', 'headlight', 'taillight', 'shadow', 'decal',
                'boat', 'wheel', 'tyre', 'tire', 'tred', 'reflection', 'chrome')
    if any(token in label for token in excluded) or len(textures) != 3 or textures[1] != 'Null' or textures[2] not in ('Null', 'noise-tga'):
        return 0, DENY
    if explicit is not None and explicit not in ROLES:
        raise ValueError(f'unknown lighting role {explicit!r}')
    if explicit == 'exclude':
        return 0, DENY
    noise = textures[2] == 'noise-tga'
    if explicit == 'signage' and noise:
        return 0, DENY  # authored opaque plain panels, not a secondary/noise pass
    if explicit:
        category = ROLES[explicit]
    elif noise:
        category = 1 if any(token in label for token in ('road', 'track', 'asphalt', 'tar_')) else 2
    elif any(token in label for token in ('tree', 'shrub', 'bush', 'bark', 'pinerow', 'plant')):
        category = 3
    elif any(token in label for token in ('wall', 'wood', 'plank', 'concrete', 'bridge', 'hut', 'house', 'building', 'castle', 'church', 'gate', 'fence', 'brick', 'roof', 'tent', 'barn', 'metal', 'caravan', 'container', 'gantry', 'scaffold')):
        category = 4
    else:
        return 0, DENY
    flags = NOISE if noise else PLAIN
    if category == 3:
        flags |= ALPHA_TEST | TWO_SIDED
    return category, flags


def static_plain_capability(name,contracts,explicit=None):
    # A material capability grants only the opaque PLAIN pass. An aluminium
    # secondary requires the separate environment capability and live contract.
    # This helper grants only a verified static plain counterpart.
    return explicit in (None,'static') and material_role(name,(name,'Null','Null'))==(4,PLAIN) and all(len(c)==3 and c[1] in ('Null','aluminium-tga') and c[2]=='Null' for c in contracts)


def static_environment_capability(name, contracts, explicit=None):
    # In a validated Course source, the exact aluminium shader binding is a
    # material semantic, even if the author's diffuse label is just "top".
    # Live admission still needs opaque identity-world geometry and normals,
    # both texture identities, and the original reflection stage contract.
    return explicit in (None,'static') and material_role(name,(name,'Null','Null'),'static')==(4,PLAIN) and all(len(c)==3 and c[1] in ('Null',*STATIC_ENVIRONMENTS) and c[2]=='Null' for c in contracts) and any(c[1] in STATIC_ENVIRONMENTS for c in contracts)


def geometry_role(model, draws):
    """Conservative source-only opaque plain surface recognition.

    Ground requires repeated UV and CW upward faces. Signage requires small
    connected upright panels; mixed, horizontal props and arbitrary solids fail.
    Runtime shader/alpha/resource checks remain mandatory.
    """
    faces=[]
    for draw in draws:
        ix=model.local_indices[draw.index_start:draw.index_start+draw.index_count]
        for j in range(0,len(ix),3):
            ids=[draw.vertex_base+i for i in ix[j:j+3]]
            a,b,c=[model.vertices.positions[i] for i in ids]
            u=[b[k]-a[k] for k in range(3)];v=[c[k]-a[k] for k in range(3)]
            n=(u[2]*v[1]-u[1]*v[2],u[0]*v[2]-u[2]*v[0],u[1]*v[0]-u[0]*v[1])
            length=math.sqrt(sum(x*x for x in n))
            if length>1e-8:faces.append((ids,[x/length for x in n],length))
    if not faces:return None
    area=sum(f[2] for f in faces)
    if sum(w for _,n,w in faces if n[1]>.55)>.95*area:
        # Only geometric ground, rather than a name-based basegrass exception.
        points=[model.vertices.positions[i] for ids,_,_ in faces for i in ids]
        spans=[max(p[k] for p in points)-min(p[k] for p in points) for k in range(3)]
        if max(spans[0],spans[2])>20 and area>100:return 'terrain'
    # Partition by shared physical positions, including UV-split duplicates.
    groups={};parent={}
    def find(x):
        parent.setdefault(x,x)
        while parent[x]!=x:parent[x]=parent[parent[x]];x=parent[x]
        return x
    for ids,n,w in faces:
        keys=[tuple(round(x,3) for x in model.vertices.positions[i]) for i in ids]
        roots=[find(k) for k in keys]
        for r in roots[1:]:parent[r]=find(roots[0])
    for ids,n,w in faces:
        key=find(tuple(round(x,3) for x in model.vertices.positions[ids[0]]))
        groups.setdefault(key,[]).append((ids,n,w))
    for component in groups.values():
        points=[model.vertices.positions[i] for ids,_,_ in component for i in ids]
        spans=[max(p[k] for p in points)-min(p[k] for p in points) for k in range(3)]
        height=spans[1];width=math.hypot(spans[0],spans[2])
        if not (.25<height<12 and 1.5*height<width<80):return None
        ref=component[0][1]
        if any(abs(n[1])>.5 or abs(sum(a*b for a,b in zip(n,ref)))<.90 for _,n,_ in component):return None
        # Reject boxes/solid structures and disconnected crossed billboards.
        deviation=max(abs(sum((p[k]-points[0][k])*ref[k] for k in range(3))) for p in points)
        if deviation>min(.3,height*.12):return None
    return 'signage' if groups else None


def fixed(value: str, size: int) -> bytes:
    data = value.encode('ascii')
    if not data or len(data) >= size or any(c < 32 or c >= 127 for c in data):
        raise ValueError(f'invalid metadata text {value!r}')
    return data + bytes(size - len(data))


def orientation_votes(model, draw):
    """Count unique surfaces; a proven front/back pair has native CW authority.

    Opposite copies share vertex indices and authored normals. They cannot
    vote against each other and make an opaque wall look ambiguous. Genuine
    mixed orientation on unpaired surfaces still fails the existing policy.
    """
    signs={}
    indices=model.local_indices[draw.index_start:draw.index_start+draw.index_count]
    for j in range(0,len(indices),3):
        vertices=tuple(draw.vertex_base+i for i in indices[j:j+3])
        a,b,c=[model.vertices.positions[i] for i in vertices]
        u=[b[k]-a[k] for k in range(3)];v=[c[k]-a[k] for k in range(3)]
        cross=(u[1]*v[2]-u[2]*v[1],u[2]*v[0]-u[0]*v[2],u[0]*v[1]-u[1]*v[0])
        normal=[sum(model.vertices.normals[i][k] for i in vertices) for k in range(3)]
        dot=sum(x*y for x,y in zip(cross,normal))
        if math.isfinite(dot) and abs(dot)>1e-5:signs.setdefault(tuple(sorted(vertices)),set()).add(int(dot>0))
    votes=[0,0]
    for candidates in signs.values():votes[0 if len(candidates)==2 else next(iter(candidates))]+=1
    return votes


def orientation_policy(category: int, flags: int, negative: int, positive: int,
                       authored_signage: bool = False) -> tuple[int, int, int]:
    """Separate material capability from source smoothing-normal orientation.

    The native opaque base_noise pass has a proven CW geometry convention.
    Mixed authored normals in a PS2 source must not poison the same valid PC
    material. Normals remain optional shading hints, checked against the live
    face; missing/opposed hints fall back to current geometric normals.
    Unsupported shaders/ambiguous roles retain DENY independently of this rule.
    """
    winding = 1 if positive > negative else -1
    if category == 3 or (flags & (NOISE|ENVIRONMENT) and not flags & DENY) or (authored_signage and category in (2,4) and flags == PLAIN):
        winding = -1
    elif not flags & DENY and (not negative + positive or max(negative, positive) < .9 * (negative + positive)):
        category, flags = 0, DENY
    return category, flags, winding


def encode_metadata(records: list[dict]) -> bytes:
    rows = bytearray()
    for r in sorted(records, key=lambda r: (r['course'], r['texture_sha256'])):
        if not re.fullmatch(r'[A-Za-z0-9_-]{1,63}', r['course']):
            raise ValueError('invalid course identifier')
        rows += fixed(r['course'], 64) + fixed(r['material'], 96) + fixed(r['texture_sha256'], 65)
        rows += struct.pack('<IIi', r['category'], r['flags'], r.get('winding', -1))
    return struct.pack('<4sII', b'LSM1', 1, len(records)) + hashlib.sha256(rows).hexdigest().encode('ascii') + rows


def decode_metadata(data: bytes) -> list[dict]:
    """Read a previously generated material table for an additive SDK export."""
    if len(data)<76 or len(data)>4*1024*1024:raise ValueError('metadata size')
    magic,version,count=struct.unpack_from('<4sII',data)
    if magic!=b'LSM1' or version!=1 or count>16384 or len(data)!=76+237*count:raise ValueError('metadata header')
    if data[12:76]!=hashlib.sha256(data[76:]).hexdigest().encode():raise ValueError('metadata checksum')
    result=[]
    for i in range(count):
        row=data[76+237*i:76+237*(i+1)]
        def text(start,size):
            field=row[start:start+size]
            if b'\0' not in field:raise ValueError('unterminated metadata text')
            value=field.split(b'\0')[0].decode('ascii');fixed(value,size);return value
        category,flags,winding=struct.unpack_from('<IIi',row,225)
        course=text(0,64);digest=text(160,65);name=text(64,96)
        if not re.fullmatch(r'[A-Za-z0-9_-]{1,63}',course) or not re.fullmatch('[0-9a-f]{64}',digest):raise ValueError('metadata identity')
        if category>4 or flags&~127 or winding not in (-1,1) or (not category and not flags&DENY) or ((flags&TWO_SIDED) and category!=3) or ((flags&ALPHA_TEST) and category!=3 and (category!=4 or flags&ENVIRONMENT)) or (flags&ENVIRONMENT and (category!=4 or flags&DENY)) or (flags&ENV_TEXTURE and (category!=0 or flags!=(DENY|ENV_TEXTURE) or name not in STATIC_ENVIRONMENTS)):raise ValueError('metadata capability')
        result.append(dict(course=course,material=text(64,96),texture_sha256=digest,category=category,flags=flags,winding=winding))
    return result


def export_lighting_metadata(sources: list[Path], courses: list[str], output: Path,
                             roles: dict[str, dict[str, str]] | None = None, base: bytes | None = None) -> dict:
    """Export stock/custom DX material roles with optional author overrides.

    Overrides map course -> exact texture label -> role. Renaming a layout,
    changing topology/vertices/UV or creating more instances needs no Proxy
    source changes. Custom unknown plain materials need an explicit role.
    """
    from .dx_course import parse_course_dx
    from .dxt import parse_dxt
    if output.exists():
        raise ValueError('fresh output directory required')
    records={(r['course'],r['texture_sha256']):r for r in decode_metadata(base)} if base else {}
    base_records=len(records)
    evidence=[]
    roles = roles or {}
    for source in sources:
        for course in courses:
            if not re.fullmatch(r'[A-Za-z0-9_-]{1,63}', course):
                raise ValueError('invalid course identifier')
            folder = source / course
            path = folder / (course.lower() + '.dx')
            if not path.exists():
                continue
            model = parse_course_dx(path)
            if not model.course_render_validated:
                raise ValueError(f'unvalidated source {path}')
            bindings = defaultdict(set)
            material_draws = defaultdict(list)
            orientation = defaultdict(lambda: [0,0])
            for draw in model.physical_draws:
                if draw.index_count:
                    bindings[draw.texture_tuple[0]].add(tuple(draw.texture_tuple))
                    material_draws[draw.texture_tuple[0]].append(draw)
                    votes=orientation_votes(model,draw)
                    for i in (0,1):orientation[draw.texture_tuple[0]][i]+=votes[i]
            report = {'course': course, 'source': str(path), 'source_sha256': hashlib.sha256(path.read_bytes()).hexdigest(), 'materials': []}
            for name, contracts in sorted(bindings.items()):
                texture = folder / (name + '.dxt')
                if not texture.exists():
                    texture = next((root / course / (name + '.dxt') for root in sources if (root / course / (name + '.dxt')).exists()), texture)
                if not texture.exists():
                    continue
                tex = parse_dxt(texture)
                capabilities = {material_role(name, contract, roles.get(course, {}).get(name)) for contract in contracts}
                category, flags = capabilities.pop() if len(capabilities) == 1 else (0, DENY)
                inferred=None
                # An exclusion can never be overridden by shape. Only otherwise
                # unknown, plain bindings are considered by this SDK classifier.
                if category==0 and all(c[1]=='Null' and c[2] in ('Null','noise-tga') for c in contracts) and not any(t in name.lower() for t in ('water','glass','glow','lamp','shadow','decal','boat','wheel','tyre','tire','tred','reflection','chrome')) and roles.get(course,{}).get(name) is None:
                    inferred=geometry_role(model,material_draws[name])
                    if inferred:
                        qualified={material_role(name,c,inferred) for c in contracts}
                        if len({c for c,f in qualified})==1 and all(not f&DENY for c,f in qualified):
                            category=next(iter(qualified))[0];flags=0
                            for _,f in qualified:flags|=f
                if static_plain_capability(name,contracts,roles.get(course,{}).get(name)):category,flags=4,PLAIN
                environment=static_environment_capability(name,contracts,roles.get(course,{}).get(name))
                if environment:category,flags=4,PLAIN|ENVIRONMENT
                negative,positive=orientation[name]
                category,flags,winding=orientation_policy(category,flags,negative,positive,
                    roles.get(course, {}).get(name) == 'signage' or inferred in ('signage','terrain'))
                # Coverage is independent of surface role: certified opaque
                # static panels may share a texture with a native alpha-test
                # subrange (railings, roof edges, boards). RGB-only lighting
                # leaves texture/vertex alpha and the coverage test untouched.
                if category == 4 and flags == PLAIN:
                    flags |= ALPHA_TEST
                opaque = bytearray(tex.bgra)
                opaque[3::4] = bytes([255]) * (len(opaque) // 4)
                    # Topology is regenerated at runtime; orientation policy is
                    # inferred from the original authored normal array per material.
                for pixels in (tex.bgra, bytes(opaque)):
                    digest = hashlib.sha256(pixels).hexdigest()
                    record = dict(course=course, material=name, texture_sha256=digest, category=category, flags=flags, winding=winding)
                    key = course, digest
                    previous = records.get(key)
                    if previous and previous['category']==record['category'] and previous['winding']==record['winding'] and not (previous['flags']|record['flags'])&DENY:
                        record['flags']|=previous['flags']
                    elif previous and any(previous[k] != record[k] for k in ('category', 'flags', 'winding')):
                        # Same pixels with different authored roles: permanently
                        # exclude the content, including aliases in later sources.
                        record.update(category=0, flags=DENY)
                    records[key] = record
                report['materials'].append({'material': name, 'category': category, 'flags': flags, 'winding':winding,'geometry_inferred_role':inferred,'source_normal_orientation_votes':orientation[name], 'bindings': sorted(contracts), 'texture_file_sha256': hashlib.sha256(texture.read_bytes()).hexdigest()})
            # Secondary identity is exported once per course, independent of
            # objects/layout topology. It is never a diffuse admission record.
            environment_names={c[1] for m in report['materials'] if m['flags']&ENVIRONMENT for c in m['bindings'] if c[1] in STATIC_ENVIRONMENTS}
            for environment_name in sorted(environment_names):
                secondary=next((root/course/(environment_name+'.dxt') for root in sources if (root/course/(environment_name+'.dxt')).exists()),None)
                if secondary is None:raise ValueError('missing certified static environment secondary: '+environment_name)
                tex=parse_dxt(secondary);opaque=bytearray(tex.bgra);opaque[3::4]=bytes([255])*(len(opaque)//4)
                for pixels in (tex.bgra,bytes(opaque)):
                    digest=hashlib.sha256(pixels).hexdigest();key=course,digest
                    certificate=dict(course=course,material=environment_name,texture_sha256=digest,category=0,flags=DENY|ENV_TEXTURE,winding=-1)
                    previous=records.get(key)
                    if previous and previous['category']!=0:raise ValueError('environment/diffuse identity collision')
                    records[key]=certificate
                report.setdefault('environment_sources',[]).append({'path':str(secondary),'sha256':hashlib.sha256(secondary.read_bytes()).hexdigest()})
            evidence.append(report)
    data = encode_metadata(list(records.values()))
    result = {'schema': 1, 'status': 'OFFLINE_MATERIAL_METADATA_RUNTIME_ADMISSION_REQUIRED', 'format': 'LSM1', 'records': len(records),'base_records':base_records,
              'metadata_sha256': hashlib.sha256(data).hexdigest(), 'payload_sha256': data[12:76].decode('ascii'),
              'per_object_geometry_hashes': False, 'normal_source': 'runtime area-weighted triangle normals; not authored smoothing normals',
              'sources': evidence}
    output.mkdir(parents=True)
    (output / 'materials.lsm').write_bytes(data)
    (output / 'provenance.json').write_text(json.dumps(result, indent=2) + '\n', encoding='utf-8')
    return result
