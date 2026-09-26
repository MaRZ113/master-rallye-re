"""Source-only extraction of a sidecar-identified GXM ``$chull`` range."""
from __future__ import annotations


def analyze_gxm_chull(data: bytes, sidecar_path, directive: str) -> dict:
    """Resolve one sidecar-named ``$chull`` range and its referenced Vector-C set.

    This function reads only source GXM and its text sidecar. It does not parse
    or accept compiled DX data.
    """
    import struct
    from pathlib import Path

    from .gxm import (parse_gxm_geometry_prefix_bytes, parse_gxm_prefix_bytes,
                      parse_gxm_triangle_prefix_bytes)
    from .sidecar import parse_sidecar

    sidecar = parse_sidecar(Path(sidecar_path))
    prefix = parse_gxm_prefix_bytes(data, "GXM chull analysis")
    geometry = parse_gxm_geometry_prefix_bytes(data, prefix)
    triangles = parse_gxm_triangle_prefix_bytes(data, prefix, geometry)
    matches = [mesh for mesh in sidecar.meshes if mesh.name == directive]
    if len(matches) != 1 or sidecar.mesh_span != triangles.record_count:
        raise ValueError("sidecar must identify one chull and match the GXM record span")
    mesh = matches[0]
    if mesh.index < 0 or mesh.size <= 0 or mesh.index + mesh.size > triangles.record_count:
        raise ValueError("chull record range outside GXM triangle records")
    records = tuple(struct.unpack_from("<10I", data, triangles.record_offset + i * 52)
                    for i in range(mesh.index, mesh.index + mesh.size))
    indices = sorted({index for record in records for index in record[4:7]})
    points = {index: struct.unpack_from("<3f", data, triangles.vector_c_offset + index * 12)
              for index in indices}
    return {"directive": directive, "record_start": mesh.index, "record_count": mesh.size,
            "material_count": len(prefix.materials),
            "record_range_half_open": [mesh.index, mesh.index + mesh.size],
            "source_c_indices": indices, "source_c_points": points,
            "records": records, "header_words": prefix.header_words,
            "geometry_prefix": geometry, "triangle_prefix": triangles}
