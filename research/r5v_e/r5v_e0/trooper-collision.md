# Trooper collision validation

The candidate uses the authentic Trooper `car.dx` tag101 payload. It does not
substitute a donor collision.

| Check | Result |
|---|---|
| Source | demo-9.3.1 Trooper revision-131 `car.dx`; tag101 SHA-256 `c6a6c6723611845d62e14115666a76c10d51f3ffefc883337f584afdc99a6bcb` |
| Converted output | revision-135 `car.dx`, SHA-256 `04a9aa09b813a0893953e6813b2d8ec4ac63a5545b987e12a29e692773de06e1`; collision bytes preserved |
| Tag101 serializer | Byte-identical roundtrip; 5,296 bytes |
| Base scalar | `2.6045312881469727`, finite and positive |
| Detailed representation B / geometry A | 28 vertices, 52 triangles; all coordinates and triangle areas finite; minimum triangle area `0.022180627097006245` |
| Closed-edge check | PASS; all 78 unique edges are used exactly twice |
| Translation invariant audit | PASS; max pairwise-distance error `3.33e-8`, max face-area error `1.19e-7`; source bytes not modified |

The tag101 structures contain positions/topology rather than a separate
collision normal array. Both converted DX model validation and the preserved
render data report finite vertex normals. Structural validation is PASS. The
owner separately reports that ID25 Trooper collision and damage worked during
the R5V-E0 P1 runtime test; the exact tested EXE hash and raw capture were not
supplied. See [runtime-test-plan.md](runtime-test-plan.md) for provenance and
scope.
