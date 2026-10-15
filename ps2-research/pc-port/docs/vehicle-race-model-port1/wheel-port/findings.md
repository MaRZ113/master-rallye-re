# X-Trail separate WHEEL resource

Original `XTRAIL/WHEEL.PSM` SHA-256 `d53360eab52761fdadf1a4d5a2c87196be7674fbbb603c41cd4726a4b303773c` is independent of CAR and COMPLETE. It contains 300 original vertices, three meshes and 252 nondegenerate source faces. All meshes select original mode 3; primary/secondary texture ordering is preserved, including rubber and chrome secondary sources. No fitted position, normal normalization, generated texture, density reduction or alpha remapping is introduced.

`convert_wheel.py` reuses the existing strict complete reader, original GXI decoder, vertex conversion and strip expansion. It emits both the original three-mesh representation and a four-range runtime representation. The latter partitions root.0 between PC records 0 and 2; root.1 maps to record 1, root.2 to record 3. Each mapping is proved by the complete unsigned float32 position-face multiset, with multiplicity. The union is exhaustive and disjoint: 72 + 36 + 54 + 90 = 252 faces. This is exact source geometry evidence, not permission to use old draw ordinals or pointers at runtime.

The draw resource must be attached to each currently certified original native wheel WORLD separately. Steering, suspension, wheel spin and gameplay remain native. No chassis WORLD may be substituted. Raw UVs are retained in the private file; the confirmed runtime primary V orientation correction remains the consumer's responsibility. Original strip parity remains unresolved, so CULL_NONE follows the accepted model pilot convention rather than claiming exact PS2 culling.

Local ignored outputs:

- `XTRAIL-WHEEL.ps2model`: 66,559 bytes, SHA-256 `6bed8f419f7d73572aaf1af5b38a6cfc9d90deaf9d0d6bf3a3b8e0047a7da27c`.
- `XTRAIL-WHEEL-DRAW.ps2model`: 68,258 bytes, SHA-256 `1c548d537acd75480515ff6d43140215638d2cd87c8b254d509dd5e6d004a31f`.

Reproduce from the repository root: `python ps2-research/pc-port/docs/vehicle-race-model-port1/wheel-port/convert_wheel.py`. Original local PS2 root and protected PC corpus are hash checked. Tests: `python -m unittest discover -s ps2-research/pc-port/docs/vehicle-race-model-port1/wheel-port -p test_wheel.py -v`.

No original resource bytes are committed or included in distributable evidence. Resource generation alone does not establish current wheel owner, reset safety or visible runtime acceptance.
