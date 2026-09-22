"""Read-only texture reference audit for preservation and asset archaeology."""
from __future__ import annotations

from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from .dx import parse_dx
from .sidecar import normalize_texture_value, parse_sidecar

ALTERNATIVE_NAME_HINTS = {
    "alt",
    "beta",
    "blank",
    "blue",
    "hybrid",
    "livery",
    "old",
    "promo",
    "red",
    "skin",
    "unused",
    "yellow",
}


def _normalized_reference(value: str) -> str | None:
    if value.strip().casefold() == "null":
        return None
    return normalize_texture_value(value).casefold()


def audit_vehicle_textures(directory: Path) -> dict[str, Any]:
    directory = directory.resolve()
    present_paths = sorted(directory.glob("*.dxt"), key=lambda path: path.name.casefold())
    present = {path.stem.casefold(): path.name for path in present_paths}
    dx_references: set[str] = set()
    txt_references: set[str] = set()
    errors: list[dict[str, str]] = []

    for path in sorted(directory.glob("*.dx"), key=lambda item: item.name.casefold()):
        try:
            model = parse_dx(path)
            for draw in model.physical_draws:
                for slot in draw.texture_slots:
                    reference = _normalized_reference(slot.value)
                    if reference:
                        dx_references.add(reference)
        except Exception as error:
            errors.append({"source": path.name, "kind": "dx", "error": str(error)})

    for path in sorted(directory.glob("*.txt"), key=lambda item: item.name.casefold()):
        try:
            sidecar = parse_sidecar(path)
            for material in sidecar.materials:
                for texture in material.textures:
                    reference = _normalized_reference(texture.resource_stem)
                    if reference:
                        txt_references.add(reference)
        except Exception as error:
            errors.append({"source": path.name, "kind": "txt", "error": str(error)})

    referenced = dx_references | txt_references
    unreferenced = sorted(set(present) - referenced)
    missing = sorted(referenced - set(present))
    alternatives = [
        stem for stem in unreferenced
        if any(token in stem for token in ALTERNATIVE_NAME_HINTS)
    ]
    return {
        "vehicle": directory.name,
        "dxt_present": [present[stem] for stem in sorted(present)],
        "dx_referenced": sorted(dx_references),
        "txt_referenced": sorted(txt_references),
        "referenced_by_either": sorted(referenced),
        "apparently_unreferenced": [present[stem] for stem in unreferenced],
        "missing_referenced_resources": missing,
        "candidate_alternative_or_beta": [present[stem] for stem in alternatives],
        "errors": errors,
        "caution": (
            "Unreferenced by currently known DX/TXT metadata does not mean safe to delete."
        ),
    }


def audit_texture_tree(root: Path) -> dict[str, Any]:
    root = root.resolve()
    if any(root.glob("*.dx")) or any(root.glob("*.dxt")):
        directories = [root]
    else:
        directories = sorted(
            {
                path.parent
                for pattern in ("*.dx", "*.dxt")
                for path in root.rglob(pattern)
            },
            key=lambda path: path.as_posix().casefold(),
        )
    vehicles = [audit_vehicle_textures(directory) for directory in directories]
    return {
        "schema_version": 1,
        "generated_utc": datetime.now(timezone.utc).isoformat(),
        "source_descriptor": "external read-only vehicle texture tree",
        "vehicle_count": len(vehicles),
        "summary": {
            "dxt_present": sum(len(item["dxt_present"]) for item in vehicles),
            "dx_referenced": sum(len(item["dx_referenced"]) for item in vehicles),
            "txt_referenced": sum(len(item["txt_referenced"]) for item in vehicles),
            "apparently_unreferenced": sum(
                len(item["apparently_unreferenced"]) for item in vehicles
            ),
            "missing_referenced_resources": sum(
                len(item["missing_referenced_resources"]) for item in vehicles
            ),
            "candidate_alternative_or_beta": sum(
                len(item["candidate_alternative_or_beta"]) for item in vehicles
            ),
            "errors": sum(len(item["errors"]) for item in vehicles),
        },
        "vehicles": vehicles,
    }
