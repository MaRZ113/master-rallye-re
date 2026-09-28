"""Read-only parser and corpus-path resolver for Master Rallye HNT manifests."""
from __future__ import annotations

import re
from dataclasses import dataclass
from pathlib import Path


ENTRY_RE = re.compile(r"^\s*([A-Za-z][A-Za-z0-9_]*)\s*\[([^\]]*)\]\s*$")
KNOWN_KINDS = {"model", "texture", "fstexture"}


@dataclass(frozen=True)
class HntEntry:
    line_number: int
    keyword: str
    value: str
    raw_line: str


@dataclass(frozen=True)
class HntDocument:
    source: str
    entries: tuple[HntEntry, ...]
    unparsed_lines: tuple[tuple[int, str], ...]

    def entries_of(self, keyword: str) -> tuple[HntEntry, ...]:
        folded = keyword.casefold()
        return tuple(entry for entry in self.entries if entry.keyword.casefold() == folded)


@dataclass(frozen=True)
class HntResolution:
    entry: HntEntry
    status: str
    resolved_path: str | None
    candidates: tuple[str, ...]


def parse_hnt_bytes(data: bytes, source: str = "<bytes>") -> HntDocument:
    """Parse recognized bracket records while preserving unknown source lines."""
    text = data.decode("latin-1")
    entries: list[HntEntry] = []
    unparsed: list[tuple[int, str]] = []
    for line_number, raw_line in enumerate(text.splitlines(), start=1):
        if not raw_line.strip():
            continue
        match = ENTRY_RE.fullmatch(raw_line)
        if match and match.group(1).casefold() in KNOWN_KINDS:
            entries.append(HntEntry(line_number, match.group(1), match.group(2), raw_line))
        else:
            unparsed.append((line_number, raw_line))
    return HntDocument(source, tuple(entries), tuple(unparsed))


def parse_hnt(path: Path) -> HntDocument:
    resolved = path.resolve()
    return parse_hnt_bytes(resolved.read_bytes(), resolved.name)


def _reference_key(value: str, extension: str) -> str | None:
    normalized = value.replace("\\", "/").strip("/")
    parts = normalized.split("/")
    if not normalized or any(part in {".", ".."} for part in parts):
        return None
    if Path(parts[-1]).suffix:
        relative = normalized
    else:
        relative = normalized + extension
    return relative.casefold()


def resolve_hnt_entries(
    document: HntDocument,
    data_gx_root: Path,
) -> tuple[HntResolution, ...]:
    """Resolve each known entry by exact case-insensitive corpus-relative path.

    Model and texture entries are mapped to `.dx` and `.dxt` respectively.
    FSTexture uses `.dxt`, but its role remains distinct in the parsed entry.
    No basename-only or fuzzy fallback is used.
    """
    root = data_gx_root.resolve()
    index: dict[str, list[str]] = {}
    for path in root.rglob("*"):
        if not path.is_file():
            continue
        relative = path.relative_to(root).as_posix()
        index.setdefault(relative.casefold(), []).append(relative)

    results: list[HntResolution] = []
    for entry in document.entries:
        kind = entry.keyword.casefold()
        extension = ".dx" if kind == "model" else ".dxt"
        key = _reference_key(entry.value, extension)
        candidates = tuple(sorted(index.get(key, ()), key=str.casefold)) if key else ()
        if len(candidates) == 1:
            status = "resolved"
            resolved_path = candidates[0]
        elif candidates:
            status = "ambiguous"
            resolved_path = None
        else:
            status = "unresolved"
            resolved_path = None
        results.append(HntResolution(entry, status, resolved_path, candidates))
    return tuple(results)
