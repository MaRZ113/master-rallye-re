"""Deterministic, read-only PC/PS2 course survey; no renderer or asset writer.

PackFS is delegated to tngtool. Scene and PC sidecar semantics are delegated
to the reference Course SDK, imported without bytecode writes. Committed
outputs contain inventories/hashes, never original XML, meshes or textures.
"""
from __future__ import annotations

import argparse
from collections import Counter
import importlib
import json
import math
from pathlib import Path
import re
import struct
import sys
import xml.etree.ElementTree as ET
import zipfile

import tngtool as t
from build_report import EXPECTED

ROOT = Path(__file__).resolve().parents[1]
MAX_XML = 16 * 1024 * 1024
DIRECTIVE = re.compile(rb'\$[A-Za-z][A-Za-z0-9_]*\([^\x00\r\n)]{0,160}\)')
NULLS = {'', 'null', '(null)'}


def normalize(value):
    return (value or '').replace('/', '\\').lower()


def counter(values):
    return dict(sorted(Counter(values).items()))


def sdk_modules(path):
    sys.dont_write_bytecode = True
    sys.path.insert(0, str(path.resolve() / 'src'))
    return (importlib.import_module('master_rallye.course_xml'),
            importlib.import_module('master_rallye.sidecar'))


def signature(points):
    """Hash ordered float32 XYZ, preserving route direction and document order."""
    packed = bytearray()
    for point in points:
        if point is None or len(point) != 3 or not all(math.isfinite(x) for x in point):
            raise t.FormatError('Missing/non-finite marker position')
        try:
            packed.extend(struct.pack('<3f', *point))
        except (struct.error, OverflowError) as exc:
            raise t.FormatError('Marker position exceeds float32') from exc
    return t.sha(bytes(packed))


def parse_scene(data, source, sdk):
    if not 0 < len(data) <= MAX_XML or b'<!DOCTYPE' in data.upper() or b'<!ENTITY' in data.upper():
        raise t.FormatError('Unsupported XML size/declarations')
    try:
        tree = ET.fromstring(data)
        if tree.tag != 'Scene':
            raise t.FormatError('Expected Scene root')
        doc = sdk.parse_course_xml_bytes(data, source)
    except (ET.ParseError, ValueError, sdk.FormatError) as exc:
        raise t.FormatError('Malformed scene: ' + source) from exc
    rows = []
    for egg in doc.eggs:
        props = {v.name: v.value for v in egg.values if v.type_name != 'Matrix'}
        model = normalize(egg.model_name)
        if model in NULLS:
            model = None
        owners = [ai.ai_name for ai in egg.ai_objects if normalize(ai.ai_name) not in NULLS]
        matrix = egg.matrix()
        if matrix and (matrix.issues or any(row is None for row in matrix.rows)):
            raise t.FormatError('Invalid authored matrix: ' + source + '/' + str(egg.name))
        # Visible means authored flag and model reference; no runtime draw proof.
        visible = bool(model and props.get('Use en2d', 'False') == 'False'
                       and props.get('en3d Visible', 'False') == 'True')
        parameters = []
        for ai in egg.ai_objects:
            if normalize(ai.ai_name) in NULLS:
                continue
            for component in ai.components:
                parameters.append({'owner': ai.ai_name, 'component': component.tag,
                                   'values': [{'name': v.name, 'value': v.value}
                                              for v in component.values]})
        rows.append({'list': egg.list_name, 'egg': egg.name, 'model': model,
                     'authored_visible': visible, 'owners': owners,
                     'position': list(matrix.position) if matrix and matrix.position else None,
                     'matrix_sha256': t.sha(json.dumps(matrix.rows).encode()) if matrix else None,
                     'properties': props, 'parameters': parameters})
    markers = {str(m.name): {'count': len(m.markers),
                            'ordered_xyz_f32_sha256': signature([v.position for v in m.markers])}
               for m in doc.marker_lists}
    if len(markers) != len(doc.marker_lists):
        raise t.FormatError('Duplicate marker list name: ' + source)
    landscape = [r['model'] for r in rows if r['list'] == 'landscape' and r['model']]
    if len(landscape) > 1:
        raise t.FormatError('Ambiguous landscape: ' + source)
    scene = {'source': source, 'sha256': t.sha(data),
             'landscape': landscape[0] if landscape else None, 'marker_lists': markers,
             'entity_count': len(rows), 'authored_visible_model_references': sum(r['authored_visible'] for r in rows),
             'model_references': counter(r['model'] for r in rows if r['model']),
             'owners': counter(o for r in rows for o in r['owners']),
             'placement_signature': t.sha(json.dumps([(r['list'], r['egg'], r['model'], r['matrix_sha256'])
                                                       for r in rows]).encode()),
             '_route_points': [v.position for v in doc.marker_list('RaceLine').markers]
                              if doc.marker_list('RaceLine') else []}
    scene['declared_visible_misc_world_references'] = sum(
        r['authored_visible'] and r['model'].startswith('misc\\') and not r['model'].startswith('misc\\sky\\')
        for r in rows)
    scene['controller_egg_counts'] = {owner: sum(owner in r['owners'] for r in rows)
                                    for owner in ('gaEntitySpline', 'gaAiRigidBody', 'gaAnimals_BirdManager',
                                                  'aiSpawnParticle', 'gaRaceSplitTimeAI')}
    return scene, rows


def route_alignment(a, b):
    """Bounded end-record allowance; never sort, reverse or fit a route."""
    if min(len(a), len(b)) < 20:
        return None
    choices = []
    for shift in range(-3, 4):
        pa, pb = a[max(shift, 0):], b[max(-shift, 0):]
        count = min(len(pa), len(pb))
        distances = [math.dist(x, y) for x, y in zip(pa[:count], pb[:count])]
        choices.append({'ps2_start': max(shift, 0), 'pc_start': max(-shift, 0),
                        'compared_points': count, 'max_distance': max(distances),
                        'mean_distance': sum(distances) / count,
                        'within_one_world_unit': sum(v <= 1 for v in distances) / count})
    return min(choices, key=lambda r: (r['mean_distance'], -r['compared_points']))


def pair_courses(ps2, pc):
    """Require unique landscape identity; ordered route agreement grades EXACT.

    STRONG requires >=90% count agreement and ordered spatial agreement.
    A filename alone cannot create a pair. Auxiliary PC RaceTest scenes are
    retained in scan coverage but cannot displace a canonical named course.
    """
    pairs = []
    for scene in sorted(ps2, key=lambda r: r['source']):
        candidates = [r for r in pc if r['landscape'] and r['landscape'] == scene['landscape']
                      and 'RaceLine' in r['marker_lists']]
        # Eliminate explicit Test* scenes, without treating name as identity.
        candidates = [r for r in candidates if not Path(r['source']).stem.lower().startswith('test')]
        route = scene['marker_lists'].get('RaceLine')
        alias = False
        if not candidates and route:
            # A retail exporter can use track01 while PS2 uses italy1. Recover
            # aliases from ordered spatial data, never from basename similarity.
            spatial = []
            for other in pc:
                if not other['landscape'] or 'RaceLine' not in other['marker_lists']:
                    continue
                alignment = route_alignment(scene.get('_route_points', []), other.get('_route_points', []))
                if alignment and alignment['within_one_world_unit'] >= .95:
                    spatial.append(other)
            if len(spatial) == 1:
                candidates, alias = spatial, True
        exact = [r for r in candidates if route and r['marker_lists']['RaceLine'] == route]
        chosen = exact[0] if len(exact) == 1 else candidates[0] if len(candidates) == 1 else None
        confidence = 'UNPAIRED'
        alignment = route_alignment(scene.get('_route_points', []), chosen.get('_route_points', [])) if chosen else None
        if chosen and route:
            other = chosen['marker_lists']['RaceLine']
            if other == route:
                confidence = 'EXACT'
            elif (alignment and alignment['within_one_world_unit'] >= .95
                  and min(route['count'], other['count']) >= .9 * max(route['count'], other['count'])):
                confidence = 'STRONG'
            else:
                confidence = 'TENTATIVE'
        pairs.append({'ps2': scene['source'], 'pc': chosen['source'] if chosen else None,
                      'confidence': confidence, 'landscape': scene['landscape'],
                      'ps2_route': route, 'pc_route': chosen['marker_lists'].get('RaceLine') if chosen else None,
                      'candidate_count': len(candidates),
                      'pc_landscape': chosen['landscape'] if chosen else None,
                      'landscape_alias_from_spatial_evidence': alias, 'ordered_spatial_check': alignment,
                      'evidence': 'CONFIRMED_BY_BYTES' if confidence == 'EXACT' else 'STATIC_INFERENCE',
                      'basis': 'Unique landscape identity or spatially proved alias + ordered route geometry; no coordinate fitting'})
    return pairs


def material_strings(data):
    tokens = [m.group().decode('ascii') for m in DIRECTIVE.finditer(data)]
    # Distinct printable strings are search evidence, not decoded PSM records.
    names = sorted({m.group().decode('ascii') for m in re.finditer(rb'[\x20-\x7e]{5,2048}', data)
                    if b'$shader(' in m.group() or b'$detail(' in m.group() or b'$surfacetype(' in m.group()})
    return {'directive_occurrences': counter(tokens), 'distinct_directives': sorted(set(tokens)),
            'distinct_material_string_candidates': names,
            'metric': 'Raw payload string occurrences; NOT material/draw/instance counts',
            'evidence': 'CONFIRMED_BY_BYTES'}


def output_path(folder, name, inputs=()):
    folder = folder.resolve()
    if not any(folder.is_relative_to(base.resolve()) for base in (ROOT / 'cdelta1', ROOT / 'data' / 'cdelta1')):
        raise t.FormatError('Survey output must stay under cdelta1 or ignored data/cdelta1')
    result = (folder / name).resolve()
    if not any(result.is_relative_to(base.resolve()) for base in (ROOT / 'cdelta1', ROOT / 'data' / 'cdelta1')):
        raise t.FormatError('Survey output path escapes allowed directory')
    t.protect_inputs(result, list(inputs))
    return result


def model_resource(model, lookup):
    prefix = '\\TNG\\DATAPSM\\' + model.upper()
    return next((prefix + ext for ext in ('.PSM', '.PSB') if prefix + ext in lookup), None)


def pc_compiled_water(pc_root):
    """Four bounded SDK samples; decoded geometry proves existing PC usage."""
    dx = importlib.import_module('master_rallye.dx_course')
    sc = importlib.import_module('master_rallye.sidecar')
    results = []
    for folder in ('France1', 'Italy_S1', 'Turkey1', 'Turkey3'):
        directory = pc_root / 'DataGx' / 'Course' / folder
        paths = {suffix: sorted(p for p in directory.iterdir() if p.suffix.lower() == suffix)
                 for suffix in ('.dx', '.txt')}
        if any(len(v) != 1 for v in paths.values()):
            raise t.FormatError('Ambiguous compiled water sample: ' + folder)
        model = dx.parse_course_dx(paths['.dx'][0])
        if not model.course_render_validated:
            raise t.FormatError('Compiled PC sample failed complete render validation: ' + folder)
        sidecar = sc.parse_sidecar(paths['.txt'][0])
        sc.apply_material_candidates(model.physical_draws, sidecar)
        water = []
        for draw in model.physical_draws:
            if (any(re.search('water|puddle', slot, re.I) for slot in draw.texture_tuple)
                    or any(re.search('water|puddle', value.name, re.I) for value in draw.material_candidates)):
                indices = model.draw_global_indices(draw)
                points = [model.vertices.positions[i] for i in sorted(set(indices))]
                if not points or not all(math.isfinite(v) for p in points for v in p):
                    raise t.FormatError('Invalid water draw bounds')
                water.append({'draw_index': draw.draw_index, 'triangles': draw.triangle_count,
                              'textures': list(draw.texture_tuple),
                              'material_candidates': [v.name for v in draw.material_candidates],
                              'bounds': {'min': [min(p[i] for p in points) for i in range(3)],
                                         'max': [max(p[i] for p in points) for i in range(3)]}})
        results.append({'source': paths['.dx'][0].relative_to(pc_root).as_posix(),
                        'sha256': t.file_hash(paths['.dx'][0]), 'vertex_count': model.vertex_count,
                        'triangles': model.triangle_count, 'draw_count': len(model.physical_draws),
                        'complete_disjoint_render_validated': model.course_render_validated,
                        'water_related_draws': water, 'evidence': 'CONFIRMED_BY_BYTES',
                        'scope': 'Broad water/puddle texture or material binding; no runtime visibility proof'})
    return results


def screenshot_inventory(screens, archive):
    rows = []
    if screens:
        for path in sorted(screens.iterdir()):
            if path.is_file() and path.suffix.lower() in ('.jpg', '.jpeg', '.png'):
                rows.append({'name': path.name, 'size': path.stat().st_size, 'sha256': t.file_hash(path)})
    archived = []
    if archive:
        with zipfile.ZipFile(archive) as z:
            for info in sorted(z.infolist(), key=lambda r: r.filename):
                if info.is_dir():
                    continue
                if info.file_size > 64 * 1024 * 1024:
                    raise t.FormatError('Screenshot archive member exceeds memory limit')
                archived.append({'name': info.filename, 'size': info.file_size, 'sha256': t.sha(z.read(info))})
    return {'files': rows, 'archive': {'size': archive.stat().st_size, 'sha256': t.file_hash(archive),
                                      'members': archived} if archive else None,
            'evidence': 'SCREENSHOT_CORRELATION',
            'scope': 'File provenance only; visual correlation is documented separately, no course/build/frame proof'}


def write_tables(output, pairs, delta, inputs):
    spatial_checks = [p for p in pairs if p.get('ordered_spatial_check')]
    exact_prefixes = sum(p['ordered_spatial_check']['max_distance'] == 0 for p in spatial_checks)
    aliases = [p for p in pairs if p.get('landscape_alias_from_spatial_evidence')]
    pair_lines = ['# Course pairing and comparable counts', '',
        'All pairs require internal resource or ordered spatial evidence. STRONG is not identical XML or binary content.', '',
        f'{exact_prefixes} of {len(spatial_checks)} spatially checked pairs have identical compared ordered XYZ prefixes. Full route counts/hashes remain separate in JSON.', '',
        f'{len(aliases)} landscape aliases are supported by ordered spatial evidence. No coordinate fitting, sorting or reversal is used.', '',
        '| PS2 course | PC scene | Confidence | Route points PS2/PC | Ordered points within 1 unit | Declared misc-world refs PS2/PC |',
        '|---|---|---|---|---|---|']
    for pair in pairs:
        course = pair['ps2'].rsplit('\\', 1)[-1]
        a, b = pair['ps2_route'], pair['pc_route']
        spatial = pair['ordered_spatial_check']
        metric = pair.get('counts', {}).get('declared_visible_misc_world_references')
        pair_lines.append(f"| {course} | {pair['pc'] or 'UNPAIRED'} | {pair['confidence']} | "
                          f"{a['count'] if a else '?'} / {b['count'] if b else '?'} | "
                          f"{100*spatial['within_one_world_unit']:.3f}%" if spatial else
                          f"| {course} | {pair['pc'] or 'UNPAIRED'} | {pair['confidence']} | ? | UNKNOWN")
        pair_lines[-1] += f" | {metric['ps2']} / {metric['pc']} |" if metric else ' | UNKNOWN |'
    pair_lines += ['', 'The prop metric counts authored visible non-2D misc model references excluding misc/sky.',
        'Each Egg counts once, including duplicates and stub references. Landscape aggregates, GPS/editor helpers, cars, HUD and sound are excluded.',
        'Total trees, plants, water bodies and runtime draws remain UNKNOWN. Generic entity/visible-reference counts in JSON are diagnostic, not scenery populations.',
        'course-pairs.json retains route hashes, spatial deviations, resource aliases, owner/model counts and all 36 identities.']
    matrix = ['# Ranked course delta catalog', '',
        '16 catalog records include known leads, overlapping fleet members, shared semantics and a rejected stub control; this is not 16 independent new features.', '',
        '| Candidate | Classification | PS2 / PC metric | Presence in scanned layer | Evidence | Suggested research |',
        '|---|---|---|---|---|---|']
    ranking = ['ambient-spline-fleet', 'haybale-rigidbody', 'particle-owner', 'detail-vegetation', 'checkpoint',
               'birds', 'water-shared', 'turkey3-water', 'treeblend', 'dinghy', 'barge', 'airship',
               'tumbleweed', 'wire-shaders', 'raceline', 'nessie-stub']
    for key in ranking:
        record = next(r for r in delta if r['id'] == key)
        if 'ps2_material_evidence' in record:
            metric = f"{len(record['ps2_material_evidence'])} / {len(record['pc_material_evidence'])} landscape directive-presence families"
        else:
            metric = f"{len(record['ps2_occurrences'])} / {len(record['pc_occurrences'])} authored matching Eggs"
        matrix.append(f"| {record['name']} | {record['classification']} | {metric} | {record['presence']} | "
                      f"{record['evidence']} | {record['next_phase']} |")
    matrix += ['', 'PC Egg comparisons use the 36 paired canonical courses; global absence checks are bounded by 99 PC XML / 7595 files.',
        'A zero standalone Egg count does not exclude geometry embedded in a course. PC dinghy/hay examples are in course-dressing-survey.md.',
        'Material counts above use one resource family with a qualifying directive, not raw PSM occurrences or visible instances.',
        'Rows overlap: do not sum fleet with individual vessel families, or marker owners with scene resources.',
        'delta-matrix.json includes exact entities, lists, transforms, owners, duplicate parameter values, resource links, material evidence, significance and open questions.',
        'Runtime execution is UNKNOWN. User-observed checkpoint interaction and screenshot correlations are separately labeled.']
    for name, lines in (('course-pairs.md', pair_lines), ('delta-matrix.md', matrix)):
        output_path(output, name, inputs).write_text('\n'.join(lines) + '\n', encoding='utf-8', newline='\n')


def read_cached(entry, inputs, cache):
    """Diagnostic extraction cache; independently decode source on every use.

    A matching cache-sidecar pair cannot authenticate itself. Re-decoding via
    tngtool binds the payload to the original archive, including coherent edits
    of cached bytes and their local SHA metadata. Cache is for inspection only.
    """
    output_path(cache, 'guard', [inputs / n for n in EXPECTED])
    path = t.extraction_path(cache, entry['path'])
    sidecar = path.with_name(path.name + '.provenance.json')
    alternate = t.extraction_path(ROOT / 'data' / 'cdelta1' / 'materials' / 'extracted', entry['path'])
    if not path.exists() and alternate.is_file():
        path = alternate
        sidecar = path.with_name(path.name + '.provenance.json')
    payload, canonical = t.read_payload(entry, inputs / 'TNG.000')
    if path.is_file() and sidecar.is_file():
        if path.stat().st_size > t.MAX_OUTPUT:
            raise t.FormatError('Cached payload exceeds memory limit')
        report = json.loads(sidecar.read_text(encoding='utf-8'))
        cached = path.read_bytes()
        if (report.get('path') == entry['path'] and report.get('offset') == entry['offset']
                and report.get('stored_size') == entry['stored_size']
                and canonical['stored_sha256'] == report.get('stored_sha256')
                and canonical['payload_sha256'] == report.get('payload_sha256')
                and t.sha(cached) == canonical['payload_sha256']):
            return payload, canonical
        raise t.FormatError('Stale/corrupt survey cache: ' + entry['path'])
    report = canonical
    # Extraction remains ignored. Never cache into source corpora or SDK.
    output_path(cache, 'guard', [inputs / n for n in EXPECTED])
    t.protect_inputs(path, [inputs / n for n in EXPECTED])
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_bytes(payload)
    t.write_json(sidecar, report)
    return payload, report


def build(inputs, pc_root, sdk_root, output, screens=None, archive=None):
    provenance = {}
    for name, expected in EXPECTED.items():
        path = inputs / name
        value = t.file_hash(path)
        if value != expected:
            raise t.FormatError('Canonical PS2 hash mismatch: ' + name)
        provenance[name] = {'size': path.stat().st_size, 'sha256': value}
    sdk, sidecar = sdk_modules(sdk_root)
    manifest, _ = t.load_pak(inputs / 'TNG.PAK')
    files = sorted([r for r in manifest['entries'] if r['kind'] == 'file'], key=lambda r: r['path'])
    lookup = {r['path']: r for r in files}
    cache = ROOT / 'data' / 'cdelta1' / 'cache'
    scenes, rows, payload_reports, pc_hashes = {'ps2': [], 'pc': []}, {}, [], {}
    for entry in files:
        if entry['path'].startswith('\\TNG\\DATASCENE\\') and entry['path'].endswith('.XML'):
            data, report = read_cached(entry, inputs, cache)
            scene, detail = parse_scene(data, entry['path'], sdk)
            scenes['ps2'].append(scene)
            rows[entry['path']] = detail
            payload_reports.append(report)
    for path in sorted((pc_root / 'DataScene').rglob('*'), key=lambda p: p.as_posix().lower()):
        if path.is_file() and path.suffix.lower() == '.xml':
            data = path.read_bytes()
            source = path.relative_to(pc_root).as_posix()
            scene, detail = parse_scene(data, source, sdk)
            scenes['pc'].append(scene)
            rows[source] = detail
            pc_hashes[source] = t.sha(data)
    ps2_courses = [s for s in scenes['ps2'] if '\\RACETEST\\' in s['source']]
    pc_courses = [s for s in scenes['pc'] if s['source'].startswith('DataScene/RaceTest/')]
    pairs = pair_courses(ps2_courses, pc_courses)
    for platform in scenes.values():
        for scene in platform:
            scene.pop('_route_points', None)
    matched = {p['pc'] for p in pairs if p['confidence'] in ('EXACT', 'STRONG')}
    ps2_models = sorted({s['landscape'] for s in ps2_courses if s['landscape']})
    material_inventory = {'ps2': [], 'pc': []}
    for model in ps2_models:
        logical = model_resource(model, lookup)
        if not logical:
            raise t.FormatError('Landscape resource unresolved: ' + model)
        payload, report = read_cached(lookup[logical], inputs, cache)
        payload_reports.append(report)
        material_inventory['ps2'].append({'model': model, 'source': logical,
                                          'provenance': report, **material_strings(payload)})
    for path in sorted((pc_root / 'DataGx' / 'Course').rglob('*'), key=lambda p: p.as_posix().lower()):
        if path.is_file() and path.suffix.lower() == '.txt':
            doc = sidecar.parse_sidecar(path)
            source = path.relative_to(pc_root).as_posix()
            pc_hashes[source] = t.file_hash(path)
            names = [m.name for m in doc.materials]
            tokens = [token.group().decode('ascii') for name in names
                      for token in DIRECTIVE.finditer(name.encode('latin-1'))]
            material_inventory['pc'].append({'source': source, 'sha256': pc_hashes[source],
                'material_records': len(names), 'material_names': names,
                'directive_material_occurrences': counter(tokens), 'distinct_directives': sorted(set(tokens)),
                'mesh_labels': [m.name for m in doc.meshes],
                'texture_stems': sorted({v.resource_stem for m in doc.materials for v in m.textures}),
                'metric': 'SDK parsed sidecar material records, not render draws or objects'})
    pc_files = sorted(p.relative_to(pc_root).as_posix() for p in pc_root.rglob('*') if p.is_file())
    definitions = json.loads((ROOT / 'cdelta1' / 'delta-definitions.json').read_text(encoding='utf-8'))
    delta = []
    all_ps2 = [s for s in scenes['ps2'] if '\\RACETEST\\' in s['source']]
    all_pc = [s for s in scenes['pc'] if s['source'] in matched]
    for definition in definitions:
        record = dict(definition)
        occurrences = {'ps2': [], 'pc': []}
        for platform, selected in (('ps2', all_ps2), ('pc', all_pc)):
            for scene in selected:
                for row in rows[scene['source']]:
                    if (any(re.search(pattern, row['model'] or '', re.I) for pattern in definition.get('models', []))
                            or any(owner in row['owners'] for owner in definition.get('owners', []))):
                        occurrence = {'course': scene['source'], **row}
                        if row['model'] and platform == 'ps2':
                            occurrence['resource'] = model_resource(row['model'], lookup)
                        occurrences[platform].append(occurrence)
        record['ps2_occurrences'] = occurrences['ps2']
        record['pc_occurrences'] = occurrences['pc']
        record['ps2_courses'] = sorted({r['course'] for r in occurrences['ps2']})
        record['pc_courses'] = sorted({r['course'] for r in occurrences['pc']})
        record['authored_representation'] = 'XML model reference/owners/parameters; runtime visibility/behavior UNKNOWN'
        delta.append(record)
    material_tests = {
        'detail-vegetation': lambda s: '$detail(' in s,
        'water-shared': lambda s: any(v in s for v in ('$shader(water', '$shader(puddle)', '$surfacetype(water)')),
        'turkey3-water': lambda s: '$shader(puddle)' in s or '$surfacetype(water)' in s,
        'treeblend': lambda s: '$shader(treeblend)' in s,
        'wire-shaders': lambda s: '$shader(wire' in s,
    }
    for record in delta:
        if record['id'] not in material_tests:
            continue
        predicate = material_tests[record['id']]
        for platform in ('ps2', 'pc'):
            matches = [m for m in material_inventory[platform] if any(predicate(s) for s in m['distinct_directives'])
                       and (record['id'] != 'turkey3-water' or 'turkey3' in m['source'].lower())]
            record[platform + '_material_evidence'] = [
                {'source': m['source'], 'matching_directives': [s for s in m['distinct_directives'] if predicate(s)],
                 'metric': m['metric']} for m in matches]
            if platform == 'ps2':
                models = {m['model'] for m in matches}
                record['ps2_courses'] = sorted(s['source'] for s in ps2_courses if s['landscape'] in models)
            else:
                folders = {normalize(Path(m['source']).parent.name) for m in matches}
                record['pc_courses'] = sorted(s['source'] for s in pc_courses if s['source'] in matched
                                              and s['landscape'] and s['landscape'].split('\\')[1] in folders)
    probes = []
    selected_resources = sorted({r['resource'] for record in delta for r in record['ps2_occurrences']
                                 if r.get('resource')})
    for logical in selected_resources:
        payload, report = read_cached(lookup[logical], inputs, cache)
        payload_reports.append(report)
        probes.append({'source': logical, 'provenance': report,
                       'small_payload_geometry_unproved': len(payload) <= 44,
                       **material_strings(payload)})
    for pair in pairs:
        if not pair['pc']:
            continue
        a = next(s for s in ps2_courses if s['source'] == pair['ps2'])
        b = next(s for s in pc_courses if s['source'] == pair['pc'])
        pair['counts'] = {k: {'ps2': a[k], 'pc': b[k]} for k in
                          ('entity_count', 'authored_visible_model_references', 'declared_visible_misc_world_references')}
        pair['model_counts'] = {'ps2': a['model_references'], 'pc': b['model_references']}
        pair['owner_counts'] = {'ps2': a['owners'], 'pc': b['owners']}
    compiled_water = pc_compiled_water(pc_root)
    for row in compiled_water:
        pc_hashes[row['source']] = row['sha256']
    source_inventory = {'schema_version': 1, 'ps2_inputs': provenance,
        'ps2_payload_provenance': sorted(payload_reports, key=lambda p: p['path']),
        'pc_source_sha256': dict(sorted(pc_hashes.items())),
        'sdk_parser_sha256': {name: t.file_hash(sdk_root / 'src' / 'master_rallye' / name)
                              for name in ('course_xml.py', 'sidecar.py', 'dx_course.py')},
        'pc_file_count': len(pc_files), 'ps2_file_count': len(files),
        'ps2_xml_count': len(scenes['ps2']), 'pc_xml_count': len(scenes['pc']),
        'ps2_racetest_count': len(ps2_courses), 'pc_racetest_count': len(pc_courses),
        'ps2_course_model_count': len(ps2_models), 'pc_sidecar_count': len(material_inventory['pc']),
        'scope': 'Complete DataScene XML + RaceTest landscape PSM + PC course TXT; not full PSM geometry/runtime'}
    inputs_to_protect = [inputs / n for n in EXPECTED] + [pc_root / p for p in pc_hashes]
    for name, data in (('input-provenance.json', source_inventory), ('course-pairs.json', pairs),
                       ('scene-inventory.json', scenes), ('material-inventory.json', material_inventory),
                       ('delta-matrix.json', delta), ('resource-inventory.json',
                        {'ps2_paths': [r['path'] for r in files], 'pc_paths': pc_files}),
                       ('resource-probes.json', probes), ('pc-compiled-water.json', compiled_water),
                       ('screenshot-provenance.json', screenshot_inventory(screens, archive))):
        t.write_json(output_path(output, name, inputs_to_protect), data)
    write_tables(output, pairs, delta, inputs_to_protect)
    return source_inventory


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument('--inputs', type=Path, required=True)
    ap.add_argument('--pc', type=Path, required=True, help='Curated retail Data.sma_unpacked root')
    ap.add_argument('--sdk', type=Path, required=True, help='Read-only Course SDK checkout')
    ap.add_argument('--output', type=Path, default=ROOT / 'cdelta1')
    ap.add_argument('--screens', type=Path, help='Optional read-only screenshot directory')
    ap.add_argument('--screen-archive', type=Path, help='Optional read-only screenshot ZIP')
    args = ap.parse_args()
    # Guard before any cache write or expensive read.
    output_path(args.output, 'guard', [args.inputs / n for n in EXPECTED])
    result = build(args.inputs, args.pc, args.sdk, args.output, args.screens, args.screen_archive)
    print(json.dumps({key: value for key, value in result.items() if key.endswith('_count')}, indent=2))


if __name__ == '__main__':
    main()
