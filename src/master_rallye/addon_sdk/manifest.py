"""Strict manifest loading, validation and deterministic physical-ID resolution."""
from __future__ import annotations

import hashlib
import json
import math
import re
import struct
from pathlib import Path, PurePosixPath
from typing import Any, Iterable


class AddonValidationError(ValueError):
    """Input failed the fail-closed generic addon contract."""


_FAMILY = re.compile(r"^[A-Za-z][A-Za-z0-9_]{0,63}$")
_SHA256 = re.compile(r"^[0-9a-f]{64}$")
_MODES = ("quick_race", "rallye_cup", "master_rallye", "invitation", "challenge", "practice")
_STOCK_CLASS_MAP = {
    "T1": list(range(0, 7)),
    "T2": list(range(7, 14)),
    "T3": list(range(14, 26)),
}
_REQUIRED_TOP = {
    "manifest_version", "addon_id", "description", "vehicle_class", "physical_id", "class_local_placement",
    "identity", "assets", "frontend", "race_colour_rgba", "unlock", "audio", "ai_eligibility", "results",
}


def _object_pairs_no_duplicates(pairs: list[tuple[str, Any]]) -> dict[str, Any]:
    output: dict[str, Any] = {}
    for key, value in pairs:
        if key in output:
            raise AddonValidationError(f"duplicate JSON key: {key}")
        output[key] = value
    return output


def read_json(path: Path) -> tuple[dict[str, Any], bytes]:
    path = Path(path)
    raw = path.read_bytes()
    try:
        value = json.loads(raw.decode("utf-8-sig"), object_pairs_hook=_object_pairs_no_duplicates)
    except (UnicodeDecodeError, json.JSONDecodeError) as exc:
        raise AddonValidationError(f"invalid UTF-8 JSON in {path}: {exc}") from exc
    if not isinstance(value, dict):
        raise AddonValidationError(f"top-level JSON value must be an object: {path}")
    return value, raw


def load_capabilities(path: Path) -> tuple[dict[str, Any], str]:
    value, raw = read_json(path)
    digest = hashlib.sha256(raw).hexdigest()
    if value.get("capability_version") != 1:
        raise AddonValidationError("unsupported capability profile version")
    if not _SHA256.fullmatch(str(value.get("retail_exe_sha256", ""))):
        raise AddonValidationError("capability profile must pin a lowercase retail EXE SHA256")
    for key in ("reserved_stock_ids", "supported_addon_physical_ids", "runtime_qualified_addon_ids"):
        rows = value.get(key)
        if not isinstance(rows, list) or any(type(item) is not int or item < 0 for item in rows):
            raise AddonValidationError(f"capability {key} must be a list of non-negative integers")
        if len(rows) != len(set(rows)):
            raise AddonValidationError(f"capability {key} contains duplicates")
    supported_ids = set(value["supported_addon_physical_ids"])
    reserved_ids = set(value["reserved_stock_ids"])
    runtime_ids = set(value["runtime_qualified_addon_ids"])
    if supported_ids & reserved_ids:
        raise AddonValidationError("capability addon-ID set overlaps reserved stock IDs")
    if not runtime_ids <= supported_ids:
        raise AddonValidationError("runtime-qualified IDs must be a subset of supported addon IDs")
    slots = value.get("qualified_addon_slots")
    if not isinstance(slots, list):
        raise AddonValidationError("capability qualified_addon_slots must be an explicit slot list")
    slot_ids: set[int] = set()
    slot_keys: set[tuple[str, int]] = set()
    for slot in slots:
        if not isinstance(slot, dict) or set(slot) != {"physical_id", "vehicle_class", "class_local_index"}:
            raise AddonValidationError("each qualified addon slot needs physical_id, vehicle_class and class_local_index")
        physical_id = slot["physical_id"]
        class_name = slot["vehicle_class"]
        local_index = slot["class_local_index"]
        if type(physical_id) is not int or physical_id < 0:
            raise AddonValidationError("qualified addon slot physical_id must be a non-negative integer")
        if class_name not in _STOCK_CLASS_MAP:
            raise AddonValidationError("qualified addon slot has an unsupported vehicle_class")
        if type(local_index) is not int or local_index < len(_STOCK_CLASS_MAP[class_name]):
            raise AddonValidationError("qualified addon slot must append after the stock class map")
        if physical_id not in supported_ids or physical_id in reserved_ids or physical_id in slot_ids:
            raise AddonValidationError("qualified addon slot physical ID is unsupported, reserved or duplicated")
        key = (class_name, local_index)
        if key in slot_keys:
            raise AddonValidationError("qualified addon class/local slot is duplicated")
        slot_ids.add(physical_id)
        slot_keys.add(key)
    if slot_ids != supported_ids:
        raise AddonValidationError("qualified_addon_slots must map every supported physical ID exactly once")
    for class_name, stock in _STOCK_CLASS_MAP.items():
        locals_ = sorted(index for name, index in slot_keys if name == class_name)
        if locals_ != list(range(len(stock), len(stock) + len(locals_))):
            raise AddonValidationError("qualified addon slots must append contiguously after the stock class map")
    qualified_profiles = value.get("runtime_qualified_addon_profiles")
    if not isinstance(qualified_profiles, list):
        raise AddonValidationError("capability runtime_qualified_addon_profiles must be an explicit identity list")
    profile_ids: set[int] = set()
    profile_fields = {
        "physical_id", "vehicle_class", "class_local_index", "runtime_family", "model_family",
        "wheel_family", "physics_family", "manufacturer", "model", "combined", "results_display_name",
        "audio_profile_id", "unlock_policy", "unlock_stock_vehicle_id",
    }
    for profile in qualified_profiles:
        if not isinstance(profile, dict) or set(profile) != profile_fields:
            raise AddonValidationError("each runtime-qualified identity profile has an invalid field set")
        physical_id = profile["physical_id"]
        slot = next((row for row in slots if row["physical_id"] == physical_id), None)
        if (type(physical_id) is not int or physical_id not in runtime_ids or physical_id in profile_ids
                or slot is None or profile["vehicle_class"] != slot["vehicle_class"]
                or profile["class_local_index"] != slot["class_local_index"]):
            raise AddonValidationError("runtime-qualified identity profile does not match a unique runtime-qualified slot")
        profile_ids.add(physical_id)
        for key in ("runtime_family", "model_family", "wheel_family"):
            _valid_family(profile[key], f"runtime_qualified_addon_profiles.{key}")
        _valid_family(profile["physics_family"].removeprefix("Vehicles/"),
                      "runtime_qualified_addon_profiles.physics_family")
        if not profile["physics_family"].startswith("Vehicles/"):
            raise AddonValidationError("runtime-qualified physics_family must be a Vehicles/<family> path")
        for key in ("manufacturer", "model", "combined", "results_display_name"):
            if not isinstance(profile[key], str) or not profile[key].isascii() or not profile[key].strip():
                raise AddonValidationError(f"runtime-qualified profile {key} must be non-empty ASCII text")
        if (type(profile["audio_profile_id"]) is not int or not 0 <= profile["audio_profile_id"] <= 24
                or profile["unlock_policy"] not in {"always_available", "mirror_stock_unlock"}
                or (profile["unlock_policy"] == "mirror_stock_unlock"
                    and (type(profile["unlock_stock_vehicle_id"]) is not int
                         or not 0 <= profile["unlock_stock_vehicle_id"] <= 25))):
            raise AddonValidationError("runtime-qualified profile contains an unsupported audio or unlock policy")
    if profile_ids != runtime_ids:
        raise AddonValidationError("runtime-qualified identity profiles must cover the runtime-qualified ID list")
    if not isinstance(value.get("stock_class_map"), dict) or set(value["stock_class_map"]) != set(_STOCK_CLASS_MAP):
        raise AddonValidationError("capability profile must define stock T1/T2/T3 class maps")
    for class_name, expected in _STOCK_CLASS_MAP.items():
        actual = value["stock_class_map"].get(class_name)
        if actual != expected:
            raise AddonValidationError(f"capability stock class map {class_name} differs from audited base")
    for key in ("class_slot_limits", "registry_layout"):
        if not isinstance(value.get(key), dict):
            raise AddonValidationError(f"capability {key} must be an object")
    if any(class_name not in value["class_slot_limits"] or type(value["class_slot_limits"][class_name]) is not int
           for class_name in _STOCK_CLASS_MAP):
        raise AddonValidationError("capability class slot limits are incomplete")
    if any(value["class_slot_limits"][name] < len(rows) for name, rows in value["stock_class_map"].items()):
        raise AddonValidationError("capability class slot limit is smaller than its stock class map")
    if type(value.get("retail_exe_size")) is not int or value["retail_exe_size"] <= 0:
        raise AddonValidationError("capability retail_exe_size must be a positive integer")
    data_sha = value.get("retail_data_sma_sha256")
    data_size = value.get("retail_data_sma_size")
    if (data_sha is None) != (data_size is None):
        raise AddonValidationError("capability retail_data_sma_sha256 and retail_data_sma_size must be supplied together")
    if data_sha is not None and (not _SHA256.fullmatch(data_sha)
                                 or type(data_size) is not int or data_size <= 0):
        raise AddonValidationError("capability retail Data.sma identity requires lowercase SHA256 and positive size")
    layout = value["registry_layout"]
    for key in ("header_bytes", "vehicle_record_stride", "racetest_count", "racetest_stride"):
        if type(layout.get(key)) is not int or layout[key] <= 0:
            raise AddonValidationError(f"invalid registry layout field {key}")
    return value, digest


def load_manifests(paths: Iterable[Path]) -> tuple[list[dict[str, Any]], list[dict[str, str]]]:
    manifests: list[dict[str, Any]] = []
    provenance: list[dict[str, str]] = []
    for path in paths:
        value, raw = read_json(path)
        manifests.append(value)
        provenance.append({"path_label": Path(path).name, "sha256": hashlib.sha256(raw).hexdigest()})
    if not manifests:
        raise AddonValidationError("at least one addon manifest is required")
    return manifests, provenance


def _need_object(value: Any, name: str, keys: set[str]) -> dict[str, Any]:
    if not isinstance(value, dict):
        raise AddonValidationError(f"{name} must be an object")
    missing = keys - set(value)
    extra = set(value) - keys
    if missing or extra:
        raise AddonValidationError(f"{name} keys: missing={sorted(missing)}, unsupported={sorted(extra)}")
    return value


def _valid_family(value: Any, label: str) -> str:
    if not isinstance(value, str) or not _FAMILY.fullmatch(value):
        raise AddonValidationError(f"{label} must be a safe resource-family identifier")
    return value


def _validate_one(manifest: dict[str, Any]) -> None:
    if not isinstance(manifest, dict):
        raise AddonValidationError("each manifest must be an object")
    if set(manifest) != _REQUIRED_TOP:
        raise AddonValidationError(
            f"manifest keys: missing={sorted(_REQUIRED_TOP - set(manifest))}, "
            f"unsupported={sorted(set(manifest) - _REQUIRED_TOP)}"
        )
    if type(manifest["manifest_version"]) is not int or manifest["manifest_version"] != 1:
        raise AddonValidationError("manifest_version must be integer 1")
    addon_id = manifest["addon_id"]
    if not isinstance(addon_id, str) or not re.fullmatch(r"[a-z0-9][a-z0-9._-]{1,63}", addon_id):
        raise AddonValidationError("addon_id must be a lowercase stable identifier (2..64 chars)")
    if not isinstance(manifest["description"], str) or not manifest["description"].strip():
        raise AddonValidationError("description must be a non-empty authorship/provenance note")
    class_name = manifest["vehicle_class"]
    if class_name not in _STOCK_CLASS_MAP:
        raise AddonValidationError("vehicle_class must be T1, T2 or T3")
    physical = _need_object(manifest["physical_id"], "physical_id", {"policy", "value"})
    if physical["policy"] == "explicit":
        if type(physical["value"]) is not int or physical["value"] < 0:
            raise AddonValidationError("explicit physical_id.value must be a non-negative integer")
    elif physical["policy"] == "auto":
        if physical["value"] is not None:
            raise AddonValidationError("auto physical ID must use value=null")
    else:
        raise AddonValidationError("physical_id.policy must be explicit or auto")
    if manifest["class_local_placement"] != "append":
        raise AddonValidationError("V1 class-local placement only supports append")

    identity = _need_object(manifest["identity"], "identity", {
        "runtime_family", "model_family", "wheel_family", "physics_family",
    })
    for key in ("runtime_family", "model_family", "wheel_family"):
        _valid_family(identity[key], f"identity.{key}")
    physics = identity["physics_family"]
    if not isinstance(physics, str) or not physics.startswith("Vehicles/"):
        raise AddonValidationError("identity.physics_family must be a Vehicles/<family> path")
    _valid_family(physics.split("/", 1)[1], "identity.physics_family suffix")

    assets = _need_object(manifest["assets"], "assets", {"model_package_root", "required_roles"})
    model_root = assets["model_package_root"]
    expected_root = f"DataGx/Vehicles/{identity['model_family']}"
    if model_root != expected_root:
        raise AddonValidationError(f"model_package_root must match model_family ({expected_root})")
    roles = assets["required_roles"]
    if not isinstance(roles, list) or not all(isinstance(item, str) for item in roles):
        raise AddonValidationError("assets.required_roles must be a string list")
    if not {"car.dx", "complete.dx", "wheel.dx"}.issubset(set(roles)):
        raise AddonValidationError("assets.required_roles must include car.dx, complete.dx and wheel.dx")
    if len({role.casefold() for role in roles}) != len(roles) or any(
            PurePosixPath(role).name != role or role in {".", ".."} for role in roles):
        raise AddonValidationError("asset roles must be unique safe basenames")

    frontend = _need_object(manifest["frontend"], "frontend", {
        "manufacturer", "model", "combined", "stats", "vehicle_select_art", "smallcarsheet",
    })
    for key in ("manufacturer", "model", "combined"):
        if (not isinstance(frontend[key], str) or not frontend[key].strip()
                or not frontend[key].isascii() or "\x00" in frontend[key]):
            raise AddonValidationError(f"frontend.{key} must be a non-empty ASCII display string without NUL")
    stats = frontend["stats"]
    if not isinstance(stats, list) or len(stats) != 4 or any(type(item) is not int or not 0 <= item <= 10 for item in stats):
        raise AddonValidationError("frontend.stats must contain four integer values in 0..10")
    art = _need_object(frontend["vehicle_select_art"], "frontend.vehicle_select_art", {"policy", "frame"})
    if art["policy"] not in {"stock_frame", "project_frame"} or type(art["frame"]) is not int or art["frame"] < 0 or art["policy"] == "project_frame" and art["frame"] > 127:
        raise AddonValidationError("Vehicle Select art must reference stock_frame or a bounded project_frame")
    small = _need_object(frontend["smallcarsheet"], "frontend.smallcarsheet", {"policy", "frame"})
    if small["policy"] not in {"stock_frame", "project_frame"} or type(small["frame"]) is not int or small["frame"] < 0 or small["policy"] == "project_frame" and small["frame"] > 127:
        raise AddonValidationError("SmallCarSheet must reference stock_frame or a bounded project_frame")

    colour = manifest["race_colour_rgba"]
    if not isinstance(colour, list) or len(colour) != 4 or any(
            isinstance(v, bool) or not isinstance(v, (float, int)) or not math.isfinite(float(v)) or not 0 <= v <= 1
            for v in colour):
        raise AddonValidationError("race_colour_rgba must be four finite normalized numbers")

    unlock = manifest["unlock"]
    if not isinstance(unlock, dict):
        raise AddonValidationError("unlock must be an object")
    if unlock.get("policy") == "always_available":
        _need_object(unlock, "unlock", {"policy"})
    elif unlock.get("policy") == "mirror_stock_unlock":
        _need_object(unlock, "unlock", {"policy", "stock_vehicle_id"})
        value = unlock["stock_vehicle_id"]
        if type(value) is not int or not 0 <= value <= 25:
            raise AddonValidationError("mirror_stock_unlock must name a reserved stock vehicle 0..25")
    else:
        raise AddonValidationError("unlock policy is unsupported; V1 supports always_available or mirror_stock_unlock")

    audio = _need_object(manifest["audio"], "audio", {"policy", "stock_audio_profile_id"})
    if audio["policy"] != "stock_profile":
        raise AddonValidationError("V1 audio policy must be stock_profile")
    audio_id = audio["stock_audio_profile_id"]
    if type(audio_id) is not int or not 0 <= audio_id <= 24:
        raise AddonValidationError("stock_audio_profile_id must be a tuned retail profile ID 0..24")

    ai = _need_object(manifest["ai_eligibility"], "ai_eligibility", set(_MODES))
    for mode in _MODES:
        row = ai[mode]
        if not isinstance(row, dict) or type(row.get("enabled")) is not bool:
            raise AddonValidationError(f"ai_eligibility.{mode}.enabled must be boolean")
        if row["enabled"]:
            if set(row) != {"enabled", "boundary", "pool"}:
                raise AddonValidationError(f"enabled AI mode {mode} requires exactly boundary and pool")
            if mode == "quick_race" and (row["boundary"], row["pool"]) != ("new_race", "dynamic_class"):
                raise AddonValidationError("Quick Race V1 boundary must be new_race/dynamic_class")
            if mode == "rallye_cup" and (row["boundary"], row["pool"]) != ("new_cup", "dynamic_class"):
                raise AddonValidationError("Rallye Cup V1 boundary must be new_cup/dynamic_class")
            if mode == "master_rallye" and (row["boundary"], row["pool"]) != ("new_competition", "dynamic_class"):
                raise AddonValidationError("Master Rallye V1 boundary must be new_competition/dynamic_class")
            if mode == "invitation" and (class_name != "T3" or row["pool"] != "ordinary_t3"):
                raise AddonValidationError("Invitation eligibility requires explicit ordinary_t3 qualification")
            if mode in {"challenge", "practice"}:
                raise AddonValidationError(f"automatic AI eligibility is unsupported for {mode}")
        else:
            if "reason" not in row or set(row) != {"enabled", "reason"} or not isinstance(row["reason"], str) or not row["reason"]:
                raise AddonValidationError(f"disabled AI mode {mode} requires a concise reason")
    if ai["challenge"].get("enabled"):
        raise AddonValidationError("Challenge remains authored/event-specific in V1")
    if ai["practice"].get("enabled"):
        raise AddonValidationError("Practice has no qualified stock AI pool in V1")

    results = _need_object(manifest["results"], "results", {"policy", "display_name"})
    if (results["policy"] != "fixed" or not isinstance(results["display_name"], str)
            or not results["display_name"].strip() or not results["display_name"].isascii()
            or "\x00" in results["display_name"]):
        raise AddonValidationError("V1 Results policy must provide a fixed non-empty ASCII display_name without NUL")


def validate_manifests(manifests: list[dict[str, Any]], capabilities: dict[str, Any]) -> dict[str, Any]:
    """Validate and resolve IDs/class ordinals, returning a stable semantic plan."""
    if not manifests:
        raise AddonValidationError("at least one addon manifest is required")
    for manifest in manifests:
        _validate_one(manifest)

    sorted_manifests = sorted(manifests, key=lambda item: item["addon_id"])
    addon_ids = [item["addon_id"] for item in sorted_manifests]
    if len(addon_ids) != len(set(addon_ids)):
        raise AddonValidationError("duplicate addon_id")

    supported = set(capabilities["supported_addon_physical_ids"])
    reserved = set(capabilities["reserved_stock_ids"])
    slots_by_class: dict[str, list[dict[str, Any]]] = {name: [] for name in _STOCK_CLASS_MAP}
    for slot in capabilities["qualified_addon_slots"]:
        slots_by_class[slot["vehicle_class"]].append(slot)
    for rows in slots_by_class.values():
        rows.sort(key=lambda row: (row["class_local_index"], row["physical_id"]))
    resolved: dict[str, int] = {}
    used: set[int] = set()
    slot_by_physical = {row["physical_id"]: row for row in capabilities["qualified_addon_slots"]}
    for item in sorted_manifests:
        physical = item["physical_id"]
        if physical["policy"] != "explicit":
            continue
        value = physical["value"]
        if value in reserved:
            raise AddonValidationError(f"physical ID {value} is reserved for stock")
        if value not in supported:
            raise AddonValidationError(f"physical ID {value} is outside this target's declared addon capability set")
        if value in used:
            raise AddonValidationError(f"physical ID collision: {value}")
        resolved[item["addon_id"]] = value
        used.add(value)
    for item in sorted_manifests:
        if item["physical_id"]["policy"] != "explicit":
            continue
        value = resolved[item["addon_id"]]
        slot = slot_by_physical[value]
        if item["vehicle_class"] != slot["vehicle_class"]:
            raise AddonValidationError(
                f"physical ID {value} is qualified for {slot['vehicle_class']} local{slot['class_local_index']}, "
                f"not {item['vehicle_class']}"
            )
    for item in sorted_manifests:
        if item["physical_id"]["policy"] == "explicit":
            continue
        available_slot = next((slot for slot in slots_by_class[item["vehicle_class"]]
                               if slot["physical_id"] not in used), None)
        if available_slot is None:
            raise AddonValidationError(
                f"{item['vehicle_class']}_ADDON_SLOT_UNAVAILABLE: class-local capacity has no qualified physical slot remaining"
            )
        resolved[item["addon_id"]] = available_slot["physical_id"]
        used.add(available_slot["physical_id"])

    identity_keys = ("runtime_family", "model_family", "wheel_family", "physics_family")
    identity_owners: dict[tuple[str, str], str] = {}
    resource_owners: dict[str, str] = {}
    class_map = {key: list(value) for key, value in capabilities["stock_class_map"].items()}
    planned: list[dict[str, Any]] = []
    # Explicit assignments can be presented in any addon-name order. Build the
    # class table in slot order, while retaining deterministic auto allocation.
    slot_order = sorted(sorted_manifests, key=lambda item: (
        item['vehicle_class'], slot_by_physical[resolved[item['addon_id']]]['class_local_index']))
    for item in slot_order:
        addon_id = item["addon_id"]
        class_name = item["vehicle_class"]
        physical_id = resolved[addon_id]
        for key in identity_keys:
            normalized = item["identity"][key].casefold()
            previous = identity_owners.get((key, normalized))
            if previous and previous != addon_id:
                raise AddonValidationError(f"{key} collision between {previous} and {addon_id}")
            identity_owners[(key, normalized)] = addon_id
        model_root = item["assets"]["model_package_root"]
        for role in item["assets"]["required_roles"]:
            path = f"{model_root}/{role}".casefold()
            previous = resource_owners.get(path)
            if previous:
                raise AddonValidationError(f"resource-name collision at {path}: {previous} and {addon_id}")
            resource_owners[path] = addon_id
        if physical_id in {entry for values in class_map.values() for entry in values}:
            raise AddonValidationError(f"physical ID {physical_id} already appears in a stock class map")
        slot = slot_by_physical[physical_id]
        local_index = slot["class_local_index"]
        slot_limit = capabilities["class_slot_limits"][class_name]
        if local_index >= slot_limit:
            raise AddonValidationError(f"{class_name} class-local capacity exceeded by {addon_id}")
        if local_index != len(class_map[class_name]):
            raise AddonValidationError(
                f"{class_name}_ADDON_SLOT_ORDER_UNSUPPORTED: qualified slot local{local_index} cannot be inserted after the current collection"
            )
        class_map[class_name].append(physical_id)
        planned.append({
            "addon_id": addon_id,
            "physical_id": physical_id,
            "vehicle_class": class_name,
            "class_local_index": local_index,
            "identity": dict(item["identity"]),
            "assets": dict(item["assets"]),
            "frontend": dict(item["frontend"]),
            "race_colour_rgba": [float(value) for value in item["race_colour_rgba"]],
            "race_colour_rgba_f32le_hex": struct.pack("<4f", *item["race_colour_rgba"]).hex(),
            "unlock": dict(item["unlock"]),
            "audio": dict(item["audio"]),
            "ai_eligibility": {mode: dict(item["ai_eligibility"][mode]) for mode in _MODES},
            "results": dict(item["results"]),
        })

    # Preserve V1 serialization order for existing author projects, including
    # the frozen Subaru plan, while class insertion above follows slot order.
    planned.sort(key=lambda row: row['addon_id'])
    highest = max([*reserved, *used], default=max(reserved, default=-1))
    layout = capabilities["registry_layout"]
    count = highest + 1
    records_end = layout["header_bytes"] + count * layout["vehicle_record_stride"]
    racetest_bytes = layout["racetest_count"] * layout["racetest_stride"]
    resolved_class_map = {key: list(value) for key, value in class_map.items()}
    reverse = {str(physical): {"vehicle_class": class_name, "class_local_index": local}
               for class_name, values in resolved_class_map.items() for local, physical in enumerate(values)}
    return {
        "plan_version": 1,
        "build_target": {
            "profile_id": capabilities["profile_id"],
            "retail_exe_sha256": capabilities["retail_exe_sha256"],
            "runtime_deployment": "NOT_IMPLEMENTED_FAIL_CLOSED",
        },
        "evidence_boundary": {
            "runtime_qualified_addon_ids": sorted(capabilities["runtime_qualified_addon_ids"]),
            "resolved_addon_ids_runtime_qualified": all(value in capabilities["runtime_qualified_addon_ids"] for value in used),
            "compiler_output_is_offline_plan": True,
        },
        "addons": planned,
        "class_mapping": {
            "class_to_physical_ids": resolved_class_map,
            "physical_id_to_class_local": reverse,
            "ordering_policy": "APPEND_TO_CLASS",
        },
        "registry_layout": {
            "record_count": count,
            "vehicle_record_base": layout["header_bytes"],
            "vehicle_record_stride": layout["vehicle_record_stride"],
            "race_test_base": records_end,
            "race_test_count": layout["racetest_count"],
            "race_test_stride": layout["racetest_stride"],
            "allocation_size": records_end + racetest_bytes,
        },
        "unsupported": {
            "runtime_execution": "no unchanged-EXE external loader is implemented or qualified",
            "custom_ordering": "deferred",
            "unqualified_physical_ids": sorted(value for value in used if value not in capabilities["runtime_qualified_addon_ids"]),
        },
    }


def classify_runtime_identity(addon: dict[str, Any], capabilities: dict[str, Any]) -> dict[str, Any]:
    """Separate a runtime-qualified physical slot from its exact qualified identity profile."""
    physical_id = addon.get("physical_id")
    slot = next((row for row in capabilities["qualified_addon_slots"]
                 if row["physical_id"] == physical_id), None)
    identity = addon.get("identity", {})
    frontend = addon.get("frontend", {})
    unlock = addon.get("unlock", {})
    audio = addon.get("audio", {})
    results = addon.get("results", {})
    candidate = {
        "physical_id": physical_id,
        "vehicle_class": addon.get("vehicle_class"),
        "class_local_index": addon.get("class_local_index"),
        "runtime_family": identity.get("runtime_family"),
        "model_family": identity.get("model_family"),
        "wheel_family": identity.get("wheel_family"),
        "physics_family": identity.get("physics_family"),
        "manufacturer": frontend.get("manufacturer"),
        "model": frontend.get("model"),
        "combined": frontend.get("combined"),
        "results_display_name": results.get("display_name"),
        "audio_profile_id": audio.get("stock_audio_profile_id"),
        "unlock_policy": unlock.get("policy"),
        "unlock_stock_vehicle_id": unlock.get("stock_vehicle_id"),
    }
    qualified = next((row for row in capabilities["runtime_qualified_addon_profiles"]
                      if row["physical_id"] == physical_id and row == candidate), None)
    return {
        "physical_slot_runtime_qualified": physical_id in capabilities["runtime_qualified_addon_ids"],
        "exact_identity_runtime_qualified": qualified is not None,
        "identity_status": "EXACT_RUNTIME_QUALIFIED_PROFILE" if qualified else "IDENTITY_NOT_RUNTIME_QUALIFIED",
    }


def canonical_json(value: Any) -> bytes:
    return (json.dumps(value, sort_keys=True, ensure_ascii=False, indent=2, allow_nan=False) + "\n").encode("utf-8")
