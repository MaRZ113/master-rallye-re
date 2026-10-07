"""Exact, immutable Observatory identities. Unknown executables fail closed."""
from dataclasses import dataclass, field
import hashlib
from pathlib import Path
from typing import Any


@dataclass(frozen=True)
class ObservatoryBuildProfile:
    id: str
    display_name: str
    sha256: str
    file_size: int
    active_log_sink_rva: int
    debug_sink_vtable_rva: int
    evidence: str
    tools: tuple[str, ...]
    profile_origin: str = "committed_exact"
    exact_profile_id: str | None = None
    compatibility_family: str | None = "retail-broker-v1"
    vehicle_registry_profile: str = "pristine"
    audit_version: str | None = None
    audit_fingerprint: str | None = None
    capabilities: dict[str, Any] = field(default_factory=dict)
    runtime_anchors: tuple[dict[str, Any], ...] = ()
    local_profile_cache: str | None = None
    cache_reused: bool = False
    pe_identity: dict[str, Any] = field(default_factory=dict)

    @property
    def build_classification(self) -> str:
        """Return the user-facing trust class derived from verified evidence."""
        if self.profile_origin == "committed_exact":
            return "exact"
        if self.capabilities.get("hardened_dump"):
            return "hardened"
        if self.capabilities.get("broker_read"):
            return "compatible"
        return "incompatible"

    def __post_init__(self) -> None:
        if self.profile_origin == "committed_exact" and self.exact_profile_id is None:
            object.__setattr__(self, "exact_profile_id", self.id)
        if not self.capabilities:
            # Exact public profiles retain their established opener contract.
            # Native Dump is separate from post-Results safety.
            capabilities = {
                "broker_read": "broker-editor" in self.tools,
                "open_broker_editor": "broker-editor" in self.tools,
                "native_dump": "broker-editor" in self.tools,
                "broker_capture_active_race": "broker-editor" in self.tools,
                "active_race_native_dump_safe": "broker-editor" in self.tools,
                "post_results_native_dump_safe": False,
                "hardened_dump": False,
                "flow_builder": "flow-builder" in self.tools,
                "legacy_loading_attract_present": None,
            }
            object.__setattr__(self, "capabilities", capabilities)

    def supports(self, capability: str) -> bool:
        return bool(self.capabilities.get(capability, False))


RETAIL_PRISTINE = ObservatoryBuildProfile(
    "retail-pristine", "Master Rallye Retail (pristine)",
    "bf8aef32407eb6552c05045b8abef149f32983cedd9503b865069b444c5f96b4",
    3121214, 0x2F7B7C, 0x29CEA8, "CONFIRMED_BY_RUNTIME",
    ("broker-editor", "flow-builder"),
)
RETAIL_WIDESCREEN_FREEZE = ObservatoryBuildProfile(
    "retail-widescreen-freeze", "Master Rallye Retail (widescreen + freeze)",
    "bcf310a79133b03aa89ce51197a37516ee27c1b0e9da19788519e849e7a2f2f6",
    3117118, 0x2F6B64, 0x29BF3C, "CONFIRMED_BY_RUNTIME",
    ("broker-editor",),
)
PROFILES = (RETAIL_PRISTINE, RETAIL_WIDESCREEN_FREEZE)


def match_profile(sha256: str, file_size: int) -> ObservatoryBuildProfile:
    for profile in PROFILES:
        if sha256 == profile.sha256:
            if file_size != profile.file_size:
                raise ValueError("Known executable hash has an unexpected file size")
            return profile
    raise ValueError("Unsupported Master Rallye executable: unknown SHA256")


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def profile_for_file(path: Path) -> ObservatoryBuildProfile:
    return match_profile(sha256_file(path), path.stat().st_size)
