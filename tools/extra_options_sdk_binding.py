"""Validate the SDK/F3 challenge binding without mutating either runtime.

The SDK relocates two record fields; F3 replaces the containing instructions.
This module produces a deterministic, reviewable proposal only.  A caller must
independently validate the entire live SDK profile before it may install it.
"""
from __future__ import annotations

import hashlib
import json
import struct
from pathlib import Path

RETAIL_LOAD = bytes.fromhex('8bbc3874050000')
SDK_LOAD = bytes.fromhex('8bbc38e0060000')
EXPECTED_IDS = frozenset(('challenge-preview-identity', 'challenge-race-consume'))


def _bytes(row, key):
    try:
        result = bytes.fromhex(row[key])
    except (KeyError, TypeError, ValueError) as error:
        raise ValueError('invalid operation bytes') from error
    if not result or len(result) > 256:
        raise ValueError('operation length outside budget')
    return result


def _operations(plan, sdk):
    if not isinstance(plan, dict) or not isinstance(plan.get('operations'), list):
        raise ValueError('missing operations')
    if len(plan['operations']) > 4096:
        raise ValueError('operation count exceeds budget')
    rows = []
    for item in plan['operations']:
        rva = item.get('rva')
        if sdk and rva is None:
            continue  # SDK file-only PE-header reconstruction is not a process write.
        if type(rva) is not int or not 0 <= rva <= 0xffffffff:
            raise ValueError('invalid operation RVA')
        before = _bytes(item, 'expected_original_bytes' if sdk else 'expected_original_hex')
        after = _bytes(item, 'replacement_bytes' if sdk else 'replacement_hex')
        if len(before) != len(after) or rva + len(before) > 0x100000000:
            raise ValueError('invalid operation extent')
        rows.append((rva, before, after, item.get('name' if sdk else 'id'), item))
    return rows


def propose(sdk_plan, f3_plan, preview_stub, race_stub, *, identity_offset=0x6e0):
    """Create an isolated patch proposal; never relax the existing bootstrap.

    Exactly the two witnessed F3 consumers may overlap. Every other overlap,
    unexpected instruction, or partial profile is a hard failure. Profile bytes
    are to be checked again against the mapped process before installation.
    """
    sdk = _operations(sdk_plan, True)
    f3 = _operations(f3_plan, False)
    if not sdk or not f3:
        raise ValueError('empty operation profile')
    for group in (sdk, f3):
        ordered = sorted(group, key=lambda row: row[0])
        if any(left[0] + len(left[1]) > right[0] for left, right in zip(ordered, ordered[1:])):
            raise ValueError('overlapping operations within a profile')
    by_id = {row[3]: row for row in f3}
    if len(by_id) != len(f3) or not EXPECTED_IDS.issubset(by_id):
        raise ValueError('missing or duplicate F3 consumers')
    overlaps = []
    for a in sdk:
        for b in f3:
            lo, hi = max(a[0], b[0]), min(a[0] + len(a[1]), b[0] + len(b[1]))
            if lo < hi:
                overlaps.append((a, b, lo, hi))
    if {b[3] for _, b, _, _ in overlaps} != EXPECTED_IDS:
        raise ValueError('unexpected SDK/F3 overlap set')
    if type(identity_offset) is not int or not 0x570 <= identity_offset <= 0x7fffffff:
        raise ValueError('invalid explicit RaceTest human offset')
    mapped_load = RETAIL_LOAD[:3] + struct.pack('<I', identity_offset)
    stubs = {'challenge-preview-identity': preview_stub, 'challenge-race-consume': race_stub}
    result = []
    for identity in sorted(EXPECTED_IDS):
        group = [item for item in overlaps if item[1][3] == identity]
        b = group[0][1]
        if b[1] != RETAIL_LOAD:
            raise ValueError('unexpected overlapping instruction')
        observed = bytearray(RETAIL_LOAD)
        for a, _, lo, hi in group:
            if a[0] != lo or a[0]+len(a[1]) != hi or lo < b[0]+3 or hi > b[0]+7:
                raise ValueError('SDK operation extends outside the witnessed displacement')
            offset = lo-b[0]
            if a[1] != RETAIL_LOAD[offset:offset+len(a[1])]:
                raise ValueError('SDK displacement preimage differs')
            observed[offset:offset+len(a[2])] = a[2]
        if bytes(observed) != mapped_load:
            raise ValueError('SDK displacement differs from explicit capacity layout')
        stub = stubs[identity]
        if not isinstance(stub, bytes) or not stub.startswith(RETAIL_LOAD + bytes.fromhex('9c60')):
            raise ValueError('F3 replay stub does not begin with the witnessed instruction')
        updated = mapped_load + stub[len(mapped_load):]
        result.append({'id': identity, 'rva': b[0], 'sdk_name': ','.join(item[0][3] for item in group),
                       'expected_mapped_hex': mapped_load.hex(), 'replacement_hex': b[2].hex(),
                       'original_stub_sha256': hashlib.sha256(stub).hexdigest(),
                       'composed_stub_hex': updated.hex(),
                       'composed_stub_sha256': hashlib.sha256(updated).hexdigest()})
    checks = [{'rva': a[0], 'expected_hex': a[2].hex(), 'name': a[3]} for a in sdk]
    return {'schema': 'extra-options-sdk-binding/1', 'status': 'OFFLINE_PROPOSAL',
            'sdk_checks': checks, 'challenge': result,
            'requirements': ['verify every SDK operation against live mapped bytes',
                             'verify every selected F3 preimage',
                             'install and rollback atomically while other threads are quiescent'],
            'runtime_qualified': False}


def write_proposal(path, proposal):
    path = Path(path)
    if path.exists():
        raise ValueError('choose a fresh output')
    path.write_text(json.dumps(proposal, indent=2, sort_keys=True) + '\n', encoding='utf-8')


def render_header(proposal, f3_plan, extension, *, registry_count=0):
    if proposal.get('schema') != 'extra-options-sdk-binding/1' or proposal.get('runtime_qualified') is not False:
        raise ValueError('invalid binding proposal')
    if type(registry_count) is not int or registry_count < 0 or registry_count > 0x7fffffff:
        raise ValueError('invalid compiled registry count')
    checks = proposal['sdk_checks']
    challenges = proposal['challenge']
    symbols = f3_plan['code_symbols']
    if (not isinstance(extension, dict) or set(extension) != {'address', 'size', 'rw_offset', 'rw_size', 'code_sha256'} or
        any(type(extension[k]) is not int or extension[k] < 0 for k in ('address', 'size', 'rw_offset', 'rw_size')) or
        extension['size'] == 0 or extension['rw_offset'] + extension['rw_size'] > extension['size'] or
        len(extension['code_sha256']) != 64 or any(c not in '0123456789abcdef' for c in extension['code_sha256'])):
        raise ValueError('invalid SDK extension profile')
    names = {'challenge-preview-identity': 'challenge_preview', 'challenge-race-consume': 'challenge_consumer'}
    rows = '\n'.join('    {0x%Xu, "%s"},' % (x['rva'], x['expected_hex']) for x in checks)
    hooks = '\n'.join('    {"%s", 0x%Xu, 0x%Xu, "%s"},' %
                      (x['id'], x['rva'], symbols[names[x['id']]], x['expected_mapped_hex'])
                      for x in challenges)
    return ('#pragma once\n#include <cstddef>\n#include <cstdint>\n'
            'namespace sdk_binding_profile {\n'
            'inline constexpr std::uint32_t registry_count = %du;\n' % registry_count +
            'struct Check { std::uint32_t rva; const char* expected_hex; };\n'
            'struct Hook { const char* id; std::uint32_t rva; std::uint32_t stub_va; const char* mapped_hex; };\n'
            'inline constexpr Check checks[] = {\n' + rows + '\n};\n'
            'inline constexpr Hook hooks[] = {\n' + hooks + '\n};\n'
            'inline constexpr std::size_t check_count = sizeof(checks)/sizeof(checks[0]);\n'
            'inline constexpr std::size_t hook_count = sizeof(hooks)/sizeof(hooks[0]);\n'
            'inline constexpr std::uint32_t extension_va = 0x%Xu;\n' % extension['address'] +
            'inline constexpr std::size_t extension_size = %du, rw_offset = %du, rw_size = %du;\n' %
            (extension['size'], extension['rw_offset'], extension['rw_size']) +
            'inline constexpr char extension_code_sha256[] = "%s";\n}\n' % extension['code_sha256'])
