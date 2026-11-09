"""Configurable registry storage and class maps, independent of qualification.

This ABI describes physical IDs, never race participant slots or model skins.
No profile grants runtime qualification merely by fitting in an allocation.
"""
from __future__ import annotations
import copy
import hashlib
import json

SDK33 = {
    'T1': list(range(7)) + [26],
    'T2': [7, 8, 30, 9, 10, 11, 12, 31, 13, 27, 28, 29],
    'T3': [14, 32, 15, 16, 17, 18, 19, 20, 21, 22, 23, 24, 25],
}
SCHEMA = 'mr-capacity-profile/1'


def integer(value, label, minimum=0, maximum=0x7fffffff):
    if type(value) is not int or not minimum <= value <= maximum:
        raise ValueError(label + ' must be a bounded integer')
    return value


def layout(count):
    integer(count, 'record_count', 33)
    base = 4 + count * 52
    size = base + 39 * 44
    if size > 0x7fffffff:
        raise ValueError('Registry layout exceeds signed x86 displacement arithmetic')
    return {'record_count': count, 'record_stride': 52, 'header_size': 4,
            'racetest_base': base, 'racetest_count': 39, 'racetest_stride': 44,
            'allocation_size': size}


def validate_profile(doc):
    if not isinstance(doc, dict) or doc.get('schema') != SCHEMA:
        raise ValueError('Unsupported capacity profile schema')
    count = integer(doc.get('record_count'), 'record_count', 33)
    storage = layout(count)
    classes = doc.get('classes')
    if not isinstance(classes, dict) or not all(c in classes for c in SDK33):
        raise ValueError('Classes must include T1, T2 and T3')
    # New classes can be described and costed, but the native emitter refuses
    # them until separate frontend/campaign/save owners are implemented.
    for c in classes:
        if not isinstance(c, str) or not c.startswith('T') or not c[1:].isdigit() or int(c[1:]) < 1 or c != 'T'+str(int(c[1:])):
            raise ValueError('Invalid class name')
    flat = []
    for c, ids in classes.items():
        if not isinstance(ids, list) or not ids:
            raise ValueError('Each class requires an explicit nonempty ID list')
        for i in ids: integer(i, 'physical_id', 0, count - 1)
        if c in SDK33 and [i for i in ids if i<33] != SDK33[c]:
            raise ValueError('SDK33 ID/class/relative selection order must remain unchanged')
        flat.extend(ids)
    if len(flat) != count or len(set(flat)) != count:
        raise ValueError('Every physical record must occur exactly once')
    budget = integer(doc.get('memory_budget_bytes', 8*1024*1024), 'memory_budget_bytes', 65536)
    # Tool resource budget, NOT an inferred engine maximum.
    table_bytes = count * 12 + len(classes) * 8
    if storage['allocation_size'] + table_bytes > budget:
        raise ValueError('Configured tool memory budget is too small for registry and maps')
    configuration = {'schema': SCHEMA, 'record_count': count,
                     'classes': {c:copy.deepcopy(classes[c]) for c in sorted(classes,key=lambda c:int(c[1:]))}, 'memory_budget_bytes': budget}
    result = copy.deepcopy(configuration)
    result.update(layout=storage, table_bytes=table_bytes, memory_budget_bytes=budget,
                  runtime_installable=False, runtime_qualified=False)
    result['profile_sha256'] = hashlib.sha256(json.dumps(configuration, sort_keys=True, separators=(',', ':')).encode()).hexdigest()
    return result


def scenario(count, distribution):
    """Create an explicit engineering experiment, not a qualified capability."""
    integer(count, 'record_count', 33)
    if layout(count)['allocation_size']+count*12+24>8*1024*1024:
        raise ValueError('Scenario exceeds default tool memory budget; author an explicit budgeted profile')
    if len(distribution) != 3 or any(type(n) is not int for n in distribution) or sum(distribution) != count:
        raise ValueError('Distribution must contain three counts summing to record_count')
    classes = copy.deepcopy(SDK33);next_id = 33
    for c, target in zip(SDK33, distribution):
        if target < len(classes[c]): raise ValueError('Cannot shrink SDK33 classes')
        extra = target - len(classes[c]);classes[c].extend(range(next_id, next_id+extra));next_id += extra
    return validate_profile({'schema': SCHEMA, 'record_count': count, 'classes': classes})


def save_compatibility(old, new):
    """Return mapping evidence; never modify a save or migrate a competition."""
    a, b = validate_profile(old), validate_profile(new)
    old_owner = {i: c for c, ids in a['classes'].items() for i in ids}
    new_owner = {i: c for c, ids in b['classes'].items() for i in ids}
    removed = sorted(set(old_owner)-set(new_owner))
    changed = sorted(i for i in old_owner if i in new_owner and old_owner[i] != new_owner[i])
    return {'physical_ids_preserved': not removed and not changed,
            'removed_ids': removed, 'changed_classes': changed,
            'active_championship_migration_qualified': False,
            'resource_identity_check_required': True,
            'save_bytes_modified': False}
