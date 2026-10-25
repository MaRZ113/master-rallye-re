# V-MESH3 measurements (before = V-MESH2 `exp-001`, after = V-MESH3)

Source: `reports/validation-report.json` (`diagnostics_before` / `diagnostics_after`), produced by `tools/vmesh_diagnose.py`
from the files inside each runtime bundle. All lengths in metres.

## Frames and wheel anchors (Navara donor)

| Quantity | Value | Basis |
|---|---|---|
| `complete.dx` - `car.dx` vertical offset dy | 0.3932 (spread 0.0003) | 10 identical draws, dx/dz < 4e-5 |
| donors where the relation is a pure dy | 22 of 25 | IceCream, Kamaz, Xtrail also differ in z or by draw |
| hubs, frontend frame (x, y, z) | (+-0.84, 0.395, +1.495 / -1.463) | bbox centres of the embedded wheel draws |
| hubs, race frame (hypothesis H1) | (+-0.84, 0.002, +1.495 / -1.463) | complete hubs - dy |
| donor visual wheel radius / half width | 0.3832 / 0.1460 (`wheel.dx`) | file |
| XML `WheelBase` / hub spacing | 2.80 / 2.957 | XML vs rendered: not equal |

## GT Impreza (`sb0097`) and the fit

| Quantity | Value |
|---|---|
| wheelbase (LOD0 wheel-arch gaps, front z -1.3025, rear +1.240) | 2.5425 |
| tyre radius (estimate; reference view + arch tops 0.52-0.60) | 0.29 |
| uniform body scale = donor hub spacing / GT wheelbase | 1.1632 |
| visual wheel scale k = scale x r_gt / r_donor | 0.8802 (visual tyre r 0.3373, half width 0.1285) |
| expected tyre hover if physics still uses r 0.383 | 0.046 |
| body (race frame) bbox | x +-1.058, y -0.327..1.453 (roof p99 1.139), z -2.572..2.536 |
| body (frontend frame) bbox | y 0.066..1.846 (roof p99 1.540) |
| ground clearance (frontend frame, body bottom 0.066 - physical ground 0.395 - 0.383 = 0.012) | 0.054 |

## Before / after

| Metric | V-MESH2 | V-MESH3 |
|---|---|---|
| frame error of body draws (race vs frontend) | -0.3932 | 0.0000 |
| tyre-slab intrusions frontend (samples / max depth) | 3 / 8 mm, 5 / 8 mm (two hubs) | 0 / 0 |
| tyre-slab intrusions race frame | 0 (but body 0.39 high) | 0 |
| arch lip gap, race frame, per hub | +0.120, +0.029, +0.120, +0.029 | +0.030 x 4 |
| arch lip gap, frontend frame, per hub | +0.031, -0.169, +0.031, -0.169 | +0.030 x 4 |
| GT vertices pushed by relief / arch snap | ~100 corners, tyre-based | 146, mean 0.047, max 0.144 (carved-edge snap only) |
| `car.dx` triangles / vertices (donor 2366 / 3248) | 1930 / 2758 | 2291 / 3233 |
| `complete.dx` triangles / vertices (donor 2761 / 3397) | 2285 / 3031 | 2761 / 3445 |
| paint draw (draw 3) triangles | 618 | 1020 |
| crew top - roof headroom (race frame) | 0.104 (crew in the wrong frame) | 0.133 |
| crew bbox y (race frame) | 0.538..1.379 | 0.164..1.006 |
| donor leftover `underdash` above roof | -0.108 (inside, wrong shape) | removed (GT cabin shell) |
| hull bbox y (race frame) | 0.005..1.480 | 0.005..1.139 |
| hull scale / translation | (1.026, 0.952, 0.975) / (0, -0.037, +0.225) | (1.026, 0.732, 0.975) / (0, -0.208, +0.225) |
| normal-vs-winding agreement (complete) | 99.5 % | 97.5 % (129 of 5211 corners; carved/snapped triangles) |
| alpha: wheel-opening sub-triangles removed / area | n/a | 413 / 1.08 m2 (frame scale) |
| alpha: invisible/overlay triangles dropped | 0 | 44 |
| fillers (car / complete) | 24 / 16 | 24 / 16 (now inside the GT cabin) |

## Known limits of these measurements

* Lip gap uses actual vertices on the outboard side above the hub; the arch edge is a carved, rounded polygon
  (adaptive depth 3, cell = triangle edge / 8), not a smooth surface.
* "Intrusion" tests the body against the *visual* tyre cylinder only; physical tyre radius and suspension travel are not modelled.
* Crew sits 0.22 m below the GT cabin floor plane (donor driver is tall); only the upper body is visible.
