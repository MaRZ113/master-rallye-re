# R5V-F.2b Mercedes collision gate

**NOT RUN — no retail-cooked `car.dx` exists.** The selected demo source has a
legacy rev127 `car.dx` reference, but it cannot prove that the retail GXM
reader/writer preserved or correctly serialized Mercedes tag101 collision.

When the native retail cook produces `car.dx`, inspect tag101 with the current
R4G collision tools. Require finite base point/scalar and Rep A/Rep B values,
valid face values, expected closure/manifold checks, convexity checks where
applicable, and a serializer round-trip. Compare the result semantically with
the legacy Mercedes rev127 collision. Byte identity is not required.

If authentic Mercedes collision is absent or invalid, record the exact
failure and keep Mercedes P0/P1 blocked. A renderable complete preview or a
successful cache write does not establish valid collision or safe gameplay.
