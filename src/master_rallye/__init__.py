"""Master Rallye clean-room asset extraction research library."""
from .dx import parse_dx, parse_dx_bytes
from .dxt import (
    decode_rgba_pixels,
    encode_dxt_pixels,
    parse_dxt,
    parse_dxt_bytes,
    replace_dxt_pixels,
)
from .dx_writer import audit_binary_diff, patch_dx_positions, write_dx_positions
from .collision import parse_collision_sections
from .collision_writer import (
    patch_dx_collision_translation,
    replace_dx_tag101,
    serialize_tag101,
    translate_tag101,
    write_dx_collision_translation,
)
from .authoring import (
    INVALID_PROVENANCE,
    POSITIONS_ONLY_CHANGED,
    SOURCE_IDENTICAL,
    UNSUPPORTED_TOPOLOGY_CHANGED,
    provenance_fingerprint,
    validate_authoring_state,
)
from .errors import BoundsError, CollisionWriteError, DxWriteError, ExportError, FormatError, MasterRallyeError, UnknownRecordTagError
from .sidecar import parse_sidecar, resolve_sidecar

__all__ = [
    "BoundsError",
    "ExportError",
    "DxWriteError",
    "CollisionWriteError",
    "FormatError",
    "MasterRallyeError",
    "UnknownRecordTagError",
    "parse_dx",
    "parse_dx_bytes",
    "patch_dx_positions",
    "write_dx_positions",
    "audit_binary_diff",
    "parse_collision_sections",
    "serialize_tag101",
    "replace_dx_tag101",
    "translate_tag101",
    "patch_dx_collision_translation",
    "write_dx_collision_translation",
    "SOURCE_IDENTICAL",
    "POSITIONS_ONLY_CHANGED",
    "UNSUPPORTED_TOPOLOGY_CHANGED",
    "INVALID_PROVENANCE",
    "provenance_fingerprint",
    "validate_authoring_state",
    "parse_dxt",
    "parse_dxt_bytes",
    "decode_rgba_pixels",
    "encode_dxt_pixels",
    "replace_dxt_pixels",
    "parse_sidecar",
    "resolve_sidecar",
]
