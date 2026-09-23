"""Test-only tag-101 encoder; never exposed as a production writer."""
from __future__ import annotations

import math
import struct


TETRA_VERTICES = (
    (0.0, 0.0, 0.0),
    (1.0, 0.0, 0.0),
    (0.0, 1.0, 0.0),
    (0.0, 0.0, 1.0),
)
TETRA_TRIANGLES = ((0, 2, 1), (0, 1, 3), (1, 2, 3), (2, 0, 3))
TETRA_EDGES = ((0, 1), (1, 2), (0, 2), (0, 3), (1, 3), (2, 3))
TETRA_EDGE_FACES = ((0, 1), (0, 2), (0, 3), (1, 3), (1, 2), (2, 3))
TETRA_FACE_EDGES = ((2, 1, 0), (0, 4, 3), (1, 5, 4), (2, 3, 5))


def geometry_block(vertices, triangles=()):
    payload = bytearray(struct.pack("<2i", len(vertices), len(triangles)))
    for vertex in vertices:
        payload += struct.pack("<3f", *vertex)
    for triangle in triangles:
        payload += struct.pack("<3i", *triangle)
    return bytes(payload)


def _area(indices):
    a, b, c = (TETRA_VERTICES[index] for index in indices[:3])
    left = tuple(b[index] - a[index] for index in range(3))
    right = tuple(c[index] - a[index] for index in range(3))
    cross = (
        left[1] * right[2] - left[2] * right[1],
        left[2] * right[0] - left[0] * right[2],
        left[0] * right[1] - left[1] * right[0],
    )
    return math.sqrt(sum(value * value for value in cross)) * 0.5


def representation():
    payload = bytearray(geometry_block(TETRA_VERTICES, TETRA_TRIANGLES))
    payload += geometry_block(((0.25, 0.25, 0.25),))
    payload += struct.pack("<i4i", 4, 0, 1, 2, 3)
    payload += struct.pack("<i", len(TETRA_EDGES))
    for edge in TETRA_EDGES:
        payload += struct.pack("<2i", *edge)
    payload += struct.pack("<i", len(TETRA_TRIANGLES))
    for face in TETRA_TRIANGLES:
        payload += struct.pack("<i", len(face)) + struct.pack("<3i", *face)
        payload += struct.pack("<i", len(face)) + struct.pack("<3i", *face)
    for pair in TETRA_EDGE_FACES:
        payload += struct.pack("<2i", *pair)
    for loop in TETRA_FACE_EDGES:
        payload += struct.pack("<i", len(loop)) + struct.pack("<3i", *loop)
    for face in TETRA_TRIANGLES:
        payload += struct.pack("<f", _area(face))
    return bytes(payload)


def tag101(*, suffix=b"", base_triangles=()):
    payload = bytearray(struct.pack("<I", 101))
    payload += geometry_block(((0.5, 0.5, 0.5),), base_triangles)
    payload += struct.pack("<f", math.sqrt(3.0) * 0.5)
    payload += representation()
    payload += representation()
    payload += suffix
    return bytes(payload)


def tag102(value_0=0.4, value_1=0.2):
    return struct.pack("<I2f", 102, value_0, value_1)
