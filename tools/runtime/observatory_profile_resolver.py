"""Resolve internal Research Observatory profiles from exact or audited evidence.

Exact profiles remain first. Unknown hashes are admitted only when the retail
PE layout and passive Broker read core independently audit; optional command
capabilities remain independently disabled when their own anchors do not match.
"""
from __future__ import annotations

from pathlib import Path
from typing import Any

from observatory_build_profiles import (
    PROFILES,
    ObservatoryBuildProfile,
    match_profile,
)
import observatory_compatibility as compatibility


def _from_audit(audit: dict[str, Any], *, exact: ObservatoryBuildProfile | None = None
                ) -> ObservatoryBuildProfile:
    caps = dict(audit.get("capabilities", {}))
    exact_id = exact.id if exact else audit.get("exact_profile_id")
    origin = "committed_exact" if exact or exact_id else "locally_audited"
    profile_id = exact.id if exact else audit.get("profile_id")
    if not profile_id:
        profile_id = "local-audited-" + audit["sha256"][:12]
    family = audit.get("compatibility_family") or (exact.compatibility_family if exact else None)
    registry = audit.get("vehicle_registry_profile", "unknown")
    if registry == "unknown" and exact:
        registry = exact.vehicle_registry_profile
    tools = tuple(name for name, capability in (
        ("broker-editor", "open_broker_editor"),
        ("flow-builder", "flow_builder"),
    ) if caps.get(capability, False))
    if exact and not audit.get("compatibility_family"):
        caps = dict(exact.capabilities)
        tools = exact.tools
    anchors = tuple(
        {"name": row["name"], "rva": row["rva"], "length": row["length"],
         "sha256": row["sha256"], "section": row["section"]}
        for row in audit.get("anchors", [])
        if row.get("compatible") and row.get("sha256") and row.get("section") in (".text", ".rdata")
    )
    pe = audit.get("pe", {})
    layout = audit.get("observatory") or {}
    return ObservatoryBuildProfile(
        id=profile_id,
        display_name=(exact.display_name if exact else
                      f"Master Rallye Retail family ({family or 'Broker core'})"),
        sha256=audit["sha256"],
        file_size=audit["size"],
        active_log_sink_rva=layout.get("active_log_sink_rva", exact.active_log_sink_rva if exact else 0),
        debug_sink_vtable_rva=layout.get("debug_sink_vtable_rva", exact.debug_sink_vtable_rva if exact else 0),
        evidence="CONFIRMED_BY_EXE",
        tools=tools,
        profile_origin=origin,
        exact_profile_id=exact_id,
        compatibility_family=family,
        vehicle_registry_profile=registry,
        audit_version=audit.get("audit_version"),
        audit_fingerprint=audit.get("audit_fingerprint"),
        capabilities=caps,
        runtime_anchors=anchors,
        local_profile_cache=audit.get("local_profile_cache"),
        cache_reused=bool(audit.get("cache_reused")),
        pe_identity={key: pe.get(key) for key in ("machine", "image_base", "size_of_image", "entry_rva")},
    )


def resolve_executable_profile(path: Path, *, cache_root: Path | None = None,
                               write_local_profile: bool = True) -> ObservatoryBuildProfile:
    """Verify the current file and resolve one immutable profile object.

    Exact public identities win. The internal Research Observatory then uses
    the audited retail-family model. The process never trusts basename, size,
    or cache alone; every call reads and re-audits current bytes.
    """
    path = Path(path)
    if path.name.casefold() != "mrallye.exe" or not path.is_file():
        raise ValueError("Expected a readable MRallye.exe file")
    data = path.read_bytes()
    image_hash = compatibility.digest(data)
    size = len(data)
    try:
        exact = match_profile(image_hash, size)
    except ValueError:
        exact = None

    try:
        resolved = compatibility.resolve_build(
            data, cache_root=cache_root,
            write_local_profile=write_local_profile,
            allow_degraded=True,
        )
        # The two historical exact Observatory profiles are not both present
        # in the R-OBS2 profile list. Preserve their exact committed route.
        return _from_audit(resolved, exact=exact)
    except ValueError:
        if exact is not None:
            # Exact profiles remain valid even when an unrelated family anchor
            # (such as Attract or resource loading) is outside this audit.
            try:
                audit = compatibility.audit_build(data)
            except ValueError:
                return exact
            if audit.get("capabilities", {}).get("broker_read"):
                return _from_audit(audit, exact=exact)
            return exact
        raise


def profile_provenance(profile: ObservatoryBuildProfile) -> dict[str, Any]:
    """JSON-safe provenance shared by captures and command status."""
    return {
        "build_profile": profile.id,
        "exact_profile_id": profile.exact_profile_id,
        "profile_origin": profile.profile_origin,
        "compatibility_family": profile.compatibility_family,
        "audit_version": profile.audit_version,
        "audit_fingerprint": profile.audit_fingerprint,
        "vehicle_registry_profile": profile.vehicle_registry_profile,
        "capabilities": dict(profile.capabilities),
        "broker_dump_variant": profile.capabilities.get("broker_dump_variant", "unknown"),
        "native_dump_post_results_safe": profile.capabilities.get("post_results_native_dump_safe"),
        "legacy_loading_attract_present": profile.capabilities.get("legacy_loading_attract_present"),
    }


def required_runtime_anchors(profile: ObservatoryBuildProfile, capability: str) -> tuple[dict[str, Any], ...]:
    names = {
        "broker_read": {"debug_logger", "debug_sink_vtable"},
        "native_dump": {"broker_editor_dump_route", "broker_singleton_accessor", "native_dump_walker"},
        "open_broker_editor": {"broker_editor_dump_route"},
    }.get(capability, set())
    by_name = {item["name"]: item for item in profile.runtime_anchors}
    if not names or not names.issubset(by_name):
        return ()
    return tuple(by_name[name] for name in sorted(names))
