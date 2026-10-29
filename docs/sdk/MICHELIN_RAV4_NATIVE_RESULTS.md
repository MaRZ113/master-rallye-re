# Michelin Toyota RAV4 native pilot — 30 October 2026

One private Source Fidelity MR addon, **MichelinRav4**, is built through the existing Universal Scene→MR bridge, scene DX writer, addon registry and qualified 30-entry roster. Original Michelin decoder/UVS schema are unchanged. The shared bridge adds optional evidenced proper local wheel rotations and optional source-corner-color preservation, with fail-closed validation; older profiles keep their existing defaults. No second importer/compiler, fleet conversion, Mégane CarID or accepted-project replacement.

## Project and launch

Private project: `.research-output/vehicles/michelin-native/final-pilot/workshop`.
Owner candidate: `.research-output/vehicles/michelin-native/final-pilot/builds/source-fidelity/candidate/Launch-SDK-Roster.cmd`.
Original inputs: `final-pilot/inputs/source-scene`; immutable compiled source baseline: `source-baseline/assets`; authored native resources: `converted/assets`. Source snapshots include original texture palettes, all PDO/decoded LOD/damage evidence already retained by accepted UVS.

Open with:

```powershell
python tools/rally_workshop.py --project .research-output/vehicles/michelin-native/final-pilot/workshop
```

Regenerate into a **fresh** private directory:

```powershell
python tools/create_michelin_rav4_pilot.py --scene .research-output/vehicles/michelin-assembly/final/Car25A/assembly/scene/scene.json --donor '../corpora/retail/Data.sma_unpacked/DataGx/Vehicles/Forester' --retail-sma '../corpora/retail/Data.sma' --retail-root '../corpora/retail/Data.sma_unpacked' --base-roster .research-output/vehicles/heritage/roster --output .research-output/vehicles/michelin-native/new-pilot
```

Generic Source Garage Create remains disabled for unqualified Michelin selections. This pilot uses a strict exact-scene CLI policy; the resulting project uses ordinary Workshop studios/build/persistence. A fresh output cannot overlap the original installation, accepted source scene, donor retail tree, SMA or input roster; linked paths are rejected by the shared guard.

## Explicit adaptations

| System | Authored decision and boundary |
|---|---|
| Body | Exact intact Car25A LOD0,652 triangles; original UVs/livery/colors/material identities, original static crew/cage. No source damage targets compiled as intact body |
| Wheels | Four authentic T0004 instances,152 triangles each. Source-X local Ypi faces rims outward; four independent native resources compensate the MR side controller. No tyres replaced with stock geometry |
| Scale | Uniform1.117647047067596, chosen0.38 MR radius /0.3400000035762787 source radius. This is an MR authoring decision, not source-unit identification. No nonuniform silhouette fit |
| MR dimensions | Body bounds4.140210 length,1.890023 width,1.541153 height; wheelbase2.697932, both tracks1.564706, radii0.38 MR units. Width includes authentic source exterior geometry; bounds do not prove real-world homologation dimensions |
| Hubs | Front±0.78235292,-0.05,+1.34896610; rear±0.78235292,-0.06034388,-1.34896610. Common Z centering/Y datum retains every original body/hub relationship; no arch-based hub fitting |
| Physics | Complete retail Forester family cloned into MichelinRav4.1340kg, springs35500/32500, damping2100/2000 retained; explicit dimensions/radius/initial ride offsets only. No incomplete loose NewRav/Kia family guessed into vehicles.xml. Actual drive/suspension/collision is owner pending |
| Collision | Existing donor hull topology fitted by existing SDK to structural shell, excluding original crew, panes, lamps and wheels. Native render arrays unchanged by collision fit |
| Paint | Original samples and source corner RGB retained; existing native materials, reflections disabled; no body island edits |
| Glass | Only34 original panes, grouped10front/6rear/9left/9right. MR alpha96 is reversible authoring. Four existing native broken/intact groups; generated MR cracks separate from source textures. Doors/pillars remain opaque |
| Damage | Existing MR deformation and native glass mechanisms; isolated original-instruction CPU replay passes. No Michelin event conversion, target averaging or invented detachable-part rig |
| Lamps | Twelve original rear triangles, mask520 original red lens pixels. Original OFF, bounded lit/glow ON. Paint/emblem/headlights/indicator regions excluded |
| Crew | Authentic static Michelin crew retained, no second crew/steering wheel/interior box. Independent rigid crew adjustment unsupported for this source |
| Audio | Explicit MR Forester audio profile8, stock engine3/tuned08; no recovered Michelin recordings or sound parity claim |
| Camera | Existing Camera2.0 original donor/reset architecture; separately selected mode2, no new camera implementation |
| Presentation | Toyota/RAV4 identity, generated original-vehicle selection artwork, Results name TOYOTA RAV4 MICHELIN, yellow marker, existing frontend AutoFrame0.517829 and Shadow AutoFit |
| Roster | Private alternative CarID29, exactly30 entries, independent namespace. Existing Pajero/Trooper/Clio/Silver alternatives are not overwritten or combined |

## Validation and evidence

`tools/validate_michelin_native_pilot.py` compiles twice and compares exact DX/DXT against the pilot. It regenerates semantic states, checks all original texture samples and source vertex/UV/color reprojection, wheel-rest controller compensation, bounded panes/lens mask, collision/render-array separation and exact runtime resource differences. Result: PASS_STATIC_OWNER_LOCAL; inverse source position error4.440892098500626e-16, wheel/normal recovery below1e-6; **zero stock vehicle model replacements**,308 resource-root files including the mutable player-state seed,307 sealed resources. `conservation/validation.json` holds every changed resource and hash; no claim that the private copied PlayerState proves unlocks.

Studio smoke on a separate copy passes edit/Undo/Redo/Restore, collision rebase, Camera2.0 reset, shadow reset/AutoFit, AutoFrame, Results/marker persistence and reopen. The first probe targeted source draw0, whose black color cannot visibly tint; the corrected meaningful probe uses painted draw8. Actual Tk project open/validate, source provenance and both original neutral scenes reopen without callback errors. Native D3D9 six race/frontend views, original/derived neutral views, wheel/culling diagnostics and OFF/ON captures are in `fidelity/`; GUI evidence in `gui/`.

Original MR native instruction replay (`tools/validate_vehicle_damage_native.py`) using retail EXE `bf8aef32407eb6552c05045b8abef149f32983cedd9503b865069b444c5f96b4` and authored car `fa6d2d17ff631b0fc814601130b13e89c47b25381766c7b4614e91b129a7acbe` confirms identical deformation, RGB, returns/ABI, zero split coincident-position groups and alpha preservation:4 coverage vertices lose alpha without the existing adapter,0 with it. Unknown UV identity passes through. This is isolated Unicorn/synthetic impact evidence, **not live D3D8/GPU or damage event qualification**.

A second independent complete SDK build produced the same308 resource names and SHA256 values (`repeat-build-validation.json`). Launcher `--verify-only`, environment preflight and native-allocation self-test pass with307 sealed resources. No game was launched by validation. Exact build/patch/index hashes are in `pilot-report.json` and `candidate/launcher/launcher-build.json`. Follow MICHELIN_RAV4_OWNER_CHECKLIST.md for selection, driving, glass/brakes/Results/menu/re-entry. Full Michelin runtime L2 WARN and owner gameplay NOT TESTED remain explicit.

Focused/full suite and protected-input audit results are recorded in REGRESSION_MATRIX.md. Review archives contain committed text sources/tests/docs only; the original/adapted images, models, audio and executable payloads remain private.
