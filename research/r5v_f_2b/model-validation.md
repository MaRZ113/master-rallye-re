# R5V-F.2b model validation

No retail-cooked model DX is available yet. Historical rev127 files are
references only; they do not satisfy the native retail-cook gate.

For each new `complete.dx`, `car.dx`, and `wheel.dx`:

1. Record file size, modification time, and SHA-256 immediately after the
   isolated game exits.
2. Parse with the current Vehicle SDK and require revision 135, finite
   geometry/bounds, valid draws/materials, resolved texture references, and a
   valid footer.
3. Compare semantic vertex, triangle, draw, material, texture, and AABB data
   against the matching selected-source rev127 file. Do not demand byte
   identity across revisions.
4. Require tag101 parsing and collision checks for `car.dx` in addition to its
   render model validation.

The copied historical DXT set passed the current round-trip validation:
44/44 files across the root Mercedes and separate `lpha` source families were
byte-identical, with zero header or payload differences. The runtime stages
only the 25 root Mercedes textures. No model output, semantic report, or DX
dependency closure has been validated in R5V-F.2b yet.
