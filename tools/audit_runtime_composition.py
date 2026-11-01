"""Read-only comparison of J.2 and Randomizer F3 patch ownership.

This is a planning gate, not a runtime compatibility certificate or installer.
"""
import argparse
import hashlib
import json
from pathlib import Path
try:
    import addon_runtime
except ImportError:
    from tools import addon_runtime

RETAIL = 'bf8aef32407eb6552c05045b8abef149f32983cedd9503b865069b444c5f96b4'


def digest(data):
    return hashlib.sha256(data).hexdigest()


def checked_range(row, name, before, after):
    start = row.get('rva')
    if type(start) is not int or start < 0:
        raise ValueError(f'{name}: invalid RVA')
    try:
        old, new = bytes.fromhex(row[before]), bytes.fromhex(row[after])
    except (KeyError, TypeError, ValueError) as error:
        raise ValueError(f'{name}: invalid patch bytes') from error
    if not old or len(old) != len(new) or start + len(old) > 0x100000000:
        raise ValueError(f'{name}: invalid patch length')
    return start, start + len(old), old, new


def file_offset_for_rva(sections, rva, length):
    matches = [section['raw_offset'] + rva - section['rva'] for section in sections
               if section['rva'] <= rva and rva + length <= section['rva'] + section['raw_size']]
    if len(matches) != 1:
        raise ValueError('RVA has no unique file-backed section')
    return matches[0]


def audit(retail, j2, randomizer):
    if j2.get('source', {}).get('sha256') != RETAIL or randomizer.get('source_executable', {}).get('sha256') != RETAIL:
        raise ValueError('plan source identity mismatch')
    pe, sections = addon_runtime._pe_sections(retail)
    if pe['machine'] != 0x14c or pe['image_base'] != 0x400000:
        raise ValueError('unexpected PE image layout')
    left, right, file_only = [], [], 0
    for row in j2['operations']:
        if row.get('rva') is None:
            file_only += 1
            continue
        start, end, old, new = checked_range(row, row['name'], 'expected_original_bytes', 'replacement_bytes')
        offset = file_offset_for_rva(sections, start, len(old))
        if retail[offset:offset + len(old)] != old:
            raise ValueError('J.2 preimage mismatch: ' + row['name'])
        left.append((start, end, row['name'], old, new))
    for row in randomizer['operations']:
        start, end, old, new = checked_range(row, row['id'], 'expected_original_hex', 'replacement_hex')
        offset = file_offset_for_rva(sections, start, len(old))
        if retail[offset:offset + len(old)] != old:
            raise ValueError('Randomizer preimage mismatch: ' + row['id'])
        mask = row.get('feature_mask')
        if type(mask) is not int or mask < 0:
            raise ValueError('invalid Randomizer feature mask')
        right.append((start, end, row['id'], old, new, mask))
    if not left or not right:
        raise ValueError('both plans need process operations')
    overlaps = []
    for a in left:
        for b in right:
            lo, hi = max(a[0], b[0]), min(a[1], b[1])
            if lo < hi:
                overlaps.append({'j2': a[2], 'randomizer': b[2], 'feature_mask': b[5],
                                 'rva_start': lo, 'rva_end_exclusive': hi,
                                 'retail_hex': a[3][lo-a[0]:hi-a[0]].hex(),
                                 'j2_hex': a[4][lo-a[0]:hi-a[0]].hex(),
                                 'randomizer_hex': b[4][lo-b[0]:hi-b[0]].hex()})
    return {'schema': 'runtime-composition-audit/1', 'plan_reference_sha256': RETAIL,
            'examined_executable_sha256': digest(retail),
            'j2_process_operations': len(left), 'j2_file_only_operations': file_only,
            'randomizer_operations': len(right), 'overlaps': overlaps,
            'status': 'CONFLICT' if overlaps else 'NO_OVERLAP_OBSERVED',
            'boundary': 'All declared operations compared; feature selection, instruction relocation, startup timing, resource resolution and runtime coexistence require separate qualification.'}


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('--retail', type=Path, required=True)
    p.add_argument('--j2', type=Path, required=True)
    p.add_argument('--randomizer', type=Path, required=True)
    args = p.parse_args()
    result = audit(args.retail.read_bytes(), json.loads(args.j2.read_text(encoding='utf-8')),
                   json.loads(args.randomizer.read_text(encoding='utf-8')))
    print(json.dumps(result, indent=2))


if __name__ == '__main__':
    main()
