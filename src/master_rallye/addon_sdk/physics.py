"""Strict, byte-preserving family clone for qualified DataGame XML templates."""
from __future__ import annotations

import re
import xml.etree.ElementTree as ET
from typing import Any

from .manifest import AddonValidationError


_FAMILY = re.compile(r"^[A-Za-z][A-Za-z0-9_]{1,39}$")


def clone_vehicle_family_xml(source: bytes, *, donor_family: str,
                             runtime_family: str, source_label: str) -> tuple[bytes, dict[str, Any]]:
    """Append a donor's native Values under a new family without editing donor/stock rows."""
    if not _FAMILY.fullmatch(donor_family) or not _FAMILY.fullmatch(runtime_family):
        raise AddonValidationError("physics donor/runtime family names must be safe resource identifiers")
    if donor_family.casefold() == runtime_family.casefold():
        raise AddonValidationError("physics family must be independent from the donor family")
    try:
        root = ET.fromstring(source.decode("utf-8-sig"))
    except (UnicodeDecodeError, ET.ParseError) as exc:
        raise AddonValidationError(f"{source_label} is not valid UTF-8 XML: {exc}") from exc

    donor_prefix = f"Vehicles/{donor_family}/"
    target_prefix = f"Vehicles/{runtime_family}/"
    donor_nodes = [node for node in root.iter("Value")
                   if (node.get("Name") or "").startswith(donor_prefix)]
    if not donor_nodes:
        raise AddonValidationError(f"{source_label} has no {donor_prefix} donor values")
    if any((node.get("Name") or "").casefold().startswith(target_prefix.casefold())
           for node in root.iter("Value")):
        raise AddonValidationError(f"{source_label} already contains target family {runtime_family}")

    donor_prefix_bytes = f'Name="Vehicles/{donor_family}/'.encode("ascii")
    target_prefix_bytes = f'Name="Vehicles/{runtime_family}/'.encode("ascii")
    pattern = re.compile(rb'<Value\s+Name="Vehicles/' + re.escape(donor_family.encode("ascii"))
                         + rb'/[^\"]+"[^>]*/>')
    clones: list[bytes] = []
    for line in source.splitlines():
        if donor_prefix_bytes not in line:
            continue
        match = pattern.search(line)
        if match is None:
            raise AddonValidationError(f"{source_label} donor entries do not use the audited self-closing Value format")
        clones.append(line.replace(donor_prefix_bytes, target_prefix_bytes, 1))
    if len(clones) != len(donor_nodes):
        raise AddonValidationError(
            f"{source_label} serialized donor entry count differs from parsed XML ({len(clones)} vs {len(donor_nodes)})"
        )
    marker = b"</Broker>"
    if source.count(marker) != 1:
        raise AddonValidationError(f"{source_label} must contain exactly one Broker close marker")
    newline = b"\r\n" if b"\r\n" in source else b"\n"
    inserted = newline + newline.join(clones) + newline
    output = source.replace(marker, inserted + marker, 1)
    try:
        output_root = ET.fromstring(output.decode("utf-8-sig"))
    except (UnicodeDecodeError, ET.ParseError) as exc:
        raise AddonValidationError(f"generated {source_label} family clone is invalid XML: {exc}") from exc
    output_values = list(output_root.iter("Value"))
    names = [node.get("Name", "") for node in output_values]
    if len(names) != len(set(names)):
        raise AddonValidationError(f"generated {source_label} contains duplicate Broker paths")
    cloned_nodes = [node for node in output_values
                    if (node.get("Name") or "").startswith(target_prefix)]
    if len(cloned_nodes) != len(donor_nodes):
        raise AddonValidationError(f"generated {source_label} family clone lost donor values")
    for donor, clone in zip(donor_nodes, cloned_nodes):
        expected = dict(donor.attrib)
        expected["Name"] = expected["Name"].replace(donor_prefix, target_prefix, 1)
        if clone.attrib != expected:
            raise AddonValidationError(f"generated {source_label} value differs from its donor template")
    # Removing precisely the appended byte block must reproduce the input.
    if output.replace(inserted, b"", 1) != source:
        raise AddonValidationError(f"generated {source_label} changed bytes outside the appended family values")
    return output, {
        "source_label": source_label,
        "donor_family": donor_family,
        "runtime_family": runtime_family,
        "cloned_value_count": len(clones),
        "stock_values_preserved_byte_exact": True,
        "semantic_delta": False,
    }
