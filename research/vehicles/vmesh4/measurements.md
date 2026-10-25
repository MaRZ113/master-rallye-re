# V-MESH4 measurements (before = V-MESH3 `v3-exp-001`, after = V-MESH4)

Source: `reports/validation-report.json` (`diagnostics_before` / `diagnostics_after`, `converter_reports`) of the V-MESH4 build,
produced by `tools/vmesh_diagnose.py` from the files inside each runtime bundle. Metres. "Physical ground" = hub height minus
the donor wheel radius 0.3832 (the physics XML radius is not changed).

## Stance

| Metric (frontend frame; race frame identical after the frame shift) | V-MESH3 | V-MESH4 |
|---|---|---|
| ride lift applied to body/cabin/crew/hull top | 0 | +0.120 |
| lowest side-skirt vertex above physical ground | 0.055 | 0.178 |
| side skirt p5 above physical ground | 0.091 | 0.243 |
| lowest body vertex above physical ground | 0.054 | 0.174 |
| roof p99 above physical ground | 1.520 | 1.624 |
| body bbox y (race frame) | -0.327 .. 1.453 | -0.207 .. 1.573 |
| hull bbox y (race frame; floor kept at donor hub level) | 0.005 .. 1.139 | 0.005 .. 1.242 |
| hull y scale / translation | 0.732 / -0.208 | 0.799 / -0.156 |
| crew bbox y (race frame) | 0.164 .. 1.006 | 0.254 .. 1.096 |
| frame error of body draws (race vs frontend) | 0.0000 | 0.0000 |
| tyre-slab intrusions (samples) | 0 | 0 |

The 0.12 m = 0.046 (restores the source body-to-ground relation after the visual tyre was shrunk below the physical one)
+ 0.074 (rally clearance). Real-car reference (estimate, not measured here): WRC Impreza ~1.42 m high, x scale 1.163 = 1.65 m.

## Arches

| Metric | V-MESH3 | V-MESH4 |
|---|---|---|
| construction | alpha-carved sub-triangles + vertex push | analytic 24-gon prism cut + tube + wall |
| lip radius from hub (visual tyre 0.337) | 0.367 (gap 0.030) | 0.397 (gap 0.060) |
| lip ring edges (open / total), per hub | 22/44, 39/52, 26/48, 48/83 | 4/31, 0/22, 2/23, 0/22 |
| GT vertices displaced | 146 (mean 0.047, max 0.144) | 0 |
| GT triangles clipped / untouched | n/a | 78 / 709 |
| generated: tube / wall / T-junction splits | n/a | 180 / 91 / 202 |
| area removed (frame scale), 4 openings | n/a | 1.695 m2 (body exists over only part of each opening) |
| normal-vs-winding agreement | 97.5 % | 99.5 % (6502 of 6534 corners) |

## Glass and interior

| Metric | V-MESH3 | V-MESH4 |
|---|---|---|
| GT window panes (Mat6_Tex10, 38 tris, 3.1 m2, alpha 219-255) | opaque black draw 9 | glass draw (car 35 / complete 24), alpha-blended |
| GT glass strips (Mat4_Tex5, 80 tris, 0.4 m2, alpha 65) | glass draw, donor grey ramp | opaque trim (draw 9) |
| glass texture `windscreen32-tga` | donor 32x32 ramp (alpha 16-138) | uniform RGBA(60,78,96,148), same size/header |
| cabin shell inset | 0 | 0.03 |
| cabin roof below shell roof p99 | 0.053 | 0.067 |
| interior points outside the shell bbox | 0 | 0 |
| crew headroom under roof p99 | 0.133 | 0.147 |

## Size

| File | V-MESH3 tris / verts | V-MESH4 tris / verts | donor Navara |
|---|---|---|---|
| car.dx | 2291 / 3233 | 2732 / 3415 | 2366 / 3248 |
| complete.dx | 2761 / 3445 | 3202 / 3627 | 2761 / 3397 |
| largest draw (vertices; limit 65535) | 1282 | 1187 | - |

Retail maximum over all vehicle car/complete files: 2761 triangles (Navara complete), 4174 vertices (IceCream car).

## Known limits of these measurements

* Lip-ring continuity counts welded single-use edges on the lip circle; paint and trim draws are welded positionally in the
  measurement although they are separate draws in the file.
* Clearances use the visual tyre only; steering lock and suspension travel are not modelled.
* Previews ignore texture alpha (Workbench), so glass appears as its flat tint in them; the in-game blend is untested.
