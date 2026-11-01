"""Versioned setup authoring. No live solver writes or global texture swaps.

Preset validation is deliberately separate from native hook qualification.
An authored preset is not proof that the running game consumes it.
"""
from __future__ import annotations

import hashlib
import json
import math
import os
from pathlib import Path, PurePosixPath
import re
import tempfile
import xml.etree.ElementTree as ET

from .manifest import canonical_json

VERSION = 'vehicle-setup/1'
STATE_VERSION = 'vehicle-setup-selection/1'
MAX_JSON = 256 * 1024
MAX_RESOURCE = 32 * 1024 * 1024
TOKEN = re.compile(r'[A-Za-z][A-Za-z0-9_.-]{0,63}\Z')
HASH = re.compile(r'[0-9a-f]{64}\Z')
TYRE_FIELDS = frozenset(('CamberStiffness', 'CorneringCoeff',
    'CorneringCoeffGradient', 'IceRating', 'InflationStiffness',
    'InflationStiffnessDamping', 'LongitudinalStiffness', 'PeakMu',
    'PneumaticTrailCoeff', 'ScaleFactor', 'SoftRating', 'WetRating'))


def digest(data):
    return hashlib.sha256(data).hexdigest()


def resource_path(value):
    if not isinstance(value, str) or '\\' in value or ':' in value:
        raise ValueError('Setup resource must be a relative forward-slash path')
    path = PurePosixPath(value)
    if not value or path.is_absolute() or any(p in ('', '.', '..') for p in value.split('/')):
        raise ValueError('Setup resource escapes its package')
    if len(value) > 240:
        raise ValueError('Setup resource path budget')
    return value


def read_owned(root, relative, limit=MAX_RESOURCE):
    root = Path(root).absolute()
    for item in (root, *root.parents):
        if item.is_symlink() or getattr(item, 'is_junction', lambda: False)():
            raise ValueError('Linked setup package')
    root = root.resolve(strict=True)
    relative = resource_path(relative)
    path = root / relative
    cursor = root
    for part in PurePosixPath(relative).parts:
        cursor = cursor / part
        if cursor.is_symlink() or getattr(cursor, 'is_junction', lambda: False)():
            raise ValueError('Linked setup resource')
    if not path.resolve(strict=True).is_relative_to(root) or not path.is_file():
        raise ValueError('Setup resource outside package')
    if not 0 < path.stat().st_size <= limit:
        raise ValueError('Setup resource size budget')
    with path.open('rb') as stream:
        raw = stream.read(limit + 1)
    if not 0 < len(raw) <= limit:
        raise ValueError('Setup resource changed size')
    return raw


def _object_pairs(pairs):
    result = {}
    for k, v in pairs:
        if k in result:
            raise ValueError('Duplicate setup JSON key: ' + k)
        result[k] = v
    return result


def decode_json(raw):
    if not 0 < len(raw) <= MAX_JSON:
        raise ValueError('Setup JSON size budget')
    return json.loads(raw, object_pairs_hook=_object_pairs,
                      parse_constant=lambda v: (_ for _ in ()).throw(ValueError(v)))


def _token(value):
    if not isinstance(value, str) or not TOKEN.fullmatch(value):
        raise ValueError('Invalid stable setup identifier')


def _pin(value):
    if not isinstance(value, str) or not HASH.fullmatch(value):
        raise ValueError('Invalid setup source hash')


def _keys(value, expected):
    if not isinstance(value, dict) or set(value) != set(expected):
        raise ValueError('Invalid setup object fields: ' + str(expected))


def tyre_table(raw, prefix):
    """All five original indexed records, unmodified; indices are not grades."""
    _token(prefix)
    if not 0 < len(raw) <= 8 * 1024 * 1024 or b'<!' in raw:
        raise ValueError('Unsupported tyre XML')
    stem = 'Vehicles/Tyres/' + prefix
    values = {}
    for node in ET.fromstring(raw).iter('Value'):
        name = node.get('Name', '')
        if not name.startswith(stem):
            continue
        suffix = name[len(stem):]
        match = re.fullmatch(r'([0-4])/([A-Za-z]+)', suffix)
        if match is None:
            # Other prefixes such as gravelCustom are distinct families.
            if suffix and suffix[0].isdigit():
                raise ValueError('Unsupported tyre record: ' + name)
            continue
        if match[2] not in TYRE_FIELDS or suffix in values or node.get('Type') != 'Float':
            raise ValueError('Invalid/duplicate tyre coefficient')
        text = node.get('Value', '')
        number = float(text)
        if not math.isfinite(number):
            raise ValueError('Nonfinite tyre coefficient')
        values[suffix] = text
    if set(values) != {f'{i}/{k}' for i in range(5) for k in TYRE_FIELDS}:
        raise ValueError('Incomplete original tyre table: ' + prefix)
    return {'source_sha256': digest(raw), 'prefix': prefix,
            'fields': dict(sorted(values.items())),
            'table_sha256': digest(canonical_json(dict(sorted(values.items()))))}


def validate(manifest, *, root=None):
    _keys(manifest, ('schema', 'vehicle', 'defaults', 'liveries', 'tyres', 'scope'))
    if manifest['schema'] != VERSION:
        raise ValueError('Unsupported setup schema')
    vehicle = manifest['vehicle']
    _keys(vehicle, ('id', 'car_id', 'geometry_sha256'))
    _token(vehicle['id']); _pin(vehicle['geometry_sha256'])
    if type(vehicle['car_id']) is not int or not 0 <= vehicle['car_id'] <= 255:
        raise ValueError('Invalid physical CarID')
    if manifest['scope'] != {'mode': 'quick_race', 'participant': 'human_player_1',
                              'application': 'before_vehicle_creation'}:
        raise ValueError('Setup pilot does not authorize AI, split screen or live changes')
    _keys(manifest['defaults'], ('livery', 'tyre'))
    for kind, plural in (('livery', 'liveries'), ('tyre', 'tyres')):
        rows = manifest[plural]
        if not isinstance(rows, list) or not 1 <= len(rows) <= 16:
            raise ValueError('Setup preset count budget')
        ids = set()
        for row in rows:
            expected = ('id', 'label', 'source', 'geometry_sha256', 'textures',
                        'carsheet', 'smallcarsheet') if kind == 'livery' else (
                        'id', 'label', 'source', 'front', 'rear')
            _keys(row, expected)
            _token(row['id'])
            if row['id'] in ids:
                raise ValueError('Duplicate preset identity')
            ids.add(row['id'])
            if not isinstance(row['label'], str) or not 1 <= len(row['label']) <= 80:
                raise ValueError('Invalid preset label')
            _keys(row['source'], ('classification', 'version', 'sha256'))
            if row['source']['classification'] not in ('ORIGINAL', 'RECONSTRUCTED', 'USER'):
                raise ValueError('Unknown livery/tyre provenance')
            if not isinstance(row['source']['version'], str) or not 1 <= len(row['source']['version']) <= 128:
                raise ValueError('Missing source version')
            _pin(row['source']['sha256'])
            if kind == 'livery':
                if row['geometry_sha256'] != vehicle['geometry_sha256']:
                    raise ValueError('Livery geometry/UV/material bindings are incompatible')
                if not isinstance(row['textures'], list) or len(row['textures']) > 64:
                    raise ValueError('Livery texture budget')
                owned = set()
                for binding in row['textures']:
                    _keys(binding, ('material', 'slot', 'path', 'sha256', 'alpha_sha256'))
                    _token(binding['material'])
                    if type(binding['slot']) is not int or not 0 <= binding['slot'] <= 3:
                        raise ValueError('Unsupported texture stage')
                    key = binding['material'], binding['slot']
                    if key in owned:
                        raise ValueError('Duplicate material/stage binding')
                    owned.add(key)
                    resource_path(binding['path']); _pin(binding['sha256']); _pin(binding['alpha_sha256'])
                    if root is not None:
                        from ..dxt import parse_dxt_bytes
                        raw = read_owned(root, binding['path'])
                        if digest(raw) != binding['sha256']:
                            raise ValueError('Livery resource hash mismatch')
                        texture = parse_dxt_bytes(raw)
                        if digest(texture.bgra[3::4]) != binding['alpha_sha256']:
                            raise ValueError('Livery alpha evidence mismatch')
                # These are independent optional assets, never copied between roles.
                for role in ('carsheet', 'smallcarsheet'):
                    art = row[role]
                    if art is not None:
                        _keys(art, ('path', 'sha256', 'classification'))
                        resource_path(art['path']); _pin(art['sha256'])
                        if art['classification'] not in ('ORIGINAL', 'RECONSTRUCTED', 'USER'):
                            raise ValueError('Invalid artwork provenance')
                        if root is not None and digest(read_owned(root, art['path'])) != art['sha256']:
                            raise ValueError('Artwork hash mismatch')
            else:
                for axle in ('front', 'rear'):
                    table = row[axle]
                    if isinstance(table,dict) and table.get('kind')=='NATIVE_PASSTHROUGH':
                        _keys(table,('kind','prefix','source_sha256','evidence_key'))
                        _token(table['prefix']);_pin(table['source_sha256'])
                        if not isinstance(table['evidence_key'],str) or not re.fullmatch(r'Vehicles/[A-Za-z][A-Za-z0-9_]*/Suspension/'+axle.title()+r'/TyreType',table['evidence_key']):
                            raise ValueError('Unqualified native Stock reference')
                        continue
                    _keys(table, ('source_sha256', 'prefix', 'fields', 'table_sha256'))
                    _pin(table['source_sha256']); _token(table['prefix']); _pin(table['table_sha256'])
                    fields = table['fields']
                    if not isinstance(fields, dict) or set(fields) != {f'{i}/{k}' for i in range(5) for k in TYRE_FIELDS}:
                        raise ValueError('Incomplete preset tyre table')
                    if any(not isinstance(v, str) or not math.isfinite(float(v)) for v in fields.values()):
                        raise ValueError('Invalid tyre coefficient text')
                    if digest(canonical_json(dict(sorted(fields.items())))) != table['table_sha256']:
                        raise ValueError('Tyre table evidence mismatch')
        if manifest['defaults'][kind] not in ids:
            raise ValueError('Missing default preset')
        if kind=='livery':
            owners=[{(b['material'],b['slot']) for b in row['textures']} for row in rows]
            if any(value!=owners[0] for value in owners[1:]):
                raise ValueError('Livery silently omits a material/secondary texture stage')
    return manifest


def selection(manifest, *, livery=None, tyre=None):
    validate(manifest)
    chosen = {'livery': livery or manifest['defaults']['livery'],
              'tyre': tyre or manifest['defaults']['tyre']}
    for key, rows in (('livery', 'liveries'), ('tyre', 'tyres')):
        if chosen[key] not in {r['id'] for r in manifest[rows]}:
            raise ValueError('Removed/unknown ' + key + ' preset; explicit reset required')
    return {'schema': STATE_VERSION, 'vehicle': manifest['vehicle'],
            'manifest_sha256': digest(canonical_json(manifest)), **chosen}


def validate_selection(manifest, state):
    _keys(state, ('schema', 'vehicle', 'manifest_sha256', 'livery', 'tyre'))
    if state['schema'] != STATE_VERSION or state['vehicle'] != manifest['vehicle']:
        raise ValueError('Selection vehicle/schema mismatch')
    expected = selection(manifest, livery=state['livery'], tyre=state['tyre'])
    if state != expected:
        raise ValueError('Preset manifest changed; explicit review/reset required')
    return state


def save_selection(directory, manifest, state):
    """Dedicated sidecar only, atomic replace; never writes PlayerState.xml."""
    validate_selection(manifest, state)
    directory = Path(directory)
    for path in (directory, *directory.parents):
        if path.is_symlink() or getattr(path, 'is_junction', lambda: False)():
            raise ValueError('Linked setup state directory')
    directory.mkdir(parents=True, exist_ok=True)
    target = directory / (manifest['vehicle']['id'] + '.setup.json')
    if target.is_symlink() or getattr(target, 'is_junction', lambda: False)() or target.exists() and not target.is_file():
        raise ValueError('Unsafe selection state destination')
    raw = canonical_json(state)
    fd, name = tempfile.mkstemp(prefix='.setup-', dir=directory)
    try:
        with os.fdopen(fd, 'wb') as stream:
            stream.write(raw); stream.flush(); os.fsync(stream.fileno())
        os.replace(name, target)
    finally:
        if os.path.exists(name):
            os.unlink(name)
    return target


def precreation_plan(manifest, state, *, mode, participant, car_id, initialized,
                     player_type, num_players, attract, replay):
    """Pure application boundary. This is a plan, not an installed native hook."""
    validate_selection(manifest, state)
    if any(type(v) is not int for v in (mode, participant, car_id, player_type, num_players)) or any(type(v) is not bool for v in (initialized,attract,replay)):
        raise ValueError('Untyped runtime participant state')
    if mode != 2 or participant != 0 or car_id != manifest['vehicle']['car_id'] or initialized or player_type!=1 or num_players!=1 or attract or replay:
        return None
    livery = next(r for r in manifest['liveries'] if r['id'] == state['livery'])
    tyre = next(r for r in manifest['tyres'] if r['id'] == state['tyre'])
    return {'vehicle': dict(manifest['vehicle']), 'participant': 0,
            'livery': livery, 'tyre': tyre,
            'writes_shared_family': False, 'native_application': 'NOT_QUALIFIED'}


def verify_tyre_sources(manifest, original_xml):
    """Compare declarations to original bytes, never trust self-labelled originals."""
    validate(manifest)
    if not 0<len(original_xml)<=8*1024*1024 or b'<!' in original_xml:
        raise ValueError('Unsupported original tire XML')
    for row in manifest['tyres']:
        if row['source']['classification'] != 'ORIGINAL' or row['source']['sha256'] != digest(original_xml):
            raise ValueError('Pilot requires source-backed complete original tyre tables')
        for axle in ('front', 'rear'):
            table = row[axle]
            if table.get('kind')=='NATIVE_PASSTHROUGH':
                values=[n for n in ET.fromstring(original_xml).iter('Value') if n.get('Name')==table['evidence_key']]
                if table['source_sha256']!=digest(original_xml) or len(values)!=1 or values[0].get('Type')!='String' or values[0].get('Value')!=table['prefix']:
                    raise ValueError('Native Stock reference differs from original source')
                continue
            if table != tyre_table(original_xml, table['prefix']):
                raise ValueError('Tyre preset differs from original coherent table')
    return True


class SetupDraft:
    """Input-independent menu transaction: Cancel never persists pending edits."""
    def __init__(self, manifest, current=None):
        self.manifest = decode_json(canonical_json(validate(manifest)))
        self.current = validate_selection(self.manifest, current) if current else selection(self.manifest)
        self.pending = dict(self.current)

    def cycle(self, field, delta):
        if field not in ('livery', 'tyre') or type(delta) is not int or delta not in (-1, 1):
            raise ValueError('Invalid setup navigation')
        rows = self.manifest['liveries' if field == 'livery' else 'tyres']
        ids = [row['id'] for row in rows]
        self.pending[field] = ids[(ids.index(self.pending[field]) + delta) % len(ids)]

    def restore_defaults(self):
        self.pending = selection(self.manifest)

    def cancel(self):
        self.pending = dict(self.current)

    def confirm(self, state_directory):
        validate_selection(self.manifest, self.pending)
        save_selection(state_directory, self.manifest, self.pending)
        self.current = dict(self.pending)
        return dict(self.current)
