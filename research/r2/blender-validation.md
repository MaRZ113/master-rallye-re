# R2 Blender validation

## Environment

- Blender: **5.2.2 LTS**, build hash `d13f752e3b9c`
- Platform: Windows
- Expected minimum from used APIs: Blender 4.3+
- Tested version claim: 5.2.2 only

## Automated checks

| Check | Evidence | Result |
|---|---|---|
| Ordinary Python suite | 31 synthetic-only tests | PASS |
| Add-on registration | Both File > Import operators present | PASS |
| Synthetic folder import | Two DX resources; primary has 4 vertices, 2 triangles, 2 materials, tag 7/8 | PASS |
| Editable mesh | Entered and left Edit Mode | PASS |
| Provenance | Point/face IDs, raw colors, source normals, and exact normal bits present | PASS |
| Normal safety | Valid fallback is silent; count mismatch, zero, and non-finite cases warn | PASS |
| Material warning ownership | Shared-cache missing-texture warning stays with its creating resource | PASS |
| Authoring status | Identical -> geometry edited -> identical | PASS |
| Synthetic save/reload | Mesh, materials, images, attributes, JSON/groups retained | PASS |
| ZIP install | Isolated profile enabled `master_rallye_io` | PASS |
| Vendored parser | Installed ZIP imported synthetic DX | PASS |
| Real folder operator | Astero, Pajero, Forester, Bruno, Ufo, and megane folders imported without process failure | PASS |
| Diverse real sample | 19 resources across seven vehicle families, including `sus` | PASS |
| Real save/reload | All 19 returned `SOURCE_IDENTICAL` | PASS |

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

The final real save/reload validation covered 19 resources and referenced 163
cached preview images. Astero and Forester each reported zero warnings. Pajero
reported one genuine existing parser diagnostic from `car.dx` (declared
top-level count 28 versus reconstructed root count 29), and no normal fallback
warnings. Blender warns
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
geometry, or reversed component placement. Blender-specific A/B renders used upright PNGs with direct source V and with
`1 - V`. Direct V makes the Astero `263/elf` and Pajero
`203/BFGoodrich` decals readable; `1 - V` turns them upside-down. Thus the
Blender policy is direct V, independent from the unchanged R1 glTF `flip-v`
policy.

The comparison render PNGs are local validation artifacts and are intentionally not
committed.

## Normal-crash validation

Initial isolated imports did not reliably identify one malformed resource:
Pajero car and wheel passed while complete reproduced the native access
violation. All three contain one source normal per vertex, zero non-finite and
near-zero normals, and magnitudes within float error of 1.0. Replacing the
from-vertices API with explicit per-corner custom normals allowed isolated
imports but still crashed during a multi-folder session.

The root cause is therefore only **partially understood**: the failure is in
Blender 5.2.2 native custom-normal handling/state, not supported by evidence of
bad DX normal data. The final importer calls neither native custom-normal API.
It preserves exact source normals and deliberately uses Blender-calculated
display normals. Valid normals do not warn; abnormal normal data still does.
Pajero car/complete/wheel, the Pajero folder,
the Astero and Forester folders, and the full 19-resource run then passed and survived
save/reload.

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
