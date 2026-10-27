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
import observatory_locator as locator

# Located profiles resolve every address from code (observatory_locator). Their
# origin is distinct from committed exact and fixed-VA audited profiles.
LOCATED_ORIGIN = "locally_located"


def _from_audit(audit: dict[str, Any], *, exact: ObservatoryBuildProfile | None = None
                ) -> ObservatoryBuildProfile:
    caps = dict(audit.get("capabilities", {}))
    exact_id = exact.id if exact else audit.get("exact_profile_id")
    origin = "committed_exact" if exact or exact_id else "locally_audited"
    profile_id = exact.id if exact else audit.get("profile_id")
    if not profile_id:
        profile_id = ("local-hardened-" if caps.get("hardened_dump") else "local-audited-") + audit["sha256"][:12]
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
                      f"Master Rallye Retail family ({'hardened native Dump' if caps.get('hardened_dump') else family or 'Broker core'})"),
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


def locate_image(image: "locator.MappedImage", pe: dict[str, Any]) -> "locator.LocatedLayout":
    """Locate the Broker/Debug layout and classify the walker in ``image``."""
    layout = locator.locate(image)

    def hardened(img, walker_rva):
        if img.image_base + walker_rva != locator.RETAIL_REFERENCE["native_dump_walker"]:
            return None
        read_va = lambda va, size: img.bytes_at(va - img.image_base, size)
        section = lambda va, size: img.section_name(va - img.image_base, size)
        return compatibility.classify_hardened_walker(read_va, pe, section)

    locator.classify_walker(image, layout, hardened)
    return layout


def locate_executable(data: bytes) -> tuple[dict[str, Any], "locator.MappedImage", "locator.LocatedLayout"]:
    pe = compatibility.pe_layout(data)
    image = locator.MappedImage.from_pe(data, pe)
    return pe, image, locate_image(image, pe)


def _from_layout(data: bytes, pe: dict[str, Any], image: "locator.MappedImage",
                 layout: "locator.LocatedLayout",
                 exact: ObservatoryBuildProfile | None = None) -> ObservatoryBuildProfile:
    caps = layout.capabilities()
    if not caps["broker_read"]:
        problems = "; ".join(f"{k}: {v}" for k, v in sorted(layout.problems.items()))
        raise ValueError("Broker/Debug layout could not be located: " + (problems or "no Debug sink"))
    image_hash = compatibility.digest(data)
    caps["legacy_loading_attract_present"] = None
    tools = tuple(name for name, capability in (
        ("broker-editor", "open_broker_editor"), ("flow-builder", "flow_builder"))
        if caps.get(capability))
    variant = caps["native_dump_walker_variant"]
    return ObservatoryBuildProfile(
        id=exact.id if exact else "local-located-" + image_hash[:12],
        display_name=(exact.display_name if exact else
                      f"Master Rallye (located layout, walker {variant})"),
        sha256=image_hash,
        file_size=len(data),
        active_log_sink_rva=layout.rva("debug_sink_global"),
        debug_sink_vtable_rva=layout.rva("debug_sink_vtable"),
        evidence="LOCATED_BY_SIGNATURE",
        tools=tools,
        profile_origin=LOCATED_ORIGIN,
        exact_profile_id=exact.id if exact else None,
        compatibility_family="retail-broker-located",
        vehicle_registry_profile=exact.vehicle_registry_profile if exact else "unknown",
        audit_version=locator.LOCATOR_VERSION,
        audit_fingerprint=compatibility.digest(repr(sorted(layout.items.items())).encode()),
        capabilities=caps,
        runtime_anchors=tuple(locator.fingerprints(image, layout)),
        pe_identity={key: pe.get(key) for key in ("machine", "image_base", "size_of_image", "entry_rva")},
        located_layout=dict(layout.items),
    )


def resolve_executable_profile(path: Path, *, cache_root: Path | None = None,
                               write_local_profile: bool = True) -> ObservatoryBuildProfile:
    """Verify the current file and resolve one immutable profile object.

    Exact public identities win. The internal Research Observatory then uses
    the audited retail-family model. The process never trusts basename, size,
    or cache alone; every call reads and re-audits current bytes.
    """
    path = Path(path)
    if path.suffix.casefold() != ".exe" or not path.is_file():
        raise ValueError("Expected a readable Master Rallye .exe file")
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
        profile = _from_audit(resolved, exact=exact)
        if profile.supports("native_dump") or exact is not None:
            return profile
        # Fixed-VA audit admitted passive read only; the locator may still
        # prove the Dump route (e.g. an unrecognized walker patch).
        try:
            return _from_layout(data, *locate_executable(data))
        except ValueError:
            return profile
    except ValueError as audit_error:
        if exact is None:
            # Shifted code, grown sections, other retail-family builds: find
            # every address from code instead of the fixed retail VAs.
            try:
                return _from_layout(data, *locate_executable(data))
            except ValueError as exc:
                raise ValueError(f"{audit_error}; locator: {exc}") from exc
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
    """JSON-safe on-disk provenance for sources without a live attestation."""
    return {
        "build_profile": profile.id,
        "exact_profile_id": profile.exact_profile_id,
        "profile_origin": profile.profile_origin,
        "build_classification": profile.build_classification,
        "compatibility_family": profile.compatibility_family,
        "audit_version": profile.audit_version,
        "audit_fingerprint": profile.audit_fingerprint,
        "vehicle_registry_profile": profile.vehicle_registry_profile,
        "disk_capabilities": dict(profile.capabilities),
        "capabilities": dict(profile.capabilities),
        "effective_capabilities": {
            "broker_read": None,
            "native_dump": None,
            "post_results_native_dump_safe": None,
            "broker_dump_variant": "not_attested",
        },
        "disk_broker_dump_variant": profile.capabilities.get("broker_dump_variant", "unknown"),
        "disk_native_dump_post_results_safe": profile.capabilities.get("post_results_native_dump_safe"),
        "broker_dump_variant": "not_attested",
        "effective_broker_dump_variant": "not_attested",
        "native_dump_post_results_safe": None,
        "native_dump_verification": "not_attested",
        "legacy_loading_attract_present": profile.capabilities.get("legacy_loading_attract_present"),
    }


def required_runtime_anchors(profile: ObservatoryBuildProfile, capability: str) -> tuple[dict[str, Any], ...]:
    names = {
        "broker_read": {"debug_logger", "debug_sink_vtable"},
        "native_dump": {"debug_logger", "debug_sink_vtable", "broker_editor_dump_route",
                        "broker_singleton_accessor", "native_dump_walker"},
        "open_broker_editor": {"broker_editor_dump_route"},
    }.get(capability, set())
    by_name = {item["name"]: item for item in profile.runtime_anchors}
    if not names or not names.issubset(by_name):
        return ()
    return tuple(by_name[name] for name in sorted(names))
