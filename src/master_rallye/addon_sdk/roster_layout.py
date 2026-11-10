"""Selection order is a permutation of physical records, never a renumbering.

Reservation locals describe append ownership. Selection locals are derived and
must not be written back into reservation locks or championship participant IDs.
"""
CLASSES = ('T1', 'T2', 'T3')
# T4 is an optional frontend class (CLASS-T4, docs/sdk/NEW_CLASS_RESEARCH.md):
# its own Vehicle Select tab, while each record keeps the qualified T3 race class.
FRONTEND_CLASSES = CLASSES + ('T4',)
BASE = {'T1': list(range(7)) + [26], 'T2': list(range(7, 14)) + [27],
        'T3': list(range(14, 26))}


def active_classes(rows, order=None):
    used = any(r['vehicle_class'] == 'T4' for r in rows) or (isinstance(order, dict) and 'T4' in order)
    return FRONTEND_CLASSES if used else CLASSES


def resolve_layout(rows, order=None):
    classes = active_classes(rows, order)
    canonical = {c: BASE.get(c, [])[:] for c in classes}
    for row in sorted(rows, key=lambda r: r['physical_id']):
        cls = row['vehicle_class']
        if cls not in classes or type(row['physical_id']) is not int:
            raise ValueError('Invalid physical roster identity/class')
        if row['class_local_index'] != len(canonical[cls]):
            raise ValueError('Reservation locals must remain canonical append indices')
        canonical[cls].append(row['physical_id'])
    flat = [i for c in classes for i in canonical[c]]
    if sorted(flat) != list(range(28 + len(rows))):
        raise ValueError('Physical roster must contain each contiguous ID exactly once')
    selected = canonical if order is None else order
    if not isinstance(selected, dict) or set(selected) != set(classes):
        raise ValueError('Selection order must declare exactly ' + ', '.join(classes))
    if 'T4' in classes and not selected['T4']:
        raise ValueError('An empty T4 class cannot be published')
    for cls in classes:
        ids = selected[cls]
        if (not isinstance(ids, list) or any(type(i) is not int for i in ids)
                or len(ids) != len(set(ids)) or sorted(ids) != sorted(canonical[cls])):
            raise ValueError('Selection order must be a complete class-preserving permutation: ' + cls)
        if len(ids) > 13:
            raise ValueError('Class capacity beyond thirteen is not qualified')
    return {'version': 1, 'canonical': canonical,
            'class_to_physical_ids': {c: selected[c][:] for c in classes},
            'physical_id_to_class_local': {str(i): {'vehicle_class': c, 'class_local_index': n}
                for c in classes for n, i in enumerate(selected[c])},
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
