"""Loss-preserving read-only inventory for course TXT hierarchy names."""
from __future__ import annotations

import re
from dataclasses import dataclass
from pathlib import Path


NODE_RE = re.compile(
    r"^\s*(?P<class>mo[A-Za-z0-9_]+)\(Name \[(?P<name>.*?)\](?P<tail>.*?)\)\s*$"
)
MESH_SPAN_RE = re.compile(r"\bIndex\s+(\d+)\s+Size\s+(\d+)\b")
LITERAL_TOKEN_RES = (
    ("$bsp", re.compile(r"\$bsp\b", re.I)),
    ("$startline", re.compile(r"\$startline\b", re.I)),
    ("$finishline", re.compile(r"\$finishline\b", re.I)),
    ("$splittime", re.compile(r"\$splittime\d*\b", re.I)),
    ("$grnd", re.compile(r"\$grnd(?:u|v)?(?=[:(\s\]]|$)", re.I)),
    ("$landdb", re.compile(r"\$landdb\b", re.I)),
    ("$draw", re.compile(r"\$draw\b", re.I)),
    ("$nodraw", re.compile(r"\$nodraw\b", re.I)),
    ("$ps2cells", re.compile(r"\$ps2cells\b", re.I)),
    ("$boinds", re.compile(r"\$boinds\b", re.I)),
    ("_boinds", re.compile(r"_boinds\b", re.I)),
    ("_limits", re.compile(r"_limits\b", re.I)),
    ("_raceline", re.compile(r"_raceline\b", re.I)),
    ("raceline", re.compile(r"(?<!_)\braceline\b", re.I)),
    ("startpoint", re.compile(r"\bstartpoint\b", re.I)),
    ("_bsplit", re.compile(r"_bsplit\w*\b", re.I)),
)


@dataclass(frozen=True)
class CourseTxtNode:
    node_id: int
    line_number: int
    indent: int
    class_name: str
    name: str
    parent_id: int | None
    mesh_index: int | None
    mesh_size: int | None
    literal_tokens: tuple[str, ...]
    raw_line: str


@dataclass(frozen=True)
class CourseTxtDocument:
    source: str
    nodes: tuple[CourseTxtNode, ...]
    unparsed_node_lines: tuple[tuple[int, str], ...]


def parse_course_txt_bytes(data: bytes, source: str = "<bytes>") -> CourseTxtDocument:
    """Retain exact node names and brace-backed hierarchy from a course TXT.

    This describes the TXT sidecar tree only. It does not claim to decode GXM
    transforms, point arrays, or runtime helper behavior.
    """
    text = data.decode("latin-1")
    lines = text.splitlines()
    nodes: list[CourseTxtNode] = []
    unparsed: list[tuple[int, str]] = []
    open_nodes: list[CourseTxtNode] = []
    model_root_id: int | None = None

    for index, raw_line in enumerate(lines):
        stripped = raw_line.strip()
        indent = len(raw_line) - len(raw_line.lstrip(" \t"))
        if stripped == "}":
            while open_nodes and indent <= open_nodes[-1].indent:
                open_nodes.pop()
            continue

        match = NODE_RE.fullmatch(raw_line)
        if not match:
            if re.match(r"^\s*mo[A-Za-z0-9_]+\(", raw_line):
                unparsed.append((index + 1, raw_line))
            continue

        class_name = match.group("class")
        name = match.group("name")
        span_match = MESH_SPAN_RE.search(match.group("tail"))
        parent_id = open_nodes[-1].node_id if open_nodes else model_root_id
        literal_tokens = tuple(
            token for token, pattern in LITERAL_TOKEN_RES if pattern.search(name)
        )
        node = CourseTxtNode(
            node_id=len(nodes),
            line_number=index + 1,
            indent=indent,
            class_name=class_name,
            name=name,
            parent_id=parent_id,
            mesh_index=int(span_match.group(1)) if span_match else None,
            mesh_size=int(span_match.group(2)) if span_match else None,
            literal_tokens=literal_tokens,
            raw_line=raw_line,
        )
        nodes.append(node)
        if class_name.casefold() == "momodel" and model_root_id is None:
            model_root_id = node.node_id
        next_line = lines[index + 1].strip() if index + 1 < len(lines) else ""
        if next_line == "{":
            open_nodes.append(node)

    return CourseTxtDocument(source, tuple(nodes), tuple(unparsed))


def parse_course_txt(path: Path) -> CourseTxtDocument:
    resolved = path.resolve()
    return parse_course_txt_bytes(resolved.read_bytes(), resolved.name)
