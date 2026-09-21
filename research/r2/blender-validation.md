# R2 Blender validation

## Environment

- Blender: **5.2.2 LTS**, build hash `d13f752e3b9c`
- Platform: Windows
- Expected minimum from used APIs: Blender 4.3+
- Tested version claim: 5.2.2 only

## Automated checks

| Check | Evidence | Result |
|---|---|---|
| Ordinary Python suite | 26 synthetic-only tests | PASS |
| Add-on registration | Both File > Import operators present | PASS |
| Synthetic direct import | 6 vertices, 2 triangles, 2 materials, tag 7/8 | PASS |
| Editable mesh | Entered and left Edit Mode | PASS |
| Provenance | Point/face IDs and raw color bytes present | PASS |
| Authoring status | Identical -> geometry edited -> identical | PASS |
| Synthetic save/reload | Mesh, materials, images, attributes, JSON/groups retained | PASS |
| ZIP install | Isolated profile enabled `master_rallye_io` | PASS |
| Vendored parser | Installed ZIP imported synthetic DX | PASS |
| Real folder operator | Astero discovered car/complete/wheel | PASS |
| Diverse real sample | Eight resources across four vehicle families plus `sus` | PASS |
| Real save/reload | All eight returned `SOURCE_IDENTICAL` | PASS |

The generated synthetic fixture contains no game bytes. It has two physical
draws, a tag-7 group with tag-8 child, two preview materials, and asymmetric
2x2 texture rows so raster/UV orientation cannot pass through two canceling
mistakes.

## Real resource sample

All sources were read from the external extracted archive and never modified.
Outputs were written only to ignored `.research-output/r2`.

| Resource | Verts | Tris | Draws | Groups | Trailing | Result |
|---|---:|---:|---:|---:|---|---|
| Astero/complete.dx | 2,657 | 2,423 | 24 | 24 | footer56-bounds | PASS |
| Astero/car.dx | 2,543 | 2,021 | 32 | 27 | opaque | PASS |
| Astero/wheel.dx | 220 | 252 | 5 | 5 | footer56-bounds | PASS |
| Bruno/car.dx | 2,455 | 2,014 | 21 | 19 | opaque | PASS |
| Bruno/wheel.dx | 220 | 252 | 5 | 5 | footer56-bounds | PASS |
| ChevyBlazer/car.dx | 2,713 | 2,156 | 36 | 32 | opaque | PASS with known diagnostic |
| Ufo/complete.dx | 837 | 670 | 6 | 6 | opaque | PASS |
| megane/sus.dx | 48 | 48 | 1 | 1 | opaque | PASS |

The real save/reload file referenced 81 cached preview images. Blender warns
that absolute OS-temporary paths cannot be made relative to a temporary
`.blend`; the paths and files nevertheless survived and were verified after
reload. The add-on does not pack decoded game textures automatically.

## Astero visual proof

A clean Blender scene imported `Astero/complete.dx` directly and rendered
orthographic side plus three-quarter views in Eevee. Observed Blender bounds
were:

```text
minimum (-1.018168, -2.164272, -0.000733)
maximum ( 1.018168,  2.154167,  1.850730)
```

The mapping `(X, -Z, Y)` puts the vehicle upright on Blender +Z at native
scale. The body, wheels, bull bar, windows, and lights form a coherent assembly.
There are no exploded triangles, cross-draw spikes, missing groups, duplicated
geometry, or reversed component placement. Directional body art, roof/door
numbers, and Michelin graphics are upright and align with the accepted R1
preview under the corrected `flip-vertical PNG + flip-v model UV` policy.

The two render PNGs are local validation artifacts and are intentionally not
committed.

## Reproduction commands

```powershell
py -3 -m unittest discover -s tests\synthetic -v

py -3 tests\blender\generate_fixture.py .research-output\r2\synthetic-fixture

& "<blender.exe>" --background --factory-startup `
  --python tests\blender\import_smoke.py -- `
  ".research-output\r2\synthetic-fixture" `
  ".research-output\r2\synthetic-import.blend" `
  ".research-output\r2\synthetic-report.json"

py -3 tools\build_blender_addon.py

& "<blender.exe>" --background --factory-startup `
  --python tests\blender\addon_install_smoke.py -- `
  "dist\master_rallye_io-r2.zip" `
  ".research-output\r2\synthetic-fixture\synthetic.dx"
```

Developer-only real-resource checks are `validate_real_vehicles.py` and
`render_vehicle_preview.py`; their arguments must point at the user's
external read-only game extraction and ignored output locations.
