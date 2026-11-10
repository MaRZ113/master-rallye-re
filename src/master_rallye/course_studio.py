"""Course Studio transactions. No bpy, renderer hooks or installation writes."""
from __future__ import annotations

import copy
import hashlib
import json
import math
import re
import shutil
import struct
import tempfile
from dataclasses import asdict, dataclass, replace
from pathlib import Path
import xml.etree.ElementTree as ET

from .course_sdk import load_course_project, discover_course_resources, build_course_race_logic
from .course_xml import parse_course_xml_bytes
from .course_race_authoring import CourseRaceLogicAuthoring
from .course_tag100 import parse_course_tag100_bytes
from .dx_course import parse_course_dx_bytes
from .hnt import parse_hnt, resolve_hnt_entries
from .errors import MasterRallyeError
from .dxt import parse_dxt

SCHEMA = "mr-course-studio/1"
KINDS = ("render_dx", "race_test_xml", "hnt", "sfl", "source_txt", "source_gxm")
SUPPORT = {
    "marker_positions": "SUPPORTED", "split_center_radius_id": "SUPPORTED",
    "race_line_limit_positions": "SUPPORTED", "visual_positions_same_topology": "SUPPORTED",
    "marker_inventory_templates": "SUPPORTED", "marker_direction": "INSPECT_ONLY", "collision_bsp": "INSPECT_ONLY",
    "sfl": "INSPECT_ONLY", "water": "INSPECT_ONLY", "new_surface_physics": "UNKNOWN",
    "alternative_native_ai_routes": "UNKNOWN", "proxy_rigid_props": "INSPECT_ONLY",
    "new_geometry_cooked_runtime": "INSPECT_ONLY",
    "surface_types": "INSPECT_ONLY", "sound_triggers": "INSPECT_ONLY",
    "ps2_spline_birds_grass_shrubs": "INSPECT_ONLY",
}


def digest(data):
    return hashlib.sha256(data).hexdigest()


def encoded(value):
    return (json.dumps(value, indent=2, sort_keys=True) + "\n").encode("utf-8")


def exact_path(root, reference):
    """Resolve portable native references without fuzzy basename fallback."""
    parts = reference.replace("\\", "/").split("/")
    if not parts or any(p in ("", ".", "..") or ":" in p for p in parts):
        raise ValueError(f"Unsafe resource reference: {reference}")
    current = Path(root)
    for part in parts:
        matches = [p for p in current.iterdir() if p.name.casefold() == part.casefold()] if current.is_dir() else []
        if len(matches) != 1:
            raise ValueError(f"Missing or ambiguous resource {reference}: {matches}")
        current = matches[0]
    return current.resolve()


def data_root(path):
    for parent in (path, *path.parents):
        if parent.name.casefold() in ("datascene", "datagx"):
            return parent.parent
        if (parent / "DataGx").is_dir() and (parent / "DataScene").is_dir():
            return parent
    return None


@dataclass(frozen=True)
class Finding:
    severity: str
    path: str
    message: str


class CourseStudio:
    """One CourseProject, explicit resource bindings and preserving staging."""

    def __init__(self, source, *, resource_root=None, race_id=None):
        source = Path(source).resolve()
        self.source = source
        self.registry = None
        self.race_id = race_id
        document = None
        if source.suffix.lower() == ".json":
            document = json.loads(source.read_text(encoding="utf-8"))
            if document.get("schema") == "mr-course-registry/1":
                self.registry = document
                choices = [r for r in document["races"] if race_id is None or r["id"] == race_id]
                if len(choices) != 1:
                    raise ValueError("Registry contains multiple races; select an explicit Race ID")
                root = Path(resource_root).resolve() if resource_root else source.parent / "resource-root"
                source = exact_path(root, choices[0]["scene"])
                self.race_id = choices[0]["id"]
            elif document.get("schema") == SCHEMA:
                source = (source.parent / document["entry"]).resolve()
                registration = document.get('registry')
                if registration:
                    self.registry = json.loads((self.source.parent / registration['manifest']).read_text(encoding='utf-8'))
                    self.race_id = registration['race_id']
            else:
                raise ValueError("Unsupported project manifest schema")
        self.root = Path(resource_root).resolve() if resource_root else data_root(source)
        search = (self.root / 'DataScene' / 'RaceTest',) if self.root and source.suffix.lower() != '.xml' else ()
        paths = discover_course_resources(source, search_roots=search)
        bindings = {kind: getattr(paths, kind) for kind in KINDS}
        if document and document.get("schema") == SCHEMA:
            base = self.source.parent
            bindings.update({k: (base / v).resolve() for k, v in document["resources"].items()})
            if document.get("resource_root"):
                self.root = (base / document["resource_root"]).resolve()
        elif bindings['race_test_xml'] and self.root:
            race_source = bindings['race_test_xml']
            xml = ET.fromstring(race_source.read_bytes())
            models = [v.get("Value") for e in xml.iter("Egg") if e.get("Name", "").casefold() == "landscape"
                      for v in e.iter("Value") if v.get("Name") == "en3d Model Name"]
            if len(models) != 1:
                raise ValueError(f"Expected one explicit landscape model, found {models}")
            bindings["render_dx"] = exact_path(self.root / "DataGx", models[0] + ".dx")
            for kind, suffix in (("source_txt", ".txt"), ("source_gxm", ".gxm")):
                candidate = bindings["render_dx"].with_suffix(suffix)
                if candidate.is_file():
                    bindings[kind] = candidate
            hnt = race_source.with_suffix(".hnt")
            if hnt.is_file():
                bindings["hnt"] = hnt
            ai = [v.get("Value") for v in xml.iter("Value") if v.get("Name") == "AI DataSet Name"]
            if len(set(ai)) > 1:
                raise ValueError(f"Ambiguous AI DataSet Name: {ai}")
            if ai:
                ref = ai[0].replace("\\", "/")
                if not ref.lower().endswith(".sfl"):
                    ref += ".sfl"
                bindings["sfl"] = exact_path(self.root / "DataScene", ref)
        resolved = replace(paths, **bindings, candidates=tuple((k, (v,) if v else ()) for k, v in bindings.items()))
        self.project = load_course_project(source, resource_paths=resolved)
        self.editor = CourseRaceLogicAuthoring.from_path(bindings["race_test_xml"]) if bindings["race_test_xml"] else None
        self.files = {}
        if self.root:
            for path in bindings.values():
                if path:
                    self._add(path)
            if bindings["render_dx"]:
                # Preserve opaque course sidecars alongside the selected model.
                for path in bindings["render_dx"].parent.rglob("*"):
                    if path.is_file():
                        self._add(path)
            if bindings["hnt"]:
                for entry in resolve_hnt_entries(parse_hnt(bindings["hnt"]), self.root / "DataGx"):
                    if entry.resolved_path:
                        self._add(self.root / "DataGx" / entry.resolved_path)
        self.hashes = {k: digest(p.read_bytes()) for k, p in self.files.items()}
        self.geometry = None
        self.structural_audit = copy.deepcopy(document.get('marker_builder', [])) if document else []
        self.feature_metadata = copy.deepcopy(document.get('scene_features', [])) if document else []
        self.editor_routes = []
        if document and document.get('schema') == SCHEMA and document.get('editor_routes'):
            routes = json.loads((self.source.parent / document['editor_routes']).read_text(encoding='utf-8'))
            if routes.get('schema') != 'mr-course-neutral-routes/1':
                raise ValueError('Unsupported neutral route schema')
            self.editor_routes = routes['routes']
            for route in self.editor_routes:
                if route['role'] not in ('AI_PROPOSAL', 'PLAYER_REGION') or not route['paths']:
                    raise ValueError('Invalid neutral route role/paths')
                for points in route['paths']:
                    if len(points)<2 or any(len(p)!=3 or not all(math.isfinite(v) for v in p) for p in points):
                        raise ValueError('Invalid neutral route coordinates')
        self.replacements = {}
        self.inherited_findings = [Finding(**f) for f in document.get('findings', [])] if document and document.get('schema') == SCHEMA else []

    def stage_texture(self, source, draft):
        source = Path(source).resolve(); draft = Path(draft).resolve()
        key = source.relative_to(self.root).as_posix()
        if key not in self.files or source == draft:
            raise ValueError('Texture replacement must bind a project dependency and separate draft')
        template = parse_dxt(source); replacement = parse_dxt(draft)
        if template.header != replacement.header:
            raise ValueError('Texture draft changed the native template header/dimensions')
        self.replacements[key] = draft.read_bytes()

    def _add(self, path):
        path = path.resolve()
        key = path.relative_to(self.root).as_posix()
        folded = [k for k in self.files if k.casefold() == key.casefold() and k != key]
        if folded:
            raise ValueError(f"Case-ambiguous resource: {key}")
        self.files[key] = path

    def collision(self):
        model = self.project.render._parsed_model if self.project.render else None
        if model is None or not model.trailing.data:
            raise ValueError("No course BSP payload")
        return parse_course_tag100_bytes(model.trailing.data, str(model.source), allow_trailing=True)

    def set_visual_positions(self, positions):
        """Same-order XYZ only. Every other byte (including BSP/bounds) is kept."""
        model = self.project.render._parsed_model
        if len(positions) != model.vertex_count:
            raise ValueError("Course visual writer refuses changed vertex count")
        raw = bytearray(self.project.resources.render_dx.read_bytes())
        for index, (old, point) in enumerate(zip(model.vertices.positions, positions)):
            point = tuple(float(v) for v in point)
            if len(point) != 3 or not all(math.isfinite(v) for v in point):
                raise ValueError("Invalid visual position")
            if math.dist(old, point) <= max(1e-5, max(map(abs, old), default=1) * 2e-7):
                continue
            struct.pack_into("<3f", raw, model.vertices.position_offset + index * 12, *point)
        parsed = parse_course_dx_bytes(bytes(raw))
        if not parsed.course_render_validated:
            raise ValueError("Position patch failed course parser validation")
        self.geometry = bytes(raw)

    def validate(self):
        findings = list(self.inherited_findings)
        def add(level, path, message): findings.append(Finding(level, str(path), message))
        for kind in ("render_dx", "race_test_xml", "hnt", "sfl"):
            if getattr(self.project.resources, kind) is None:
                add("ERROR", kind, "Required resource absent or ambiguous; bind explicitly")
        for text in self.project.diagnostics:
            add("ERROR" if "failed" in text or "ambiguous" in text else "WARNING", self.source, text)
        if self.root is None:
            add("ERROR", self.source, "Native DataGx/DataScene root required for portable staging")
        for key, path in self.files.items():
            if not path.is_file() or digest(path.read_bytes()) != self.hashes[key]:
                add("ERROR", key, "Source changed since project was opened; reload before export")
        if self.project.dependencies:
            model_key = self.project.resources.render_dx.relative_to(self.root / 'DataGx').as_posix().casefold() if self.project.resources.render_dx and self.root else None
            if model_key and not any(d.keyword.casefold()=='model' and d.resolved_relative_path and d.resolved_relative_path.casefold()==model_key for d in self.project.dependencies.entries):
                add('ERROR', self.project.dependencies.source, 'HNT does not bind the selected landscape model')
            for dep in self.project.dependencies.entries:
                if dep.status != "resolved":
                    add("ERROR", dep.referenced_value, f"HNT dependency: {dep.status}")
        if self.project.render:
            render = self.project.render
            for error in render.validation_errors: add("ERROR", render.source, error)
            if not all(all(math.isfinite(x) for x in p) for p in render.positions):
                add("ERROR", render.source, "Non-finite vertex coordinates")
            add("UNKNOWN", render.source, "Native draw/geometry budgets need owner runtime qualification")
        if self.editor:
            edited_xml, _ = self.editor.export()
            edited_document = parse_course_xml_bytes(edited_xml)
            for marker_list in edited_document.marker_lists:
                ids = [m.marker_no for m in marker_list.markers]
                if None in ids or len(ids) != len(set(ids)):
                    add('ERROR', marker_list.xml_path, 'Missing or duplicate Marker No within native source list')
            for status in self.editor.area_status:
                if not status.supported:
                    add("ERROR", status.name, "Missing or unsupported Start/Finish area")
            for status in self.editor.marker_list_status:
                if not status.present:
                    add('ERROR', status.name, 'Required native RaceLine/Limit list missing')
                elif not status.supported:
                    add('WARNING', status.name, 'Existing native list is inspect-only; writer binding not supported')
            splits = build_course_race_logic(edited_document).split_times
            ids = [s.split_id for s in splits]
            if None in ids or len(ids) != len(set(ids)):
                add("ERROR", "SplitTime", "Missing or duplicate Split Time ID")
            if ids and sorted(ids) != list(range(len(ids))):
                add("WARNING", "SplitTime", "Non-contiguous Split IDs; native ordering needs review")
            try:
                _, report = self.editor.export()
                for warning in report.warnings: add("WARNING", "RaceTest", warning)
            except ValueError as error:
                add("ERROR", "RaceTest", str(error))
        try:
            bsp = self.collision()
            if not bsp.complete: add("UNKNOWN", "Collision", f"{bsp.trailing_size} bytes after BSP preserved; separate collision structures not interpreted")
            add("UNKNOWN", "Collision", "INSPECT_ONLY: BSP topology edits require a qualified rebuild; no triangle mesh inferred")
        except (ValueError, MasterRallyeError) as error:
            add("ERROR", "Collision", str(error))
        if self.geometry is not None and digest(self.geometry) != self.hashes.get(self.project.resources.render_dx.relative_to(self.root).as_posix()):
            add("WARNING", "Visual Terrain", "Visual positions changed; native BSP and spatial bounds preserved, physics not rebuilt")
        add("UNKNOWN", "SFL", "Source bytes preserved; AI field generation and alternative route choice unqualified")
        return list(dict.fromkeys(findings))

    def export(self, output, *, registry=None, template_race_id=None, name=None):
        """Validate then atomically publish a fresh, reproducible staging tree."""
        findings = self.validate()
        if any(f.severity == "ERROR" for f in findings):
            raise ValueError("Course validation failed: " + "; ".join(f.path + ": " + f.message for f in findings if f.severity == "ERROR"))
        output = Path(output).resolve()
        # Never permit an output inside any input data tree, even a fresh child.
        if output == self.root or output.is_relative_to(self.root) or self.root.is_relative_to(output):
            raise ValueError("Output must be outside the source resource root")
        if output.exists():
            raise FileExistsError("Choose a fresh staging directory")
        payloads = {k: p.read_bytes() for k, p in self.files.items()}
        payloads.update(self.replacements)
        xml_key = self.project.resources.race_test_xml.relative_to(self.root).as_posix()
        payloads[xml_key], edit_report = self.editor.export()
        if self.geometry is not None:
            payloads[self.project.resources.render_dx.relative_to(self.root).as_posix()] = self.geometry
        catalog = copy.deepcopy(registry if registry is not None else self.registry)
        register_new = name is not None
        preserved_race = None
        if catalog is not None and not register_new:
            if self.race_id is None or self.race_id < 39:
                raise ValueError('Opening a stock registry requires a new race name for isolated export')
            preserved_race = next((r for r in catalog['races'] if r['id']==self.race_id),None)
            if preserved_race is None:
                raise ValueError('Saved registration is absent from linked catalog')
            if preserved_race['course'] in {r['course'] for r in catalog['races'][:39]}:
                raise ValueError('Registration shares a stock Course; choose a new race name to isolate its model and resources')
        if catalog is not None and register_new:
            if not name or not re.fullmatch(r"[A-Za-z][A-Za-z0-9_]{0,47}", name):
                raise ValueError("An explicit portable new race name is required")
            templates = [r for r in catalog["races"] if r["id"] == template_race_id]
            if len(templates) != 1:
                raise ValueError("Select one original registry template race")
            row = copy.deepcopy(templates[0]); new_id = len(catalog["races"])
            baseline = copy.deepcopy(catalog['races'][:39])
            course = next(c for c in catalog['courses'] if c['key'] == row['course'])
            actual_model = self.project.resources.render_dx.relative_to(self.root).as_posix()
            if course['model'].casefold() != actual_model.casefold():
                raise ValueError('Registry template course differs from the opened landscape')
            old_folder = self.project.resources.render_dx.parent.relative_to(self.root).as_posix()
            if any(not key.casefold().startswith(old_folder.casefold() + '/') for key in self.replacements):
                raise ValueError('A shared texture draft needs a qualified native binding remap before isolated new-race export')
            new_folder = f'DataGx/Course/{name}'
            new_model = new_folder + '/' + self.project.resources.render_dx.name
            for key, value in list(payloads.items()):
                if key.casefold().startswith(old_folder.casefold() + '/'):
                    payloads[new_folder + key[len(old_folder):]] = value
                    payloads[key] = self.files[key].read_bytes()
            # Bind a separate Course identity; do not change shared stock geometry.
            new_course = dict(key='studio:' + name, folder=new_folder, model=new_model)
            if any(c['key'] == new_course['key'] for c in catalog['courses']):
                raise ValueError('New Course identity already exists')
            catalog['courses'].append(new_course)
            new_scene = f"DataScene/RaceTest/{name}.xml"
            new_hnt = str(Path(new_scene).with_suffix(".hnt")).replace("\\", "/")
            new_sfl = f"DataScene/ICont/{name}.sfl"
            # Edit only the proven AI dataset string via the original lexical spans.
            xml = payloads[xml_key]
            landscape = ET.fromstring(xml)
            names = [v.get('Value') for e in landscape.iter('Egg') if e.get('Name', '').casefold() == 'landscape'
                     for v in e.iter('Value') if v.get('Name') == 'en3d Model Name']
            if len(names) != 1: raise ValueError('Ambiguous landscape model')
            new_native_model = new_model[len('DataGx/'):].rsplit('.', 1)[0].replace('/', '\\')
            old_binding = ('Value="' + names[0] + '"').encode('ascii')
            if xml.count(old_binding) != 1: raise ValueError('Ambiguous lexical landscape binding')
            xml = xml.replace(old_binding, ('Value="' + new_native_model + '"').encode('ascii'), 1)
            matches = list(re.finditer(rb'(<Value\b[^>]*Name="AI DataSet Name"[^>]*Value=")([^"]*)(")', xml))
            if len(matches) != 1:
                raise ValueError("New registration requires exactly one lexical AI dataset binding")
            match = matches[0]
            payloads[new_scene] = xml[:match.start(2)] + ("ICont\\" + name).encode() + xml[match.end(2):]
            payloads[xml_key] = self.project.resources.race_test_xml.read_bytes()
            hnt = self.project.resources.hnt.read_bytes()
            bound_models = 0
            def model_binding(match):
                nonlocal bound_models
                kind = match.group(2).decode('ascii').casefold()
                value = match.group(3).decode('latin-1').replace('\\', '/')
                expected = actual_model[len('DataGx/'):].rsplit('.', 1)[0]
                native_folder = old_folder[len('DataGx/'):]
                if kind == 'model' and value.casefold() == expected.casefold():
                    replacement = new_native_model
                    bound_models += 1
                elif kind in ('texture', 'fstexture') and value.casefold().startswith(native_folder.casefold() + '/'):
                    replacement = (new_folder[len('DataGx/'):] + value[len(native_folder):]).replace('/', '\\')
                else:
                    return match.group(0)
                return match.group(1) + replacement.encode('ascii') + match.group(4)
            payloads[new_hnt] = re.sub(rb'((Model|Texture|FSTexture)\s*\[)([^\]]*)(\])', model_binding, hnt, flags=re.IGNORECASE)
            if not bound_models: raise ValueError('No exact landscape Model binding in HNT')
            payloads[new_sfl] = self.project.resources.sfl.read_bytes()
            row.update(id=new_id, course=new_course['key'], scene=new_scene, icont=new_sfl, title=name, modes=["QuickRace"],
                       progress_key=name, menu={"group": 0, "position": 3 + new_id - 39, "flag_frame": row.get("menu", {}).get("flag_frame", 0), "screenshot_pair": row.get("menu", {}).get("screenshot_pair", 0)})
            row.pop("prepare_variant", None); row["native_fields"][0] = new_id
            catalog["races"].append(row)
            from .course_registry import validate_manifest
            validate_manifest(catalog, baseline)
            xml_key = new_scene
        output.parent.mkdir(parents=True, exist_ok=True)
        temporary = Path(tempfile.mkdtemp(prefix=".course-studio-", dir=output.parent))
        try:
            rows = []
            for key, payload in sorted(payloads.items()):
                target = temporary / "resource-root" / key
                target.parent.mkdir(parents=True, exist_ok=True); target.write_bytes(payload)
                rows.append({"path": key, "sha256": digest(payload), "source_sha256": self.hashes.get(key), "changed": digest(payload) != self.hashes.get(key)})
            bindings = {k: "resource-root/" + p.relative_to(self.root).as_posix() for k in KINDS if (p := getattr(self.project.resources, k))}
            bindings["race_test_xml"] = "resource-root/" + xml_key
            if catalog is not None and register_new:
                for kind in ('render_dx', 'source_txt', 'source_gxm'):
                    if kind in bindings:
                        bindings[kind] = 'resource-root/' + new_folder + '/' + Path(bindings[kind]).name
                bindings["hnt"] = "resource-root/" + new_hnt
                bindings["sfl"] = "resource-root/" + new_sfl
            if catalog is not None:
                (temporary / "courses.json").write_bytes(encoded(catalog))
            if preserved_race is not None:
                course = next(c for c in catalog['courses'] if c['key']==preserved_race['course'])
                explicit = {preserved_race['scene'].casefold(),preserved_race['icont'].casefold(),str(Path(preserved_race['scene']).with_suffix('.hnt')).replace('\\','/').casefold()}
                override_keys = {k for k in payloads if k.casefold() in explicit or k.casefold().startswith(course['folder'].casefold() + '/')}
            else:
                override_keys = {k for k in payloads if catalog is None or k not in self.files}
            overrides = {k: str(output / 'resource-root' / k) for k in sorted(override_keys)}
            (temporary / 'resource-overrides.json').write_bytes(encoded(overrides))
            manifest = {"schema": SCHEMA, "entry": "resource-root/" + xml_key, "resource_root": "resource-root", "resources": bindings,
                        "support": SUPPORT, "status": "OFFLINE_VALIDATED_RUNTIME_NOT_TESTED", "findings": [asdict(f) for f in findings],
                        "files": rows, "race_logic": edit_report.to_dict()}
            manifest['marker_builder'] = self.structural_audit
            manifest['scene_features'] = self.feature_metadata
            manifest['versions'] = {'course_dx_revision':self.project.render.revision,'workflow':'COURSE-VIS1'}
            if catalog is not None:
                manifest['registry'] = {'manifest':'courses.json','race_id':new_id if register_new else self.race_id}
            manifest['provenance'] = {'input':str(self.source),'input_sha256':digest(self.source.read_bytes()) if self.source.is_file() else None,
                                      'source_kind':'manifest' if self.source.suffix.lower()=='.json' else 'native resource selection'}
            if self.editor_routes:
                manifest['editor_routes'] = 'editor-routes.json'
                (temporary / 'editor-routes.json').write_bytes(encoded({'schema':'mr-course-neutral-routes/1','routes':self.editor_routes,
                    'native_ai_selection':'UNKNOWN','player_region_is_independent_of_ai_line':True}))
            # Absolute source paths are provenance only, not resolution inputs.
            (temporary / "course-studio.json").write_bytes(encoded(manifest))
            # Reopen before publication so incomplete output is never presented as success.
            reopened = CourseStudio(temporary / "course-studio.json")
            if any(f.severity == "ERROR" for f in reopened.validate()):
                raise ValueError("Staged Course failed re-open validation")
            temporary.rename(output)
        except Exception:
            if temporary.resolve().parent != output.parent or not temporary.name.startswith('.course-studio-'):
                raise RuntimeError('Unexpected staging cleanup path')
            shutil.rmtree(temporary)
            raise
        return manifest


def bsp_ray_intervals(bsp, origin, direction, start, end):
    """Exact plane partition intervals along a ray; no surface reconstruction."""
    pending = [(bsp.root_index, float(start), float(end))]
    result = []
    while pending:
        index, lo, hi = pending.pop()
        node = bsp.nodes[index]
        if node.optional_record is None:
            if node.field_0 not in (1, 0xFFFFFFFF):
                raise ValueError("Unqualified BSP leaf encoding")
            result.append((lo, hi, node.field_0 == 0xFFFFFFFF, index)); continue
        if node.first_child_index is None or node.next_sibling_index is None:
            raise ValueError("Incomplete binary BSP node")
        a, b, c, d = node.optional_record.values
        value = a * origin[0] + b * origin[1] + c * origin[2] + d
        slope = a * direction[0] + b * direction[1] + c * direction[2]
        if abs(slope) < 1e-12:
            pending.append((node.first_child_index if value <= 0 else node.next_sibling_index, lo, hi)); continue
        cut = -value / slope
        for child, left, right in ((node.first_child_index, lo if slope > 0 else max(lo, cut), min(hi, cut) if slope > 0 else hi),
                                   (node.next_sibling_index, max(lo, cut) if slope > 0 else lo, hi if slope > 0 else min(hi, cut))):
            if right > left: pending.append((child, left, right))
    return sorted(result)
