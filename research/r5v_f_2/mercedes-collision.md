# Authentic Mercedes collision audit

The collision source selected for the distinct historic model is tag101 in `demo-8.4.1/DataGx/Vehicles/Copy of Mercedes/car.dx`, not the registered `Mercedes` folder's LandCruiser-identical car file.

| Check | Result |
|---|---|
| Source DX | Revision127; 112,501 bytes; SHA-256 `989905468d528bb35dec7901b03a08367b37a1fa4f8a32143428a782253d0791` |
| Demo structural parser | Pass; tag101 present; no parser warnings/errors |
| Tag101 | 5,668 bytes; SHA-256 `9e834c3cb9ca3186bc84f1f7c9a4eec90638aa74fcc9045bdfe08a1f13003f3e` |
| Finite values | All render positions/normals, collision coordinates, base scalar and face scalars finite; base scalar is positive |
| Representation A | 8 vertices / 12 triangles; every edge incident twice; Euler characteristic 2; convex |
| Representation B | 34 vertices / 64 triangles; every edge incident twice; Euler characteristic 2; convex |
| Zero-edit serializer | `serialize_tag101(parsed) == original bytes` |
| Bounds suffix | Marker1339 suffix parses; center/radius/min/max finite and ordered; 44 bytes |

`complete.dx` and `wheel.dx` contain tag102 and the parsed 44-byte bounds suffix; the authentic chassis collision is in `car.dx`. The selected source passed a bounded structural collision audit using the beta branch's `demo_dx.py`/collision code and the existing tag101 serializer. This is not a full retail DX parse, not a runtime collision test, and not proof that an eventual cooker preserves the tag101 bytes. A future converted output must re-run the retail SDK parser and collision checks and compare the produced tag101 to this source or otherwise document the cooker result.
