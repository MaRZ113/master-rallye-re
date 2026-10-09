# Authored convex collision geometry

Both prop PSM families contain a **tag101** collision section after supported visual nodes and before a four-byte ffffffff trailer. The existing Course SDK strict collision reader independently parses the section; RIGID1 does not create a second collision parser.

| Source | Visual vertices / emitted triangles | Collision start/end | A vertices/triangles | B vertices/triangles | A edges/faces | B edges/faces |
|---|---|---|---|---|---|---|
| Both hay aliases | 74 / 60 | 4060 / 6632 | 8 / 12 | 16 / 28 | 12 / 6 | 24 / 10 |
| Tumbleweed | 96 / 48 | 5203 / 9815 | 8 / 12 | 26 / 48 | 12 / 6 | 56 / 32 |

Each representation has a further one-point, zero-triangle geometry record. Base geometry is also a one-point record followed by a scalar (hay1.5406000614; tumble1.06927502155). These scalars are not interpreted as the authored trigger distance. Visual triangle counts preserve strip ADC suppression and degeneracy rules; they are not physical-shape or live polygon counts.

Canonical source consumer:

```text
PSM tag101 ->38fac0 call38ff08 ->3946e0
 ->3b4c20 [base via3b5278; A/B via3b4cb8]
 ->model+34 convex container
```

`collision-shape-inventory.json` provides offsets, bounds, hashes, compact index hashes and source identities. The two hay payloads are byte-identical, not two separate model geometries. Tumbleweed uses authored convex geometry rather than an inferred sphere; exact A/B narrowphase stage selection remains UNKNOWN.
