"""Portable, fail-closed PE32 and Broker-family compatibility audit."""
from __future__ import annotations
import hashlib
import json
import struct
from pathlib import Path

DATA_DIR = Path(__file__).resolve().parent / "data"
AUDIT_VERSION = "retail-broker-v1.2"
PROFILE_SCHEMA_VERSION = 3
PROFILE_CACHE_ROOT = Path(__file__).resolve().parent / "observatory-data" / "build-profiles"

def digest(data):
    return hashlib.sha256(data).hexdigest()


def pe_layout(data):
    """Bounded PE32 inspection; reports unknown images without granting trust."""
    if len(data) < 0x100 or data[:2] != b'MZ':
        raise ValueError('Missing DOS header')
    pe = struct.unpack_from('<I', data, 0x3c)[0]
    if pe > len(data)-24 or data[pe:pe+4] != b'PE\0\0':
        raise ValueError('Missing PE header')
    machine, count, timestamp = struct.unpack_from('<HHI', data, pe+4)
    optional_size = struct.unpack_from('<H', data, pe+20)[0]
    opt = pe+24
    if machine != 0x14c or not 1 <= count <= 96 or optional_size < 96 or opt+optional_size+count*40 > len(data):
        raise ValueError('Invalid x86 PE headers')
    if struct.unpack_from('<H', data, opt)[0] != 0x10b:
        raise ValueError('Expected PE32')
    sections = []
    for i in range(count):
        at = opt+optional_size+i*40
        name = data[at:at+8].split(b'\0',1)[0].decode('ascii')
        vs, rva, size, raw = struct.unpack_from('<IIII', data, at+8)
        flags = struct.unpack_from('<I', data, at+36)[0]
        if size and (raw > len(data) or size > len(data)-raw):
            raise ValueError('Section extends beyond file')
        sections.append(dict(name=name, virtual_size=vs, rva=rva, raw_size=size,
                             raw_offset=raw, characteristics=flags))
    return dict(machine=machine, timestamp=timestamp,
                pe_header_sha256=digest(data[pe:opt+optional_size+count*40]),
                image_base=struct.unpack_from('<I',data,opt+28)[0],
                size_of_image=struct.unpack_from('<I',data,opt+56)[0],
                entry_rva=struct.unpack_from('<I',data,opt+16)[0], sections=sections)


def window(data, pe, va, length):
    rva = va-pe['image_base']
    for section in pe['sections']:
        if section['rva'] <= rva and rva+length <= section['rva']+section['raw_size']:
            start = section['raw_offset']+rva-section['rva']
            return data[start:start+length], section['name'], start
        if section['rva'] <= rva and rva+length <= section['rva']+section['virtual_size']:
            # PE zero-filled tail, not a runtime pointer read. The corresponding
            # accessor/logger fingerprints establish the slot's native owner.
            delta=rva-section['rva']
            backed=max(0,min(length,section['raw_size']-delta))
            start=section['raw_offset']+delta
            return data[start:start+backed]+bytes(length-backed),section['name'],None
    raise ValueError('Anchor outside file-backed section')


def definitions():
    return json.loads((DATA_DIR/'broker-families.json').read_text(encoding='utf-8'))


def registry_definitions():
    return json.loads((DATA_DIR/'registry-profiles.json').read_text(encoding='utf-8'))


def _family_layout_matches(pe, reference):
    layout_match = all(pe[k] == reference[k] for k in ('machine', 'timestamp', 'image_base', 'size_of_image', 'entry_rva'))
    actual_sections = [dict(s, virtual_size=0) if s['name'] == '.text' else s for s in pe['sections']]
    expected_sections = [dict(s, virtual_size=0) if s['name'] == '.text' else s for s in reference['sections']]
    layout_match &= actual_sections == expected_sections
    text = next((s for s in pe['sections'] if s['name'] == '.text'), None)
    rdata = next((s for s in pe['sections'] if s['name'] == '.rdata'), None)
    layout_match &= bool(text and text['virtual_size'] <= text['raw_size']
                         and (rdata is None or text['rva'] + text['virtual_size'] <= rdata['rva']))
    return bool(layout_match)


def _semantic_trampoline_variant_matches(data, pe, anchor, variant):
    """Recognize only the audited two-hook NULL-safe native Dump wrapper.

    The candidate still has to match every unchanged byte of the stock walker.
    Each replacement must be a near JMP to a bounded x86 stub in executable,
    file-backed .text. The stubs are accepted only when their exact instruction
    shape checks the pointer before the original dereference/call and branches
    to the audited stock null and continuation paths.
    """
    try:
        walker, section, _ = window(data, pe, anchor["va"], anchor["length"])
        if section != anchor["section"]:
            return False

        hooks = variant["hooks"]
        coverage = bytearray(anchor["length"])
        for segment in variant["stable_segments"]:
            offset, length = segment["offset"], segment["length"]
            if (type(offset) is not int or type(length) is not int or offset < 0 or length <= 0
                    or offset + length > len(walker)):
                return False
            if any(coverage[offset:offset + length]):
                return False
            if digest(walker[offset:offset + length]) != segment["sha256"]:
                return False
            coverage[offset:offset + length] = b"\x01" * length

        stub_ranges = []
        for hook in hooks:
            offset = hook["offset"]
            original = bytes.fromhex(hook["original_hex"])
            if (type(offset) is not int or len(original) < 5 or offset < 0
                    or offset + len(original) > len(walker)
                    or any(coverage[offset:offset + len(original)])):
                return False
            coverage[offset:offset + len(original)] = b"\x01" * len(original)
            patch = walker[offset:offset + len(original)]
            if patch[0] != 0xE9 or patch[5:] != b"\x90" * (len(patch) - 5):
                return False

            hook_va = anchor["va"] + offset
            stub_va = hook_va + 5 + struct.unpack_from("<i", patch, 1)[0]
            stub_length = hook["stub_length"]
            anchor_end = anchor["va"] + anchor["length"]
            if type(stub_length) is not int or stub_length <= 0 or stub_va < anchor_end:
                return False
            stub, stub_section, file_offset = window(data, pe, stub_va, stub_length)
            section_info = next((item for item in pe["sections"] if item["name"] == stub_section), None)
            if (stub_section != ".text" or file_offset is None or section_info is None
                    or not (section_info["characteristics"] & 0x20000000)):
                return False

            prefix = bytes.fromhex(hook["stub_prefix_hex"])
            body = bytes.fromhex(hook["stub_body_hex"])
            if (len(prefix) < 4 or prefix[-2:] != b"\x0f\x84"
                    or stub[:len(prefix)] != prefix):
                return False
            branch_offset = len(prefix)
            null_target = stub_va + branch_offset + 4 + struct.unpack_from("<i", stub, branch_offset)[0]
            body_offset = branch_offset + 4
            if stub[body_offset:body_offset + len(body)] != body:
                return False
            jump_offset = body_offset + len(body)
            if (jump_offset + 5 != stub_length or stub[jump_offset] != 0xE9
                    or null_target != hook["null_target_va"]):
                return False
            resume_target = stub_va + stub_length + struct.unpack_from("<i", stub, jump_offset + 1)[0]
            if resume_target != hook["resume_target_va"]:
                return False
            stub_ranges.append((stub_va, stub_va + stub_length))

        if not hooks or not all(coverage):
            return False
        ordered = sorted(stub_ranges)
        return all(left[1] <= right[0] for left, right in zip(ordered, ordered[1:]))
    except (KeyError, TypeError, ValueError, struct.error):
        return False


def _registry_profile_for(data, pe, exact_profile):
    if exact_profile:
        return exact_profile.get('vehicle_registry_profile', 'unknown'), 'committed_exact'
    maps = registry_definitions()
    for profile, markers in maps.get('detection_fingerprints', {}).items():
        matches = True
        for marker in markers:
            try:
                raw, section, _ = window(data, pe, marker['va'], marker['length'])
                matches &= section == marker['section'] and digest(raw) == marker['sha256']
            except (KeyError, ValueError):
                matches = False
        if matches:
            return profile, 'structural_fingerprint'
    return 'unknown', 'unrecognized'


def _audit_fingerprint(audit):
    canonical = {
        'audit_version': AUDIT_VERSION,
        'family': audit.get('compatibility_family'),
        'layout_compatible': audit.get('layout_compatible'),
        'anchors': [(a['name'], a.get('sha256'), a.get('compatible')) for a in audit.get('anchors', [])],
        'capabilities': audit.get('capabilities', {}),
    }
    # Preserve the historical stock fingerprint, but bind a non-stock exact
    # anchor variant to its declared policy identity as well as its bytes.
    variants = [(a['name'], a['matched_variant']) for a in audit.get('anchors', [])
                if a.get('matched_variant') not in (None, 'stock')]
    if variants:
        canonical['approved_anchor_variants'] = variants
    raw = json.dumps(canonical, sort_keys=True, separators=(',', ':')).encode('utf-8')
    return digest(raw)


def _profile_document(audit, *, exact_profile=None, registry_profile=None, registry_origin=None):
    origin = 'committed_exact' if exact_profile else 'locally_audited'
    family = audit.get('compatibility_family')
    caps = dict(audit.get('capabilities', {}))
    hardened = bool(caps.get('hardened_dump'))
    profile_id = (exact_profile['profile'] if exact_profile else
                  ('local-hardened-' if hardened else 'local-audited-') + audit['sha256'][:12])
    if exact_profile:
        # Exact profiles carry separately reviewed frontend tool permissions.
        # Family Dump-route fingerprints do not prove the main-window 0x27
        # opener or Flow Builder's full open path.
        for capability in ('open_broker_editor', 'flow_builder'):
            if capability in exact_profile.get('capabilities', {}):
                caps[capability] = exact_profile['capabilities'][capability]
    reg = registry_profile if registry_profile is not None else audit.get('registry_profile', 'unknown')
    caps['vehicle_registry_profile'] = reg
    return {
        'schema_version': PROFILE_SCHEMA_VERSION,
        'sha256': audit['sha256'],
        'size': audit['size'],
        'profile_id': profile_id,
        'build_classification': 'exact' if exact_profile else 'hardened' if hardened else 'compatible',
        'profile_origin': origin,
        'compatibility_family': family,
        'audit_version': AUDIT_VERSION,
        'audit_fingerprint': _audit_fingerprint(audit),
        'vehicle_registry_profile': reg,
        'registry_profile_origin': registry_origin or ('committed_exact' if exact_profile else 'structural_fingerprint' if reg != 'unknown' else 'unrecognized'),
        'capabilities': caps,
        'pe_identity': {key: audit['pe'][key] for key in ('machine', 'image_base', 'size_of_image', 'entry_rva')},
    }


def _cache_path(root, image_hash):
    root = Path(root).resolve()
    if root.name != 'build-profiles':
        raise ValueError('Profile cache must use a build-profiles directory')
    return root / (image_hash + '.json')


def _load_valid_cache(path, audit):
    try:
        cached = json.loads(path.read_text(encoding='utf-8'))
        expected = _profile_document(audit, registry_profile=audit.get('registry_profile'),
                                     registry_origin=audit.get('registry_profile_origin'))
        return cached if cached == expected else None
    except (OSError, UnicodeError, json.JSONDecodeError, TypeError):
        return None


def _write_cache(path, profile):
    path.parent.mkdir(parents=True, exist_ok=True)
    temp = path.with_suffix('.json.tmp')
    temp.write_text(json.dumps(profile, indent=2) + '\n', encoding='utf-8')
    temp.replace(path)


def audit_build(data):
    pe = pe_layout(data)
    canonical = definitions()
    reference = canonical['retail_pe']
    layout_match = _family_layout_matches(pe, reference)
    anchors=[]
    for anchor in canonical['anchors']:
        try:
            raw, section, offset = window(data,pe,anchor['va'],anchor['length'])
            observed = digest(raw)
            matched_variant = 'stock' if observed == anchor['sha256'] else None
            if matched_variant is None:
                for variant in anchor.get('approved_variants', []):
                    if observed == variant.get('sha256'):
                        matched_variant = variant['id']
                        break
            if matched_variant is None:
                for variant in anchor.get('semantic_variants', []):
                    if _semantic_trampoline_variant_matches(data, pe, anchor, variant):
                        matched_variant = variant['id']
                        break
            match = matched_variant is not None and section == anchor['section']
        except ValueError:
            observed, section, offset, matched_variant, match = None,None,None,None,False
        anchors.append(dict(name=anchor['name'],va=anchor['va'],rva=anchor['va']-pe['image_base'],
                            length=anchor['length'],section=section,file_offset=offset,
                            sha256=observed,compatible=match,matched_variant=matched_variant,
                            semantics=anchor['semantics']))
    h=digest(data)
    registered=next((p for p in canonical['profiles'] if p['sha256']==h and p['size']==len(data)),None)
    families = canonical.get('families', {})
    family_id = next((name for name, family in families.items()
                      if family.get('pe_reference') == 'retail_pe'),
                     'retail-broker-v1' if not families else None)
    family = families.get(family_id, {})
    required = set(family.get('anchor_names', [a['name'] for a in canonical['anchors']]))
    by_name = {a['name']: a for a in anchors}
    required_anchors_match = bool(required) and all(by_name.get(name, {}).get('compatible') for name in required)
    compatible=layout_match and required_anchors_match
    registry_profile, registry_origin = _registry_profile_for(data, pe, registered)
    # Derive each observation capability from only the anchors it consumes.
    # PE/layout compatibility is required because the reader and UI command
    # routes use audited retail RVAs; unrelated gameplay, loading and resource
    # anchors are informational and must not suppress passive Broker reads.
    broker_read_anchors = ('debug_logger', 'debug_sink_vtable', 'debug_sink_global')
    broker_read = bool(layout_match and all(by_name.get(name, {}).get('compatible')
                                            for name in broker_read_anchors))
    route_anchor = bool(by_name.get('broker_editor_dump_route', {}).get('compatible'))
    singleton_anchor = bool(by_name.get('broker_singleton_accessor', {}).get('compatible'))
    manager_anchor = bool(by_name.get('broker_manager_global', {}).get('compatible'))
    dump_anchor = bool(by_name.get('native_dump_walker', {}).get('compatible'))
    # The 0x27 main-window opener is not a standalone family anchor. Grant it
    # only to a complete family match together with the Broker route anchor;
    # degraded profiles may still discover/use an already-open, signature-
    # checked editor when native_dump is independently proven.
    open_editor = bool(compatible and route_anchor)
    native_dump = bool(layout_match and broker_read and route_anchor and singleton_anchor
                       and manager_anchor and dump_anchor)
    walker = by_name.get('native_dump_walker', {})
    walker_variant = walker.get('matched_variant') if walker.get('compatible') else None
    hardened_walker = walker_variant in {
        'native-hardened-r-ai1-v1',
        'native-hardened-null-safe-stubs-v1',
    }
    # A matching walker alone is not enough to admit an executable. The
    # hardened classification applies only when the native Dump route and its
    # supporting Broker structures also pass the current build audit.
    hardened_dump = bool(native_dump and hardened_walker)
    capabilities = {
        'broker_read': broker_read,
        'open_broker_editor': open_editor,
        'native_dump': native_dump,
        'broker_capture_active_race': broker_read,
        'active_race_native_dump_safe': native_dump,
        'post_results_native_dump_safe': (True if hardened_dump else False if walker_variant == 'stock' else None),
        'hardened_dump': hardened_dump,
        'flow_builder': False,
    }
    loading_anchor = by_name.get('loading_legacy_failure', {})
    capabilities['legacy_loading_attract_present'] = bool(
        loading_anchor.get('compatible') and loading_anchor.get('matched_variant') == 'stock')
    capabilities['legacy_loading_attract_neutralized'] = bool(
        loading_anchor.get('compatible') and
        loading_anchor.get('matched_variant') == 'r-ai2-loading-false-trigger-neutralization-v1')
    capabilities['broker_dump_variant'] = ('native_hardened' if hardened_dump else
                                           'native_stock' if walker_variant == 'stock' else 'unknown')
    capability_compatible = bool(layout_match and broker_read)
    admitted = bool(compatible or capability_compatible)
    return dict(schema_version=2,sha256=h,size=len(data),pe=pe,layout_compatible=layout_match,
                anchors=anchors,anchor_compatible=compatible,
                status=('FULL_FAMILY_COMPATIBLE' if compatible else
                        'CAPABILITY_COMPATIBLE' if capability_compatible else 'INCOMPATIBLE'),
                compatibility_family=family_id if admitted else None,
                family_anchor_names=sorted(required),
                family_anchor_compatible=required_anchors_match,
                broker_core_compatible=broker_read,
                capability_compatible=capability_compatible,
                registry_profile=registry_profile,
                registry_profile_origin=registry_origin,
                build_classification=('hardened' if admitted and hardened_dump else
                                      'compatible' if admitted else 'incompatible'),
                capabilities=capabilities,
                audit_version=AUDIT_VERSION,
                exact_registered_profile=registered['profile'] if registered else None,
                automatic_trust=False,runtime_full_pass=False,
                audit_does_not_register=True)


def identify(data):
    # Identity gate precedes anchor work. Matching anchors cannot admit unknowns.
    h=digest(data)
    profile=next((p for p in definitions()['profiles'] if p['sha256']==h and p['size']==len(data)),None)
    if profile is None:
        raise ValueError('Unknown executable hash/size; exact registered builds only')
    audit=audit_build(data)
    if not audit['anchor_compatible'] or audit['pe'] != profile['pe']:
        raise ValueError('Registered build failed layout/anchor verification')
    return profile


def resolve_build(data, *, cache_root=None, write_local_profile=True, allow_degraded=False):
    """Resolve exact identity, a full family match, or an explicitly allowed Broker-core profile."""
    audit = audit_build(data)
    exact = next((p for p in definitions()['profiles']
                  if p['sha256'] == audit['sha256'] and p['size'] == audit['size']), None)
    if exact:
        committed = identify(data)
        profile = _profile_document(audit, exact_profile=committed,
                                    registry_profile=committed['vehicle_registry_profile'],
                                    registry_origin='committed_exact')
        resolved = {**audit, **profile, 'local_profile_cache': None, 'cache_reused': False}
    else:
        full_family = bool(audit['anchor_compatible'] and audit.get('compatibility_family'))
        degraded_core = bool(allow_degraded and audit.get('capability_compatible')
                             and audit.get('compatibility_family'))
        if not (full_family or degraded_core):
            failures = [a['name'] for a in audit['anchors'] if not a['compatible']]
            raise ValueError('Unknown executable failed structural family/Broker-core audit: ' +
                             (', '.join(failures) if failures else 'PE/layout mismatch'))
        if not audit['capabilities'].get('broker_read'):
            raise ValueError('Compatible family lacks the independently audited Broker read core')
        cache_root = Path(cache_root) if cache_root is not None else PROFILE_CACHE_ROOT
        path = _cache_path(cache_root, audit['sha256'])
        cached = _load_valid_cache(path, audit) if path.exists() else None
        profile = cached or _profile_document(audit)
        if write_local_profile and not cached:
            _write_cache(path, profile)
        resolved = {**audit, **profile, 'local_profile_cache': str(path), 'cache_reused': bool(cached)}
    family_name = resolved.get('compatibility_family')
    family = definitions().get('families', {}).get(family_name, {})
    exact_for_layout = next((p for p in definitions()['profiles']
                             if p['profile'] == family.get('observatory_layout_profile')), None)
    resolved['profile'] = resolved['profile_id']
    resolved['exact_profile_id'] = resolved.get('profile_id') if resolved['profile_origin'] == 'committed_exact' else None
    resolved['broker_dump_variant'] = resolved.get('capabilities', {}).get('broker_dump_variant', 'unknown')
    resolved['native_dump_post_results_safe'] = resolved.get('capabilities', {}).get('post_results_native_dump_safe')
    resolved['legacy_loading_attract_present'] = resolved.get('capabilities', {}).get('legacy_loading_attract_present')
    resolved['observatory'] = exact_for_layout.get('observatory') if exact_for_layout else None
    return resolved
