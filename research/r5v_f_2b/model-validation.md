# R5V-F.2b model validation

`complete.dx` has now been retail-cooked and passed revision-135 SDK
validation. Its size/hash, complete parser report, and semantic comparison to
the selected demo-8.4.1 rev127 reference are recorded in
`research-output/r5v_f_2b/cook-a/complete-cook-validation.md` and `.json`.
The car and wheel outputs are not present yet, so their validation gates remain
open.

For the remaining `car.dx` and `wheel.dx` outputs:

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
only the 25 root Mercedes textures. For `complete.dx`, all 20 non-null texture
references resolve to staged files and appear in the retail load log. This
does not validate yet-unproduced `car.dx` or `wheel.dx` dependencies.
