"""Selection order is a permutation of physical records, never a renumbering.

Reservation locals describe append ownership. Selection locals are derived and
must not be written back into reservation locks or championship participant IDs.
"""
CLASSES = ('T1', 'T2', 'T3')
BASE = {'T1': list(range(7)) + [26], 'T2': list(range(7, 14)) + [27],
        'T3': list(range(14, 26))}


def resolve_layout(rows, order=None):
    canonical = {c: ids[:] for c, ids in BASE.items()}
    for row in sorted(rows, key=lambda r: r['physical_id']):
        cls = row['vehicle_class']
        if cls not in CLASSES or type(row['physical_id']) is not int:
            raise ValueError('Invalid physical roster identity/class')
        if row['class_local_index'] != len(canonical[cls]):
            raise ValueError('Reservation locals must remain canonical append indices')
        canonical[cls].append(row['physical_id'])
    flat = [i for c in CLASSES for i in canonical[c]]
    if sorted(flat) != list(range(28 + len(rows))):
        raise ValueError('Physical roster must contain each contiguous ID exactly once')
    selected = canonical if order is None else order
    if not isinstance(selected, dict) or set(selected) != set(CLASSES):
        raise ValueError('Selection order must declare exactly T1, T2 and T3')
    for cls in CLASSES:
        ids = selected[cls]
        if (not isinstance(ids, list) or any(type(i) is not int for i in ids)
                or len(ids) != len(set(ids)) or sorted(ids) != sorted(canonical[cls])):
            raise ValueError('Selection order must be a complete class-preserving permutation: ' + cls)
        if len(ids) > 13:
            raise ValueError('Class capacity beyond thirteen is not qualified')
    return {'version': 1, 'canonical': canonical,
            'class_to_physical_ids': {c: selected[c][:] for c in CLASSES},
            'physical_id_to_class_local': {str(i): {'vehicle_class': c, 'class_local_index': n}
                for c in CLASSES for n, i in enumerate(selected[c])},
            'reservation_policy': 'addon.class_local_index and locks remain append ownership; selection locals are this explicit permutation',
            'save_policy': 'physical IDs unchanged; new/disposable competitions only until owner validation'}


def validate_trial_save(raw):
    """No implicit migration of an in-progress championship to a trial layout."""
    import xml.etree.ElementTree as ET
    if not isinstance(raw,bytes) or len(raw)>4*1024*1024 or b'<!' in raw:
        raise ValueError('Invalid trial player-state input')
    tree=ET.fromstring(raw)
    active=[n.get('Name') for n in tree.iter('Value')
            if 'gamesaved' in n.get('Name','').casefold()
            and n.get('Value','').casefold() not in ('false','0','')]
    if active:raise ValueError('Active championship migration is not qualified: '+', '.join(active))
    return {'status':'PASS_NO_ACTIVE_CHAMPIONSHIP','original_bytes_preserved':True,
            'boundary':'Disposable candidate state; no general save migration claim'}
