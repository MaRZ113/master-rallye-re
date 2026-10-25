# V-MESH4 - Subaru geometry and glass polish

**Status: READY_FOR_HUMAN_RUNTIME. Not runtime-qualified. No runtime PASS is claimed.**
V-MESH3 (`v3-exp-001`) was human-confirmed to improve body/wheel alignment; its findings (too-low stance, visible
arch cut-outs with edge artifacts, dark/opaque windows with transparent edges, crew visible through parts of the glass)
are the input of this phase. The addon identity, J.3-B runtime bundle and launcher flow are unchanged (addon plan SHA256
`567a27a8f3c978bebd2a6600710b89779d16ddece7cd983630d286338490477b` is identical to V-MESH2/3; `wheel.dx` is byte-identical
to V-MESH3). GT3 data, derived `.dx`/`.dxt` and the bundle stay private under `.research-output/`.

## Defects, origin and change

| Visible defect (V-MESH3) | Origin | Evidence | V-MESH4 change |
|---|---|---|---|
| Body sits too low | **Fit/conversion.** The GT car is a low tarmac car; scaling it about the hubs and shrinking the visual tyre (0.337 m) below the physical one (0.383 m) leaves the body 4.6 cm lower relative to the physical ground than in the source, so the skirt cleared the ground by only 5.5 cm | `measurements.md`: skirt 0.055 m, roof 1.52 m above physical ground | `--ride-lift 0.12`: the body, cabin, crew and hull top move up 12 cm; hubs/wheels/physics are not touched. Result: skirt 0.178 m, roof 1.62 m (scaled real WRC Impreza ~1.65 m, estimate) |
| Arches look cut out, stair-stepped edge, void behind | **Conversion.** V-MESH3 baked the source's texture-alpha cut-outs (adaptive sub-triangles) and then pushed vertices out of the tyre; both leave a serrated lip and an open hole through a thin sheet | role-colour renders; lip ring: 22-48 of 44-83 edges open | analytic cut: every paint/trim triangle is clipped against an N-gon prism (N = 24, circumscribing R = visual tyre + 6 cm) around each hub, the new edges form the lip, a tube (lip -> wall 6 cm inboard of the tyre) and an inboard wall close the wheel house. No vertex is moved, no source triangle outside the opening is changed. Lip ring: 0-4 of 22-31 edges open (chain ends at the sill) |
| Windows mostly dark/opaque, glass edges transparent, crew visible through parts | **GT geometry classification (V-MESH1 rules) + donor glass texture.** The GT panes (`Mat6_Tex10`, 38 tris, 3.1 m2, texture alpha 219-255, near black) were classed as *black trim* and drawn opaque by the donor `black-tga` draw; the only geometry in the glass role (`Mat4_Tex5`, 80 tris, 0.4 m2, alpha 65) is a set of thin frame/mullion strips, drawn with the donor `windscreen32` grey ramp (alpha ~0.5). So the panes were opaque and only the strips blended | `after_role` renders; draw 9 vs draw 24 isolated renders | panes are detected by texture alpha/luminance (not by name) and routed to the donor glass draw (alpha-blended); the thin GT glass strips become opaque trim (window seals). The donor glass texture `windscreen32-tga` is replaced (same-size DXT edit, the R4D.1 M2 mechanism) by a uniform tint `RGBA(60,78,96,148)` (alpha 0.58) so every pane has the same transparency |
| Cabin shell touches/pokes the roof edges | **Conversion.** The GT cabin shell is coplanar with the paint roof at the pillars | interior vertices vs shell | shell shrunk 3 cm about its centre (`interior_inset`) |
| Race vs frontend | consistent in V-MESH3 | frame test | unchanged; one transform per frame, same body/arch/glass in both |

## What is generic and what is not

* `tools/vmesh_arch.py` - donor/vehicle agnostic: `WheelHouse` (hub, radius, inboard wall, N), `cut_wheel_houses` (clip,
  area-conserving, winding-preserving), `build_liner` (tube + wall from the lip edges), `split_tjunctions` (the clipping
  fragments are re-split so no T-junctions remain; a closed lip is watertight, see tests).
* `tools/vmesh_geometry.py` - `BuildOptions` (V-MESH4 defaults, `BuildOptions.v3()` reproduces V-MESH3), `FitPlan.lift`,
  `find_glazing_materials` (texture-measured: Mat6 class, min alpha >= 128, mean alpha <= 245, mean luminance <= 80; when no
  material qualifies the V-MESH3 role mapping stays), interior inset. Nothing here names Subaru.
* Subaru/Navara specifics stay in the driver `tools/build_vmesh4_impreza_experimental.py`: donor draw roles (`PROFILES`), the
  lift value, the glass tint, the project JSON.
* `tools/vmesh_diagnose.py` gained reusable measurements: `ground_clearance`, `open_edges_near_wheels` (lip continuity),
  `interior_containment`. `tools/vmesh_preview.py` renders texture/role previews (Blender, private, diagnostic only).

## Reproducible build

```powershell
$env:PYTHONPATH = 'src;.'
python tools/build_vmesh4_impreza_experimental.py `
  --gt-dir ".research-output/vehicles/gt-import/gt3-dumps/sb0097/sb0097_dump/CarModelSet" `
  --retail-root "D:/Game/Master Rallye/corpora/retail" `
  --retail-exe "D:/Game/Master Rallye/MRallye.exe" `
  --before-candidate-dir ".research-output/vehicles/vmesh3/v3-exp-001/runtime/resource-root/DataGx/Vehicles/ImprezaProto" `
  --output-root ".research-output/vehicles/vmesh4/v4-exp-001" `
  --blender "C:/Program Files (x86)/Steam/steamapps/common/Blender/blender.exe"
python -m unittest tests.synthetic.test_vmesh_arch tests.synthetic.test_vmesh_geometry tests.synthetic.test_vmesh_gt3_to_dx
```

Tuning knobs (re-run with a new output root; everything else is unchanged): `--ride-lift` (m), `--arch-gap` (m),
`--arch-sides`, `--glass-alpha` (0..1), `--glass-rgb R,G,B`. The glass look is the least certain value (see below):
try `--glass-alpha 0.75` for darker/less see-through glass or `0.45` for lighter.

## First in-game test (human)

Same launcher flow as V-MESH2/3 (`research/vehicles/vmesh/README.md`, "First in-game test") on
`.research-output/vehicles/vmesh4/v4-exp-001`: first `mr-runtime-launcher.exe --verify <MRallye.exe> <runtime>` (expect
`RESOURCE_ROOT_VERIFIED files=187 ...` and `RUNTIME_BUNDLE_VERIFIED patch_operations=246 plan_sha256=567a27a8...`), then
`--integrated`. Check and report pass/fail with screenshots:

1. **Stance.** Side view standing still and driving: is the ride height now right, not scraping, not floating? The wheels
   still hover ~4.6 cm (visual tyre smaller than physics) - is that visible?
2. **Arches.** Front and rear, from the side and 3/4: clean round opening, dark liner behind, no jagged edge, no sparkle/pinholes
   along the lip, no see-through to the sky. Steer to full lock and compress the suspension (bumps): does the tyre touch the
   lip or the liner wall?
3. **Windows (race).** All panes uniformly tinted and see-through, frames black. Is the transparency level right? Do the crew
   and interior look coherent through the glass (driver at the wheel, roll cage, seats)? Any pane that is opaque, missing or
   shows the sky/cabin back faces?
4. **Windows (frontend, Vehicle Select).** Same look as in the race?
5. **Glass damage.** Crash into something until the windscreen breaks: what happens to the glass (all panes vanish with
   the front-screen group? any crack texture? flicker)? Known open point, see below.
6. **Cabin shell / roof edges.** Any dark line or poke-through at the pillar tops/roof edges?
7. **Cameras.** Cockpit/bonnet camera inside or above the (now 12 cm higher) roof?
8. **Collision/damage.** Wall hits at the visible body edge, deformation, loss of paint/body parts as in V-MESH3.
9. Brake light/glow, headlamps: unchanged from V-MESH3 (secondary, not part of this phase).

## Unresolved / blockers (not hidden)

* **Glass damage states.** The donor has paired intact/cracked glass draws behind group switches (`screenfront`, `screenleft`,
  `screenright`, `screenrear`); the group child order is not uniform (draws 31/33 carry the label on the cracked child),
  so which child is default is not proven for every window. All GT panes therefore sit in the one draw that was already proven
  visible (car.dx draw 35 `screenfront`, complete.dx draw 24); the cracked draws remain hidden fillers. Consequence to be
  observed (test 5): breaking the front screen may remove all panes at once and no crack texture appears. Splitting the panes
  per window zone and filling the cracked draws needs the group selector semantics (runtime evidence).
* **Glass tint/alpha** (`RGBA(60,78,96,148)`, vertex grey ~0.67 of the donor glass draw, env helper `glass-tga` active with
  Reflections ON) is derived from the GT panes (alpha 0.86, near black) and the R4D.1 M2 result; the in-game look is untested.
* **Triangle budget.** car.dx 2732 / complete.dx 3202 triangles (V-MESH3 2291 / 2761; retail maximum 2761). R4G confirms
  that triangle counts can differ from the donor and that only the per-draw uint16 local-index limit applies (largest draw here:
  1187 vertices), but no larger-than-retail file has been loaded by the engine in a confirmed test. `--arch-sides 16` removes
  ~250 triangles (2484 / 2954) if needed.
* **Lip/tube seams.** The tube and wall are trim-draw (black) triangles, the cut body panels are paint-draw triangles: their
  edges coincide but are different draws, so a rasteriser sparkle along the lip is possible (test 2). The lip ring is open
  only at chain ends (sill/bumper boundary of the GT shell).
* **Arch clearance in motion.** The opening has a constant 6 cm gap to the *visual* tyre (donor arch gaps 4-8 cm). Steering
  lock moves the tyre edge fore/aft by up to ~6 cm and suspension travel (XML MaxBounce 0.30) is not modelled.
* Still open from V-MESH3 (unchanged): native proportions (engine/physics wheel-anchor mapping unresolved, H1 unverified), physical
  tyre radius 0.383 vs visual 0.337, cockpit camera vs roof, hull is a refit of the donor convex hull (floor at hub level),
  filler draws, brake-light/glow and cracked-glass visuals.
