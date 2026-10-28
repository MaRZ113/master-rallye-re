"""Read-only provenance inspection for imported Universal Vehicle Scenes."""
from pathlib import Path
import re

from master_rallye.universal_vehicle_scene import load_scene, read_bounded, sha, MAX_JSON_BYTES, MAX_OUTPUT_BYTES, relative_name, unlinked


def verify_baseline(record):
    """The source-derived MR baseline remains separate from editable assets."""
    if not isinstance(record,dict) or not isinstance(record.get('assets'),str) or not Path(record['assets']).is_absolute():
        raise ValueError('Immutable source baseline requires an absolute resource root')
    root=Path(record['assets']);unlinked(root);pins=record.get('sha256')
    if not isinstance(pins,dict)or not 1<=len(pins)<=256:raise ValueError('Immutable source baseline file budget')
    for name,digest in pins.items():
        relative_name(name)
        if Path(name).name!=name or Path(name).suffix.lower()not in ('.dx','.dxt') or not isinstance(digest,str)or not re.fullmatch('[0-9a-f]{64}',digest):
            raise ValueError('Invalid immutable source baseline resource pin')
    if {p.name for p in root.iterdir()}!=set(pins):raise ValueError('Immutable source baseline file set changed')
    total=0
    for name,digest in pins.items():
        data=read_bounded(root/name,MAX_OUTPUT_BYTES);total+=len(data)
        if total>MAX_OUTPUT_BYTES or sha(data)!=digest:raise ValueError('Immutable source baseline changed: '+name)


def verify_source(record):
    if not isinstance(record, dict):
        raise ValueError('Universal source provenance must be an object')
    for name in ('scene_sha256', 'manifest_sha256', 'conversion_report_sha256'):
        if not isinstance(record.get(name), str) or not re.fullmatch('[0-9a-f]{64}', record[name]):
            raise ValueError('Universal source provenance hash required: ' + name)
    for name in ('scene_path', 'conversion_report'):
        if not isinstance(record.get(name), str) or not Path(record[name]).is_absolute():
            raise ValueError('Universal source provenance requires an absolute path: ' + name)
    path = Path(record['scene_path'])
    if sha(read_bounded(path, MAX_JSON_BYTES)) != record['scene_sha256']:
        raise ValueError('Immutable Universal source scene changed')
    if sha(read_bounded(path.parent / 'manifest.json', 2 * 1024 * 1024)) != record['manifest_sha256']:
        raise ValueError('Immutable Universal source manifest changed')
    if sha(read_bounded(Path(record['conversion_report']), MAX_JSON_BYTES)) != record['conversion_report_sha256']:
        raise ValueError('Universal source conversion report changed')
    return load_scene(path)


def inspect_source(record):
    scene = verify_source(record)
    return {'provenance': record, 'identity': scene.get('metadata', {}),
            'source': {key: value for key, value in scene['source'].items() if key != 'catalog_original'},
            'coordinates': scene['coordinate_system'], 'measurements': scene.get('measurements', {}),
            'selection': scene.get('selection', {}), 'unknown_semantics': scene['unknown_semantics'],
            'boundary': 'Immutable original scene and neutral source evidence. MR materials, donor systems and gameplay qualification are separate.'}
