"""Stable roster reservations and append-only resource/UI composition.

Allocation is a planning operation. It never upgrades an experimental native
layout to runtime-qualified. Removed IDs remain reserved for saved selections.
"""
from __future__ import annotations

import copy
import hashlib
import re
import struct
from pathlib import PurePosixPath

from .manifest import AddonValidationError, validate_manifests, _validate_one
from .ui_assets import append_frame, parse_bank, BANKS
from ..dxt import parse_dxt_bytes

STOCK_COUNTS = {'T1': 7, 'T2': 7, 'T3': 12}


def reserve_roster(requests, *, slots, previous=None):
    """Assign explicit audited slots, preserving tombstones and prior identity.

    `slots` is supplied by the selected native profile, not a claimed engine
    maximum. Requests contain addon_id, vehicle_class, optional physical_id.
    """
    by_id, by_local = {}, set()
    for row in slots:
        if (not isinstance(row,dict) or set(row) != {'physical_id', 'vehicle_class', 'class_local_index'}
                or type(row['physical_id']) is not int or row['physical_id'] < 26
                or row['vehicle_class'] not in STOCK_COUNTS
                or type(row['class_local_index']) is not int
                or row['class_local_index'] < STOCK_COUNTS[row['vehicle_class']]):
            raise AddonValidationError('invalid profile slot')
        key = (row['vehicle_class'], row['class_local_index'])
        if row['physical_id'] in by_id or key in by_local:
            raise AddonValidationError('profile has colliding ID/class slots')
        by_id[row['physical_id']] = dict(row); by_local.add(key)
    old = {'version': 1, 'reservations': []} if previous is None else previous
    if (not isinstance(old,dict) or set(old) != {'version', 'reservations'}
            or type(old['version']) is not int or old['version'] != 1
            or not isinstance(old['reservations'],list)):
        raise AddonValidationError('unsupported roster reservation file')
    owned, used = {}, set()
    for row in old['reservations']:
        if (not isinstance(row, dict) or set(row) != {'addon_id', 'physical_id', 'vehicle_class', 'class_local_index'}
                or not re.fullmatch(r'[a-z0-9][a-z0-9._-]{1,63}', str(row['addon_id']))):
            raise AddonValidationError('invalid prior reservation')
        slot = by_id.get(row['physical_id'])
        if (slot != {k: row[k] for k in slot or {}} or slot is None
                or row['addon_id'] in owned or row['physical_id'] in used):
            raise AddonValidationError('prior reservation conflicts with native profile')
        owned[row['addon_id']] = dict(row); used.add(row['physical_id'])
    names = set()
    for row in requests:
        if (not isinstance(row, dict) or not {'addon_id','vehicle_class'} <= set(row)
                or set(row) - {'addon_id','vehicle_class','physical_id'}
                or not re.fullmatch(r'[a-z0-9][a-z0-9._-]{1,63}', str(row['addon_id']))
                or row['vehicle_class'] not in STOCK_COUNTS or row['addon_id'] in names):
            raise AddonValidationError('invalid or duplicate addon reservation request')
        names.add(row['addon_id'])
    # Explicit reservations precede auto requests, so input order is irrelevant.
    order = sorted(requests, key=lambda r: (r.get('physical_id') is None, r['addon_id']))
    for row in order:
        name = row['addon_id']; explicit = row.get('physical_id')
        if explicit is not None and type(explicit) is not int:
            raise AddonValidationError('physical_id must be an integer')
        if name in owned:
            if (owned[name]['vehicle_class'] != row['vehicle_class']
                    or explicit is not None and explicit != owned[name]['physical_id']):
                raise AddonValidationError('cannot change a reserved addon identity')
            continue
        options = sorted((s for s in slots if s['vehicle_class'] == row['vehicle_class']
                          and s['physical_id'] not in used),
                         key=lambda s: (s['class_local_index'], s['physical_id']))
        slot = next((s for s in options if explicit is None or s['physical_id'] == explicit), None)
        if slot is None:
            raise AddonValidationError('profile capacity exhausted or requested ID conflicts')
        owned[name] = {'addon_id': name, **slot}; used.add(slot['physical_id'])
    active = [owned[name] for name in names]
    for cls, stock in STOCK_COUNTS.items():
        indices = sorted(r['class_local_index'] for r in active if r['vehicle_class'] == cls)
        if indices != list(range(stock, stock + len(indices))):
            raise AddonValidationError('active class roster has a hole; do not silently reassign saved IDs')
    lock = {'version': 1, 'reservations': sorted(owned.values(), key=lambda r: r['physical_id'])}
    return lock, sorted(active, key=lambda r: r['physical_id'])


def plan_collection(manifests, capabilities, previous=None):
    """Use persistent reservations with the shared SDK manifest validator."""
    # Validate authorship first, then resolve with persistent ownership. A
    # temporary alphabetical auto assignment must not override saved IDs.
    if not manifests:
        raise AddonValidationError('at least one addon manifest is required')
    for manifest in manifests:
        _validate_one(manifest)
    requests=[{'addon_id':m['addon_id'],'vehicle_class':m['vehicle_class'],
               **({'physical_id':m['physical_id']['value']} if m['physical_id']['policy']=='explicit' else {})}
              for m in manifests]
    lock,active=reserve_roster(requests,slots=capabilities['qualified_addon_slots'],previous=previous)
    assigned={r['addon_id']:r['physical_id'] for r in active};resolved=copy.deepcopy(manifests)
    for m in resolved:m['physical_id']={'policy':'explicit','value':assigned[m['addon_id']]}
    return validate_manifests(resolved,capabilities),lock


def compose_ui_bank(base, role, contributions):
    """Rebase independently built one-frame banks without altering any base frame.

    Contributions are (addon_id, source_bank_bytes, source_texture_bytes).
    Existing base frames (including other addons) retain their frame IDs/bytes.
    Assignment order must come from the roster reservation order.
    """
    if role not in BANKS:
        raise AddonValidationError('unknown UI bank role')
    prefix, stock_count, template, size = BANKS[role]
    before = parse_bank(base)
    if before['count'] < stock_count:
        raise AddonValidationError('base UI bank is smaller than the stock profile')
    result = base; textures = {}; assigned = {}; names = set()
    for name, source_bank, source_texture in contributions:
        if name in names:
            raise AddonValidationError('duplicate UI contributor')
        names.add(name); source = parse_bank(source_bank)
        if (source['count'] != stock_count + 1
                or source['records'][:stock_count] != before['records'][:stock_count]):
            raise AddonValidationError('UI contributor does not extend the identical stock bank')
        # Require the admitted native placement/scalars; only texture names vary.
        expected, source_name = append_frame(_stock_bank(before, stock_count), template)
        if source_bank != expected:
            raise AddonValidationError('UI contributor has an unsupported native sprite layout')
        try:
            tex = parse_dxt_bytes(source_texture)
        except Exception as exc:
            raise AddonValidationError('invalid UI texture') from exc
        import zlib
        if (tex.width, tex.height) != size or tex.word_0x08 != zlib.crc32(tex.bgra) & 0xffffffff:
            raise AddonValidationError('UI texture dimensions/CRC mismatch')
        frame = parse_bank(result)['count']
        result, target_name = append_frame(result, template)
        path = prefix.rsplit('/', 1)[0] + '/' + target_name + '.dxt'
        textures[path] = source_texture; assigned[name] = frame
    after = parse_bank(result)
    if after['records'][:before['count']] != before['records']:
        raise AddonValidationError('existing UI frames changed during composition')
    return result, textures, assigned


def _stock_bank(bank, count):
    return (struct.pack('<3I', 0xf001, 125, count)
            + b''.join(struct.pack('<2I', i, i) for i in range(count))
            + struct.pack('<I', count) + b''.join(bank['records'][:count]))


def merge_resources(contributions):
    """Case-insensitive ownership and path safety; identical shared bytes allowed.

    No overwrite semantics: a composed bank/XML must be generated separately.
    """
    assets = {}; owners = {}
    for owner, rows in contributions:
        for raw, data in rows.items():
            if (not isinstance(raw, str) or '\\' in raw or ':' in raw or '\x00' in raw
                    or any(p in ('', '.', '..') for p in raw.split('/'))
                    or PurePosixPath(raw).is_absolute() or not isinstance(data, bytes)):
                raise AddonValidationError('unsafe collection resource')
            key = raw.casefold()
            if key in owners:
                old_path, old_owner = owners[key]
                if assets[old_path] != data:
                    raise AddonValidationError(f'resource conflict: {old_owner}, {owner}: {raw}')
            else:
                owners[key] = (raw, owner); assets[raw] = data
    manifest = [{'path': p, 'size': len(d), 'sha256': hashlib.sha256(d).hexdigest(),
                 'owner': owners[p.casefold()][1]} for p, d in sorted(assets.items(), key=lambda r:r[0].casefold())]
    return assets, manifest
