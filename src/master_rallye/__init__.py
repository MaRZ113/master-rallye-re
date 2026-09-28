"""Master Rallye clean-room asset extraction library.

Public helpers are loaded on demand so importing one focused submodule does not
eagerly import the full research library.
"""
from __future__ import annotations

from importlib import import_module
from importlib.util import find_spec
from .version import __version__

_EXPORTS = {
    "BoundsError": "errors", "ExportError": "errors", "DxWriteError": "errors",
    "CollisionWriteError": "errors", "FormatError": "errors",
    "MasterRallyeError": "errors", "UnknownRecordTagError": "errors",
    "DxSpatialBounds1339": "bounds", "parse_bounds1339": "bounds",
    "compute_bounds1339": "bounds", "scale_tag101": "collision_scale",
    "scale_dx_collision": "collision_scale", "VehicleProject": "vehicle_project",
    "validate_vehicle": "vehicle_project", "build_vehicle_mod": "vehicle_project",
    "parse_dx": "dx", "parse_dx_bytes": "dx", "patch_dx_positions": "dx_writer",
    "write_dx_positions": "dx_writer", "audit_binary_diff": "dx_writer",
    "parse_collision_sections": "collision", "serialize_tag101": "collision_writer",
    "replace_dx_tag101": "collision_writer", "translate_tag101": "collision_writer",
    "patch_dx_collision_translation": "collision_writer",
    "write_dx_collision_translation": "collision_writer",
    "SOURCE_IDENTICAL": "authoring", "POSITIONS_ONLY_CHANGED": "authoring",
    "UNSUPPORTED_TOPOLOGY_CHANGED": "authoring", "INVALID_PROVENANCE": "authoring",
    "provenance_fingerprint": "authoring", "validate_authoring_state": "authoring",
    "parse_dxt": "dxt", "parse_dxt_bytes": "dxt", "decode_rgba_pixels": "dxt",
    "encode_dxt_pixels": "dxt", "replace_dxt_pixels": "dxt",
    "parse_sidecar": "sidecar", "resolve_sidecar": "sidecar",
}

__all__ = [
    name for name, module_name in _EXPORTS.items()
    if find_spec(f"{__name__}.{module_name}") is not None
]


def __getattr__(name: str):
    module_name = _EXPORTS.get(name)
    if module_name is None:
        raise AttributeError(f"module {__name__!r} has no attribute {name!r}")
    value = getattr(import_module(f".{module_name}", __name__), name)
    globals()[name] = value
    return value
