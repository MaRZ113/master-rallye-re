"""Read-only RaceTest XML marker overlays for imported course scenes."""
from __future__ import annotations

import hashlib
import json
from pathlib import Path

import bpy
from bpy.props import StringProperty
from bpy_extras.io_utils import ImportHelper

from ..blender_mesh import create_collection
from ..library import parse_course_xml, position_to_blender


def _contains_object(collection, target):
    if target is None:
        return False
    if target.name in collection.objects:
        return True
    return any(_contains_object(child, target) for child in collection.children)


class IMPORT_SCENE_OT_master_rallye_course_xml_markers(bpy.types.Operator, ImportHelper):
    bl_idname = "import_scene.master_rallye_course_xml_markers"
    bl_label = "Import RaceTest XML Markers"
    bl_description = "Add the explicit RaceTest XML Marker Pos records as a read-only course overlay"
    bl_options = {"REGISTER", "UNDO"}

    filename_ext = ".xml"
    filter_glob: StringProperty(default="*.xml", options={"HIDDEN"})

    def execute(self, context):
        source = Path(self.filepath).resolve()
        try:
            document = parse_course_xml(source)
            positioned = [marker for marker in document.markers if marker.position is not None]
            if not positioned:
                raise ValueError("XML contains no Marker records with a valid Marker Pos Vector3")

            candidates = [
                collection
                for collection in bpy.data.collections
                if collection.get("mr_resource_kind") == "course"
                and str(collection.get("mr_course_identity", "")).casefold().endswith(source.stem.casefold())
            ]
            active_matches = [
                collection for collection in candidates
                if _contains_object(collection, context.object)
            ]
            if len(active_matches) == 1:
                root = active_matches[0]
            elif len(candidates) == 1:
                root = candidates[0]
            elif len(candidates) > 1:
                raise ValueError(
                    f"multiple imported course collections match {source.stem!r}; select one of their course meshes first"
                )
            else:
                root = bpy.data.collections.get(f"Master Rallye Course - {source.stem}")
            root_name = f"Master Rallye Course - {source.stem}"
            if root is None:
                root = create_collection(root_name)
                root["mr_resource_kind"] = "course"
                root["mr_course_identity"] = source.stem
                root["mr_read_only"] = True
                root["mr_import_note"] = "Created for XML marker diagnostics; course render DX not imported"
            elif root.get("mr_resource_kind") != "course":
                raise ValueError(f"collection {root_name!r} exists but is not marked as a course")

            payload = source.read_bytes()
            source_path = str(source)
            for child in root.children:
                if child.get("mr_xml_source") == source_path:
                    raise ValueError(f"this XML source is already imported under {root.name}")
            overlay = create_collection(f"XML Markers - {source.stem}", root)
            overlay["mr_course_helper_kind"] = "RaceTest XML marker overlay"
            overlay["mr_xml_source"] = source_path
            overlay["mr_xml_sha256"] = hashlib.sha256(payload).hexdigest()
            overlay["mr_marker_count"] = len(positioned)
            overlay["mr_marker_records_with_issues"] = sum(bool(item.issues) for item in document.markers)

            for marker in positioned:
                marker_label = marker.marker_type or "unknown"
                obj = bpy.data.objects.new(
                    f"XML Marker {marker.ordinal:04d} - {marker_label}", None
                )
                overlay.objects.link(obj)
                obj.empty_display_type = "SPHERE"
                obj.empty_display_size = 2.0
                obj.show_in_front = True
                obj.location = position_to_blender(marker.position)
                obj["mr_course_helper_kind"] = "RaceTest XML Marker"
                obj["mr_course_identity"] = source.stem
                obj["mr_xml_source"] = source_path
                obj["mr_marker_ordinal"] = marker.ordinal
                obj["mr_marker_no"] = marker.marker_no or ""
                obj["mr_marker_type"] = marker.marker_type or ""
                obj["mr_source_position_xyz"] = list(marker.position)
                if marker.direction is not None:
                    obj["mr_source_direction_xyz"] = list(marker.direction)
                obj["mr_xml_record_json"] = json.dumps(
                    {
                        "tag": marker.record.tag,
                        "attributes": dict(marker.record.attributes),
                        "values": [
                            {"name": value.name, "type": value.type_name, "value": value.value}
                            for value in marker.record.values
                        ],
                        "issues": list(marker.issues),
                    },
                    ensure_ascii=False,
                    separators=(",", ":"),
                )

            self.report(
                {"WARNING"} if overlay["mr_marker_records_with_issues"] else {"INFO"},
                f"Imported {len(positioned)} XML markers into {root.name}; positions use the shared Blender axis conversion",
            )
            return {"FINISHED"}
        except Exception as error:
            self.report({"ERROR"}, str(error))
            return {"CANCELLED"}
