# V-MESH4.10 — final Subaru cleanup

2026-10-23. Branch `research/vehicles`. Baseline: private V4.9 `v49-exp-004`.
Candidate: `.research-output/vehicles/vmesh410/v410-exp-002`.

## Changes

| Area | Actual runtime asset change | Boundary / limitation |
|---|---|---|
| Tyre bead | `mercwheel64-tga.dxt` contains only resampled stock Navara rubber. Rubber extends into the otherwise unused centre, preventing bilinear samples from picking up gold rim pixels. | Stock tread and inboard texture retained byte for byte. Native filtering/mip behaviour still needs the game check. |
| Rim interior | Nonreflective pixels between spokes now depict a restrained dark brake disc, hub and barrel with subtle radial bands. | Opaque draw, source metallic RGB and reflection alpha retained. This is a baked appearance, not a recovered GT3 brake mesh. Recess and every wheel geometry byte are unchanged. |
| Brake glow | Existing halo clipped against actual taillight triangles and conformed 1.5 mm above the lens, with a small inset. 28 halo triangles become 100; UV/colour interpolation retains the stock glow pattern. | Native switch, input binding, lit patch geometry, textures and case metadata unchanged. Surface conformity intentionally replaces the donor halo's protruding depth. The user confirmed baseline braking behaviour; the revised glow still needs oblique runtime inspection. |
| Intercooler | A narrow backing annulus extends behind the existing opening frame: 12 mm padding / 12 mm depth, 16 two-sided triangles per body frame. | Mouth, radiator panel and vents retained. This addresses a bounded perimeter gap; it is not a claim that the front is watertight from every camera angle. |
| Headlights | Four existing lower cap panels gain simple reflector/bulb shading via subdivision: 512 triangles per body frame. A guarded, unused 7×7 swatch in the existing 64×64 lamp atlas supplies the material. | Original opaque caps, covered upper housings and glass retained. Detail lies 0.35 mm forward of the caps, behind the glass. Simplified visual detail, not original GT3 optical geometry. |

All original body triangle positions, UVs, normals and colours remain exact. Additions are consistent between `car.dx` and `complete.dx`; the native brake switch applies only to the race car. No livery repacking, rear decal edits, body material reclassification, collision change or wheel relocation.

## Reusable logic

`tools/vmesh_final_cleanup.py` contains opt-in operations on existing geometry/material slots:

- Tyre-only texture extension beneath an enlarged rim bead.
- Opaque, dark wheel-interior shading restricted to nonreflective texels.
- Convex projection admission, triangle clipping and surface conformity for a native lamp halo. Concave/overlapping projections outside the admitted tolerance fail closed.
- Simple detail on explicitly selected planar lamp caps.
- Bounded recess backing annulus that does not cover the opening mouth.

`subaru-cleanup.json` holds model-specific source face selectors and limits. The builder binds them to exact baseline DX hashes, inherits the existing SDK project and collision transform, and uses existing material slots. These operations are optional finishing tools, not universal automatic repairs for arbitrary cars.

## Build / validate

```powershell
C:/Python315/python.exe tools/build_vmesh410_impreza_experimental.py --before .research-output/vehicles/vmesh49/v49-exp-004 --output .research-output/vehicles/vmesh410/v410-exp-002 --profile research/vehicles/vmesh410/subaru-cleanup.json
C:/Python315/python.exe tools/validate_vmesh410_candidate.py --stage .research-output/vehicles/vmesh410/v410-exp-002 --before .research-output/vehicles/vmesh49/v49-exp-004 --previews
```

Builder refuses to overwrite an existing output. Use a fresh stage name when rebuilding.

## Deferred

Race wheel positions, offsets, physics and suspension remain for the physics phase. Lancer source-specific selectors/material decisions require its own inspection. Further optical fidelity, genuine brake assemblies and texture-resolution changes are outside this final pass.

No game launch, publication, push, EXE patch or graphics DLL change. Private converted assets stay under ignored `.research-output`; the review archive contains source, tests, documentation and compact validation evidence only.
