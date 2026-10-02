# Mercedes texture and material validation

## Static source closure

- The chosen GXM material tables reference 25 distinct GXI source files plus
  the `Null` sentinel.
- All 25 GXI files exist in the chosen root and each has an existing DXT
  companion. File sizes and hashes are in
  [mercedes-source-manifest.json](mercedes-source-manifest.json).
- All three existing TXT sidecars were included in the hash inventory. Their
  per-role references resolve within the source package: 19 car, 25 complete,
  and 6 wheel uses, with overlap.
- The prior source audit parsed all referenced DXT containers; all 25 existing
  DXT files also byte-match the prior offline GXI→DXT encoder.

## Retail output gate

No retail DXT was generated and no Mercedes material was rendered in retail.
Therefore output magic/header, dimensions, payload length, BGRA/orientation,
alpha behavior, and runtime appearance are **NOT VALIDATED** for native-cooked
files. There are no missing files in the static source-folder inventory, but
the absolute authoring-root references and retail texture-stem lookup remain
unresolved for an isolated cook. Static folder closure must not be reported as
retail runtime closure.

`Null` appears as an explicit source sentinel and is not counted as a missing
GXI. No further alpha/environment-semantic claim is made here.
