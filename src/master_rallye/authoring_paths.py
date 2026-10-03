"""Evidence-led discovery and mirroring for absolute GXI source paths."""
from __future__ import annotations

import hashlib
import shutil
from dataclasses import dataclass
from pathlib import Path, PurePosixPath, PureWindowsPath
from typing import Any, Mapping

from .gxm import parse_gxm_prefix


class AuthoringPathError(ValueError):
    """A source GXI reference cannot be mapped or bridged safely."""


@dataclass(frozen=True)
class AuthoringFileReference:
    gxm_role: str
    embedded_path: str
    historical_root: str
    mirror_relative_path: str
    source_relative_path: str
    source_sha256: str
    resolution: str

    def to_dict(self) -> dict[str, str]:
        return {
            "gxm_role": self.gxm_role,
            "embedded_path": self.embedded_path,
            "historical_root": self.historical_root,
            "mirror_relative_path": self.mirror_relative_path,
            "source_relative_path": self.source_relative_path,
            "source_sha256": self.source_sha256,
            "resolution": self.resolution,
        }


def _sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with Path(path).open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def _safe_source_files(root: Path) -> list[Path]:
    root = Path(root).resolve()
    if not root.is_dir():
        raise AuthoringPathError(f"source folder does not exist: {root}")
    result = []
    for path in root.rglob("*"):
        if path.is_symlink() or not path.is_file():
            continue
        resolved = path.resolve()
        try:
            resolved.relative_to(root)
        except ValueError as exc:
            raise AuthoringPathError(f"source file escapes source folder: {path}") from exc
        result.append(path)
    return sorted(result, key=lambda item: item.relative_to(root).as_posix().casefold())


def discover_embedded_authoring_paths(
    source_root: Path,
    gxm_by_role: Mapping[str, Path],
) -> dict[str, Any]:
    """Resolve every parsed absolute ``.gxi`` reference against copied source files.

    Matching uses a normalized relative path first and then a unique basename.
    If multiple candidate files differ in bytes, resolution fails closed.
    """
    root = Path(source_root).resolve()
    source_files = _safe_source_files(root)
    by_relative = {path.relative_to(root).as_posix().casefold(): path for path in source_files}
    by_name: dict[str, list[Path]] = {}
    for path in source_files:
        by_name.setdefault(path.name.casefold(), []).append(path)

    references: dict[tuple[str, str], AuthoringFileReference] = {}
    errors: list[dict[str, str]] = []
    for role, gxm_path in sorted(gxm_by_role.items()):
        gxm_path = Path(gxm_path).resolve()
        try:
            gxm_path.relative_to(root)
        except ValueError as exc:
            raise AuthoringPathError(f"GXM source is outside source folder: {gxm_path}") from exc
        parsed = parse_gxm_prefix(gxm_path)
        if parsed.prefix_kind != "material_table":
            raise AuthoringPathError(
                f"{role} GXM has unsupported authoring-reference prefix {parsed.prefix_kind}"
            )
        for material in parsed.materials:
            for slot in material.slots:
                embedded = slot.reference.strip()
                if embedded.casefold() == "null" or not embedded.casefold().endswith(".gxi"):
                    continue
                win_path = PureWindowsPath(embedded.replace("/", "\\"))
                if not win_path.is_absolute() or not win_path.drive:
                    errors.append({
                        "gxm_role": role,
                        "embedded_path": embedded,
                        "reason": "relative_or_drive-less_GXI_path_not_supported",
                    })
                    continue
                historical_root = str(win_path.parent)
                mirror_relative = win_path.name
                candidates = by_name.get(win_path.name.casefold(), [])
                # Vehicle folders may contain nested alternate-model copies
                # (for example ``lpha/``). The top-level file is the package
                # member selected by the GXM's historical vehicle root.
                top_level = [path for path in candidates if path.parent == root]
                if top_level:
                    candidates = top_level
                if not candidates:
                    errors.append({
                        "gxm_role": role,
                        "embedded_path": embedded,
                        "reason": "source_GXI_not_found",
                    })
                    continue
                hashes = {_sha256_file(path) for path in candidates}
                if len(hashes) > 1:
                    errors.append({
                        "gxm_role": role,
                        "embedded_path": embedded,
                        "reason": "ambiguous_source_GXI_basename_with_different_bytes",
                    })
                    continue
                chosen = candidates[0]
                key = role.casefold(), embedded.casefold()
                references[key] = AuthoringFileReference(
                    role,
                    embedded,
                    historical_root,
                    mirror_relative,
                    chosen.relative_to(root).as_posix(),
                    next(iter(hashes)),
                    "RESOLVED" if len(candidates) == 1 else "RESOLVED_IDENTICAL_DUPLICATES",
                )

    ordered = sorted(
        references.values(),
        key=lambda item: (item.historical_root.casefold(), item.mirror_relative_path.casefold(),
                          item.gxm_role.casefold()),
    )
    roots: dict[str, dict[str, Any]] = {}
    for reference in ordered:
        key = reference.historical_root.casefold()
        row = roots.setdefault(key, {
            "historical_root": reference.historical_root,
            "files": [],
        })
        entry = {
            "mirror_relative_path": reference.mirror_relative_path,
            "source_relative_path": reference.source_relative_path,
            "source_sha256": reference.source_sha256,
        }
        existing = next((item for item in row["files"]
                         if item["mirror_relative_path"].casefold() == reference.mirror_relative_path.casefold()), None)
        if existing and existing["source_sha256"] != entry["source_sha256"]:
            errors.append({
                "gxm_role": reference.gxm_role,
                "embedded_path": reference.embedded_path,
                "reason": "one_historical_path_maps_to_different_source_bytes",
            })
        elif not existing:
            row["files"].append(entry)

    for index, row in enumerate(sorted(roots.values(), key=lambda item: item["historical_root"].casefold())):
        row["mirror_id"] = f"root-{index:02d}"
        row["files"].sort(key=lambda item: item["mirror_relative_path"].casefold())

    return {
        "schema_version": 1,
        "source_root": str(root),
        "references": [item.to_dict() for item in ordered],
        "historical_roots": sorted(roots.values(), key=lambda item: item["historical_root"].casefold()),
        "unresolved": sorted(errors, key=lambda item: (item["gxm_role"].casefold(), item["embedded_path"].casefold())),
        "status": "PASS" if not errors else "BLOCKED",
    }


def materialize_authoring_mirror(
    source_root: Path,
    discovery: Mapping[str, Any],
    mirror_root: Path,
) -> list[dict[str, Any]]:
    """Copy only referenced GXI files and verify their hashes after copying."""
    if discovery.get("status") != "PASS":
        raise AuthoringPathError("cannot build authoring mirror while GXI references are unresolved")
    source_root = Path(source_root).resolve()
    mirror_root = Path(mirror_root).resolve()
    if mirror_root.exists():
        raise AuthoringPathError(f"authoring mirror output already exists: {mirror_root}")
    mirror_root.mkdir(parents=True)
    records: list[dict[str, Any]] = []
    try:
        for root_row in discovery.get("historical_roots", []):
            target_root = mirror_root / root_row["mirror_id"]
            for file_row in root_row["files"]:
                relative = PurePosixPath(file_row["mirror_relative_path"])
                if relative.is_absolute() or any(part in {"", ".", ".."} for part in relative.parts):
                    raise AuthoringPathError(f"unsafe authoring mirror path: {relative}")
                source = source_root / Path(file_row["source_relative_path"])
                resolved_source = source.resolve()
                resolved_source.relative_to(source_root)
                if _sha256_file(resolved_source) != file_row["source_sha256"]:
                    raise AuthoringPathError(f"source GXI changed after inventory: {source}")
                destination = target_root.joinpath(*relative.parts)
                destination.parent.mkdir(parents=True, exist_ok=True)
                shutil.copyfile(resolved_source, destination)
                copied_hash = _sha256_file(destination)
                if copied_hash != file_row["source_sha256"]:
                    raise AuthoringPathError(f"copied GXI hash mismatch: {destination}")
                records.append({
                    **file_row,
                    "mirror_id": root_row["mirror_id"],
                    "target_path": str(destination),
                    "copied_sha256": copied_hash,
                })
    except Exception:
        shutil.rmtree(mirror_root, ignore_errors=True)
        raise
    return sorted(records, key=lambda item: (item["mirror_id"], item["mirror_relative_path"].casefold()))
