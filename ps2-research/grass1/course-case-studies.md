# Controlled course cases

All four resources were freshly read through validated PackFS and compared
with CDELTA1 cache bytes. Exact decoded hashes, material offsets and counts are
in [case-evidence.json](case-evidence.json). Counts below concern source
triangles and bounded offline inputs, not screenshot-visible decorations.

| Course | Grass slope/category pass | Shrubs slope/category pass | Special control |
|---|---:|---:|---|
| FRANCE1 | 5,193 | 1,463 | Stones567 bound /555 slope-pass /0 eligible |
| ITALY_S1 | 3,239 | 1,158 | No stones required; harddirt and grass category differences persist |
| TURKEY_S1 | 3,348 | 1,782 | Singular material11:343 bound /153 slope-pass /0 eligible |
| SPAIN1 | 3,248 | 2,188 | Additional country, no stones; same parser/source path |

France1 material identities are the spatial table's zero-based indices:

| ID | Surface | Detail | Bound triangles | Slope-pass | Eligible |
|---:|---|---|---:|---:|---:|
| 0 | gravel | none | 1388 | 221 | 0 |
| 1 | gravel | grass | 1941 | 215 | 215 |
| 2 | grass | shrubs | 3944 | 1244 | 1244 |
| 3 | grass | grass | 4068 | 1612 | 1612 |
| 4 | harddirt | grass | 4257 | 3366 | 3366 |
| 5 | water | missing → none | 3205 | 3158 | 0 |
| 6 | harddirt | stones | 567 | 555 | 0 |
| 7 | tarmac | none | 1678 | 1334 | 0 |
| 8 | harddirt | none | 1114 | 900 | 0 |
| 9 | harddirt | shrubs | 360 | 219 | 219 |
| 10 | mud | none | 542 | 176 | 0 |

A material labeled grass does not automatically select grass sprites.
Harddirt material4 vs material8 gives a positive/negative control in the same
model: source triangles **9174** vs **16967**, both satisfying slope, differing
in category. Stones triangle **16297** also satisfies slope but is excluded.
The `$grass(off)` long visual strings remain a separate unbound render/cooker
question; no override is inserted into these actual short-table bindings.

Italy_S1's harddirt grass material3 supplies selected source triangle **8681**.
Turkey_S1 uses plural shrubs in materials3/4 and singular shrub in material11;
selected singular triangle **16696** is rejected by category. Spain1 material3
harddirt grass supplies triangle **8390**, the fifth case's cross-country check.

| Diagnostic source | Explicit synthetic full-triangle activation count | Accepted CPU records with synthetic center/scale |
|---|---:|---:|
| France1 grass9174 | 32 | 32 |
| France1 shrubs1231 | 80 | 80 |
| France1 none16967 | 0 | 0 |
| France1 stones16297 | 0 | 0 |
| Italy_S1 grass8681 | 15 | 15 |
| Turkey_S1 singular16696 | 0 | 0 |
| Spain1 grass8390 | 31 | 31 |

These use original source coordinates but **synthetic** activation, nearest-even
hash rounding, centroid camera center, projection-scale64 and vertical-factor1.
Every output is ignored and repeated with equal SHA256. They verify the bounded
reconstruction, not actual initial placement, camera-history clipping or PS2
visible primitive counts.

The remaining corpus receives structural checks only. All **36** models have
one validated spatial table and consistent material/source-index binding;
no full visual geometry/instance reconstruction was required. Spain2's
detail-none-only material also demonstrates that a surface-type token is not
mandatory. No tree/scene-object population is counted as material decoration.
