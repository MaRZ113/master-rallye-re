"""Explicit stock resource copy-on-write projects. No registration or source mutation."""
import hashlib,json,re,shutil
from pathlib import Path

QUALIFIED_STOCK={1:"Pajero",18:"Megane"} # original 00458E70 registration, exact PC build

def identity(family,car_id):
    if type(car_id) is not int or QUALIFIED_STOCK.get(car_id)!=family: raise ValueError("unqualified stock family/CarID pair")

def digest(p): return hashlib.sha256(p.read_bytes()).hexdigest()
def safe(root,relative):
    if not isinstance(relative,str) or not relative or relative.endswith('/') or any(not x or x in ('.','..') for x in relative.split('/')): raise ValueError('unsafe resource path')
    p=Path(relative)
    if p.is_absolute() or '..' in p.parts or ':' in relative or '\\' in relative: raise ValueError('unsafe resource path')
    q=root/p
    if not q.resolve().is_relative_to(root.resolve()): raise ValueError('resource escapes root')
    if any(x.is_symlink() or getattr(x,'is_junction',lambda:False)() for x in (q,*q.parents)): raise ValueError('linked resource path')
    return q

def create(source,project,family,car_id):
    source=Path(source).resolve(); project=Path(project)
    if project.exists(): raise ValueError('project already exists')
    identity(family,car_id)
    if not re.fullmatch('[A-Za-z][A-Za-z0-9_]{0,39}',family): raise ValueError('invalid family')
    relative='DataGx/Vehicles/'+family
    folder=safe(source,relative)
    files=sorted(p for p in folder.rglob('*') if p.is_file())
    if not files: raise ValueError('empty stock family')
    records={p.relative_to(source).as_posix():digest(safe(source,p.relative_to(source).as_posix())) for p in files}
    project.mkdir(parents=True)
    for rel in records:
        dest=safe(project/'resources',rel);dest.parent.mkdir(parents=True,exist_ok=True);shutil.copyfile(safe(source,rel),dest)
    data={'version':1,'kind':'stock_resource_override','car_id':car_id,'family':family,'source_root':str(source),'original_sha256':records,'identity_policy':'preserve'}
    (project/'stock-project.json').write_text(json.dumps(data,indent=2)+'\n')
    return data

def build(project,output):
    project=Path(project);output=Path(output)
    data=json.loads((project/'stock-project.json').read_text())
    if data['version']!=1 or data['kind']!='stock_resource_override' or data['identity_policy']!='preserve': raise ValueError('unsupported project')
    identity(data['family'],data['car_id'])
    source=Path(data['source_root']);records=data['original_sha256'];root=project/'resources'
    if not isinstance(records,dict) or not records or any(not isinstance(v,str) or not re.fullmatch('[0-9a-f]{64}',v) for v in records.values()): raise ValueError('invalid original resource pins')
    if len({rel.casefold() for rel in records})!=len(records): raise ValueError('case-insensitive resource conflict')
    prefix='DataGx/Vehicles/'+data['family']+'/'
    if any(not rel.startswith(prefix) for rel in records): raise ValueError('resource ownership violation')
    actual={p.relative_to(root).as_posix() for p in root.rglob('*') if p.is_file()}
    if actual!=set(records): raise ValueError('resource additions/removals require separate qualification')
    changes={}
    for rel,original in records.items():
        if digest(safe(source,rel))!=original: raise ValueError('retail source changed: '+rel)
        p=safe(root,rel)
        if digest(p)!=original: changes[rel]={'original_sha256':original,'sha256':digest(p)}
    validate_changes(root, changes)
    if output.exists(): raise ValueError('output already exists')
    output.mkdir(parents=True)
    for rel in changes:
        dest=safe(output/'overrides',rel);dest.parent.mkdir(parents=True,exist_ok=True);shutil.copyfile(safe(root,rel),dest)
    report={'version':1,'car_id':data['car_id'],'family':data['family'],'resources':changes,'zero_edit':not changes,'installation':'not installed; compose only after semantic DX/DXT validation'}
    (output/'override-manifest.json').write_text(json.dumps(report,indent=2)+'\n');return report


def validate_changes(root, changes):
    """Only known resource formats may cross the authoring/install boundary."""
    from master_rallye.dx import parse_dx_bytes
    from master_rallye.dxt import parse_dxt_bytes
    for rel in changes:
        raw=safe(root,rel).read_bytes()
        if rel.lower().endswith('.dxt'):
            parse_dxt_bytes(raw,rel)
        elif rel.lower().endswith('.dx'):
            model=parse_dx_bytes(raw)
            if not model.diagnostics.validated:
                raise ValueError('invalid changed DX: '+rel)
        else:
            raise ValueError('unqualified changed resource format: '+rel)


def validated_overrides(project):
    """Read a COW project without writing files; return pinned changed resources.

    The roster composer must independently require each original hash to match
    the destination being overridden. This function never registers a CarID.
    """
    import tempfile
    with tempfile.TemporaryDirectory() as directory:
        output=Path(directory)/'validated'
        report=build(project,output)
        result={rel:safe(output/'overrides',rel).read_bytes() for rel in report['resources']}
        if any(hashlib.sha256(raw).hexdigest()!=report['resources'][rel]['sha256'] for rel,raw in result.items()):
            raise ValueError('resource changed during validation')
        validate_changes(output/'overrides',result)
        return result


def restore(project, relative):
    """Restore one owned resource from its immutable, hash-pinned retail input."""
    project=Path(project)
    data=json.loads((project/'stock-project.json').read_text())
    identity(data['family'],data['car_id'])
    if data.get('identity_policy')!='preserve' or relative not in data['original_sha256']:
        raise ValueError('unowned restore resource')
    source=safe(Path(data['source_root']),relative)
    if digest(source)!=data['original_sha256'][relative]: raise ValueError('retail source changed')
    destination=safe(project/'resources',relative)
    shutil.copyfile(source,destination)
    return {'restored':relative,'sha256':digest(destination)}

def conflicts(manifests):
    owners={}
    for i,m in enumerate(manifests):
        for rel in m['resources']:
            key=rel.casefold()
            if key in owners: raise ValueError('resource conflict: '+rel)
            owners[key]=i
    return owners
