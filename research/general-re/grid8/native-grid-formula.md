# Native eight-car grid formula

## Evidence boundary

The normal path is native retail `0x0048EB40`, inspected in the current
Ghidra 12.1.4 export at
`research-output/general-re/persistence/writer-owners/0048eb40.{asm,c}.txt`.
The tiny float-to-integer helper at `0x005C2E5C` was separately checked in the
exact retail x86 bytes: it saves the x87 control word, sets round-control to
truncate, executes `FISTP`, then restores the control word. This is static
executable evidence, not a physical collision test.

The function reads `RaceTest`'s first two `StartArea` `Marker Pos` entries:

- `P0` at the first marker object's `+0x38,+0x3C,+0x40`;
- `P1` at the second marker object's `+0x80,+0x84,+0x88`.

Define the horizontal forward direction from `P0` to `P1`:

```text
d = normalizeXZ(P1 - P0)
side = normalizeXZ(-d.z, 0, d.x)
L = length3D(P1 - P0)
K = trunc(abs(L * 0.1666666716))
if K == 0: K = 2
```

`0.1666666716` is the retail float at `0x00690D4C`. `K` is the count of cars
per longitudinal row. For position ordinal `i=0..7`:

```text
row = i // K
column = i % K
slot = 7 - i                         # normal Ghost OFF path
position = P1 - d*(L/2) - d*(6*column) - side*(8*row)
forward = d
up = (0,1,0)
```

The function writes the corresponding `Race/CarN/Transform`; slot enumeration
begins at Car7 and decrements. Longitudinal spacing is six world units and each
new row moves eight units along negative `side`. The transform builder records
the orientation basis and a yaw only under the explicit convention that local
forward is positive Z; the basis vectors are the primary orientation result.

Ghost-specific participant skipping is routed through `0x0048E9C0` and is not
modeled here. The candidate forces Ghost OFF. Exact per-instruction float
rounding in the Python-derived world positions may differ by small ULPs; all
input coordinates are rounded to their native float32 storage first. The
resulting [grid8-predicted-transforms.json](grid8-predicted-transforms.json)
contains 288 derived slot transforms, all marked prediction-only.

The algorithm predicts positions and orientation. It does not include vehicle
collision radii, terrain shape, static objects, authored boundaries, or
initial physics impulses. Therefore the clearance field remains unknown for
every course until human runtime observation.
