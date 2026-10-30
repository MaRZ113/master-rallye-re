# Universal Vehicle Scene v1 — implemented Evo2 subset

Schema: `universal-vehicle-scene/1`; implementation:
`src/master_rallye/universal_vehicle_scene.py`. This version implements the
source-scene boundary proposed in UNIVERSAL_VEHICLE_SCENE_PROPOSAL.md for one
qualified Evo2 source. It does not migrate GT/Heritage or provide an MR compiler.

| Field / record | Meaning and retained evidence |
|---|---|
| `metadata` | Adapter identity, vehicle/year, exact parser/scene source-code SHA256 |
| `source` | Original root/catalog, POD and executable identity, protected roots, catalog records with line numbers, resource offsets/sizes/hashes/private original snapshot paths |
| `coordinate_system` | Original axis/unit interpretation, normalized frame, interpretation status, evidence and reversible row-major affine `source_to_normalized` matrix |
| `meshes` | Source positions/normals/UVs, original triangle indices and animation frames, name, material ID, original resource/object index/visibility/unknown fields |
| `nodes` | Instance IDs/mesh associations/parent, source and selected visibility, role, source-local matrix if actually present, original transform record, derived local matrix and transform evidence |
| `materials` | Original strings/flags, diffuse/bump texture associations, unsupported semantics, explicit neutral preview policy |
| `textures` | Exact original resource binding, TIFF tags/channel metadata, raw sample and 16-bit palette sidecars, separately derived neutral RGBA cache, all sizes/hashes |
| `wheel_variants`, `selection` | All six original meshes, selected native detail/side, equipment mask and evidence; no MR replacement or fitted hubs |
| `measurements` | Original and normalized hubs/tracks/bounds, catalog discrepancy and reversible geometry comparison |
| `unknown_semantics` | Stable IDs/status/meaning for unresolved source behavior; never implicit permission to delete or modify source geometry |

Matrices are row-major, affine, act on column points, translation at indices
3/7/11. Node `local_transform` is in original units; parent multiplication
precedes global normalization. A `source_local_transform` of null means the
source did not encode a recovered matrix; it does not claim a literal source
identity matrix. Wheel translation records are original values; their matrix
is derived for the evidenced zero-angle static pose. RH normalized coordinates
use metres, Y up, front -Z. Original source arrays remain unchanged. The preview
alone reverses winding when a composed transform has negative determinant and
uses inverse-transpose normal conversion. There is no destructive normalization.

API:

```python
from master_rallye.universal_vehicle_scene import load_scene, validate_scene
scene = load_scene(path)  # checks scene + manifest + all sidecar bindings
counts = validate_scene(scene)  # also usable for an in-memory candidate
```

`save_scene` accepts a validated scene and explicit sidecar byte mapping, fresh
output directory and protected source roots. Canonical sorted UTF-8 JSON with
finite numbers makes output deterministic for identical inputs/configuration.
`manifest.json` binds `scene.json` and every sidecar by size/SHA256; the manifest
does not claim a circular self-hash. Reopening requires the scene, manifest and content matches. Original TIFF/raw channel/palette and mesh
provenance links are validated, not merely carried as descriptive strings.

Limits: 32 MiB JSON, 128 MiB scene output, 200000 geometry/animation vertices,
400000 triangles, 64 MiB decoded textures, 256 texture records; POD/TRK/SMF/TIFF
read/record limits are additionally enforced by the adapter. Invalid indices,
missing UVs/normals/resources, singular/nonfinite transforms, cyclic parents,
duplicate IDs/JSON keys, path case aliases, Windows device names, linked/reparse
paths, protected output overlap and altered sidecars fail closed. Bounds apply
before allocation where possible and to aggregate output, not only each file.

The minimal implementation deliberately retains source-specific records in
their own fields rather than inventing universal meanings for every flag.
Other sources, a richer rig/LOD model, conversion policies, semantic edits and
MR authoring remain separately reviewed work. See EVO2_SOURCE_ADAPTER_RESULTS.md
for actual-file qualification and Windows preview evidence.


## Backwards-compatible hardening extension — 30 October2026

Existing UVS v1 serialized scenes and MRPV v1/v2 remain unchanged. Optional mesh uv_channels1..3 retain float2 values/evidence with exact vertex association; uvs stays UV0. Per-corner BGRA is checked at save/reopen, and every declared raw source stream is independently bound by path/stride/count/hash to the manifest. Original values, UVs, palettes/extra samples, transforms, streams and unknowns remain immutable. External semantic contracts and explicit native loss policies are described in UNIVERSAL_NATIVE_BRIDGE_QUALIFICATION.md; they do not add source-derived CarIDs/physics or infer alpha/damage from names. Typed Dakar2 UV1 exposure creates separate projects, preserving132 exact UV0 aliases and all original source sidecars.
