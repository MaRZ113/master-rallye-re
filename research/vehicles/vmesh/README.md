# V-MESH2 - experimental GT3-Impreza body on the J.3-B Navara addon pipeline

**Status: READY_FOR_HUMAN_RUNTIME. Not runtime-qualified.** Nothing here has been run in the game.
The GT3 extraction, the derived `car.dx` / `complete.dx` / texture and the runtime bundle are
**private research material** (gitignored under `.research-output/`); this directory and the review
archive contain only source, metadata, reports and hashes.

## What it is

A donor-draw mesh swap, built entirely from existing, runtime-confirmed SDK pieces:

| Piece | Source |
|---|---|
| Subaru Impreza body, LOD1 (2,263 tris) | GT3 `sb0097` (private), converted by `tools/vmesh_gt3_to_dx.py` |
| Draw structure, materials, collision, wheels, physics | stock Navara donor (only donor the J.3-B runtime profile supports) |
| Topology rebuild | existing `topology_writer.rebuild_topology` (R4F/R4G, human-confirmed) |
| Collision fit | existing `collision_scale` + `collision_translation` (C1, human-confirmed) |
| Paint | same-size DXT edit of Navara `colour-tga` (flat 16x16 blue, `texture_edits`) |
| Addon identity / runtime bundle / launcher | J.3-A `addon init/project-*`, J.3-B `runtime-prepare/verify/launcher-build` (unmodified) |

Identity: ID27 / T2 / local 7, family `ImprezaProto`, display "SUBARU IMPREZA PROTOTYPE" (Mercedes ID26 is
bundled as the J.3-B layout requires). Physics, audio profile, unlock and AI policy are inherited Navara/Glacier-style values.

## Reproducible build

```powershell
$env:PYTHONPATH = 'src;.'
python tools/build_vmesh_impreza_experimental.py `
  --gt-dir ".research-output/vehicles/gt-import/gt3-dumps/sb0097/sb0097_dump/CarModelSet" `
  --retail-root "D:/Game/Master Rallye/corpora/retail" `
  --retail-exe  "D:/Game/Master Rallye/MRallye.exe" `
  --output-root ".research-output/vehicles/vmesh2/exp-001"
python -m unittest tests.synthetic.test_vmesh_gt3_to_dx
```

The driver refuses to overwrite, checks the retail EXE SHA256
(`bf8aef32407eb6552c05045b8abef149f32983cedd9503b865069b444c5f96b4`) before and after, and runs in order:
`convert (car, complete)` -> `addon init` -> `validate-vehicle` -> `addon project-validate/project-build/verify` ->
`addon runtime-prepare/runtime-verify/runtime-launcher-build` -> launcher `--verify` -> structural checks and risk
analysis -> `reports/validation-report.json` -> review archive. Every `mrtool` call is logged in `reports/commands.log`.
Individual converter use:

```powershell
python tools/vmesh_gt3_to_dx.py --profile car --obj <model0.lod1.obj> --axle-obj <model0.lod0.obj> `
  --donor-car-dx <Navara/car.dx> --output car.dx --report car.report.json
```

## Conversion rules (summary)

* GT frame: metres, Y-up, front -Z, CCW-outward. Master Rallye front is +Z: 180 degree yaw (handedness/winding preserved).
* Wheelbase measured from LOD0 wheel-arch gaps (2.5425 m); Navara hub centres measured from `complete.dx`
  (2.958 m) -> uniform scale **1.1634**, axle midpoints aligned. See [scale-and-risks.md](scale-and-risks.md).
* Excluded GT faces: `*_reflection` env shells, lit-lamp duplicate overlay, untextured `Mat-1` shells
  (GT cabin shell `shape28` is used only in `complete.dx`).
* `Mat4_*` -> glass, `Mat6` tail/head lamp objects -> lamps, other `Mat6_*` -> black trim, the rest -> body paint.
* All GT UVs are discarded: each draw samples one chosen donor texel (flat paint/black, grey glass, light lens, red tail lamp).
* Vertices inside a margin-expanded donor wheel cylinder are pushed radially out (arch relief).
* Draw roles (Navara): `car.dx` paint 3, black 9, tail lamp 24, head lamp 25, glass 35; keep 0,1,2,16-20 (interior/driver);
  the other 24 draws become one hidden 2 cm triangle. `complete.dx`: paint 3, black 9, tail 16, head 25, glass 24,
  interior 0 (GT cabin shell); keep wheels 20-23; the other 16 draws become fillers.

## First in-game test (human)

Optional control first: run the unmodified-Navara `GlacierSprint` bundle from the J.3-B handoff to learn whether the
custom-family T2 slot itself works. If this Subaru bundle fails to load and Glacier also fails, the cause is the slot,
not the mesh.

Paths below are relative to the vehicle worktree; `$retail` is the original game `MRallye.exe`.

```powershell
$root = '.research-output/vehicles/vmesh2/exp-001'
$retail = 'D:\Game\Master Rallye\MRallye.exe'
Get-FileHash $retail -Algorithm SHA256        # must be bf8aef32407eb6552c05045b8abef149f32983cedd9503b865069b444c5f96b4
& "$root/launcher/mr-runtime-launcher.exe" --verify $retail "$root/runtime"
#   expect RESOURCE_ROOT_VERIFIED files=187 ... and RUNTIME_BUNDLE_VERIFIED patch_operations=246 ...
& "$root/launcher/mr-runtime-launcher.exe" --integrated $retail "$root/runtime"
```

Then, in the game:

1. Vehicle Select, T2 class, last slot (local 7): name should read **SUBARU IMPREZA PROTOTYPE**; the 3D car should be a
   **blue Impreza saloon with wing and four wheels** (not a Navara pickup). The 2D icon/art is a stock frame and is expected
   to be wrong ("Menu icon" in scale-and-risks.md section 4).
2. Start one short single-player T2 Quick Race with that car. Check: loads without crash, car sits on the ground, wheels
   turn inside the arches, it drives (Navara physics), walls/other cars collide at the visible body edge, windows, headlamps
   and tail lamps look sane, chase/bonnet camera not clipped by the interior.
3. Optionally brake/crash to see damage, glass and brake-light behaviour (known weak points, see risks).
4. Quit; hash the EXE again (must be unchanged). To disable the mod simply launch the game normally.

Report back: pass/fail per item, screenshots (Vehicle Select, in-race side view, wheel arch close-up, rear lights),
any crash or stall, and whether the car looked too big. Do not delete saves/profiles. Remove only the external
`exp-001` bundle/launcher after testing if desired.
