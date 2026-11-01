# V-DEF4 — PRIVATEER TOMCAT and historical frontend ratings

## Delivery

The owner accepts V-DEF3 ordering in-game without reported bugs. The isolated
33-record CMD candidate now replaces only technical probe32 with **PRIVATEER
TOMCAT**, using the early8.4.1 blue WildCat source, not the later retail body.
CarID32 remains T3/local1 immediately after retail Wildcat14. Forester30 and
RAV4 31 ordering, accepted projects, physics, artwork, identities and marker
values remain unchanged. New TOMCAT gameplay is **PENDING OWNER**.

Launch privately:
`.research-output/vehicles/v-def4/delivery/workshop/builds/final/candidate/Launch-SDK-Roster.cmd`

Open the editable project using:
`.research-output/vehicles/v-def4/delivery/Open-Restoration-Workshop.cmd`

The persistent Workshop's Last Build points to the final candidate. No file is
installed into the game. Original inputs and prior accepted builds are read-only.
Source-only archives exclude the private candidate, captures, models and textures.

## Source and authoring qualification

Manifest: `research/vehicles/sdk/restorations/tomcat-841.json`.
Canonical source: owner-local PCG `DataGx/Vehicles/WildCat`.
All three original `car.gxm`, `complete.gxm`, `wheel.gxm` byte-match shipped
`corpora/demo-8.4.1`. Original source hashes, material references and resource
snapshots remain private and immutable. Exact pins are in the manifest/provenance.

The1651-triangle cooked body is visibly and structurally distinct from retail
Wildcat. Source, restored and retail reference D3D9 views are in
`.research-output/vehicles/v-def4/d3d9-comparison/comparison.png`, with six views,
frontend, OFF/ON rear views and manually selected broken-glass states.

The rev135 rebakes have stale global caches. Generic oriented-triangle writer
validation remains strict. A reusable **explicit source-pinned cache repair**
requires both exact input and output hashes and proves that local render
positions/normals/colors/UVs/material ownership/draw states/collision fingerprints
remain unchanged. It reconstructs only the global cache from local indices.
Unlisted models retain the old strict policy; a changed source or repair result
is rejected. The existing Heritage stage performs the same repair.

This is a qualified local-draw interpretation of the authentic rebake, not a claim
of complete legacy GXM/cooker equivalence. Original GXM has1691 body records versus
1651 cooked triangles; a simple uniform axis match accounts for1630 body faces,
2061/2115 complete faces and252/252 wheel faces. Unresolved legacy bake/transform
correspondence remains explicit; it does not authorize editing the source mesh.
Original shipped rev127 DX is preserved, not silently substituted or rewritten.
No cooker or new legacy-format converter was introduced.

## Native systems

| System | Qualified implementation / boundary |
|---|---|
| Body/wheels | Original early geometry, UVs, textures and crew; common Heritage/native compiler. Original four complete-model wheel instances recovered through five independent mirrored/reindexed geometry+UV/topology parts. |
| Glass | Exact original `glass` sidecar/GXM maps12 faces, zero nearest matches, to draw15. Three native front/left/right zones, four faces each. No invented rear pane. Original intact surfaces remain unchanged; cracked textures/controllers are MR-native adaptations. |
| Brake lamps | Exact original `blight` maps8 faces, zero nearest matches, to draw2. Retail Wildcat ON core and glow geometry/material/UV is independently fitted to both selected source lenses. OFF state remains intact; no glowing body panels or global alpha override. |
| Physics | Independent retail Wildcat schema with100 compatible original8.4.1 fields. All121 old rows preserved.21 source-only fields explicitly retain retail equivalents: whole incompatible torque curve, old damage thresholds, suspension application vectors and tyre selection. Harddirt replaces old Slicks; no uncontrolled old tyre solver coefficients. Additional retail-only fields stay listed. |
| Geometry/contact | Source render wheelbase2.809745m vs original parameter2.77m; source track1.640126m vs1.66m; source wheel radial extents0.384573/0.390506m vs radius0.38m. No hidden body/hub/scale/ride-height adjustment. These are initialization/rest measurements, not suspension-settling proof. |
| Mass | Original compatible total mass1200kg; no speculative handling tune. Retail solver equivalence, tyre wear and suspension remain owner tests. |
| Audio/camera | Explicit retail Wildcat technical donor/profile14 and existing shared family/gameplay systems. No authentic8.4.1 sound-recovery claim. |
| Frontend | Common source-rest-frame alignment to retail Wildcat complete-model presentation. Derived complete translation only; race source geometry unchanged. Original8.4.1 catalog class field1 retained; target retail T3/class2 is the requested adaptation. |
| AI/save | Existing accepted AI/registry/Results mechanisms retained. New T3 AI insertion remains disabled, as in the probe; not silently inferred from selectable capacity. Trial championship migration guard remains; use the candidate's disposable copied state. No new progression bit or CarID allocation. |

The source material pipeline's existing bounded false-blend normalization is
reported separately. It does not discard source textures or convert arbitrary
glass/body regions. Manual D3D9 state captures do not test native damage/brake
triggers or actual D3D8 blending.

## Authentic identity and artwork

Original8.4.1 registration/localization proves **TOMCAT / PRIVATEER TOMCAT**;
the folder is only a technical resource key. Original8.4.1 named
`Bowler_Wildcat` frontend widget binds CarSheet frame6. Its blue artwork is
retained exactly. Original9.3.1 SmallCarSheet frame6 is visibly the matching blue
vehicle and is bounded-resampled into the qualified32×16 HUD slot. The original
bank/image ownership is verified; its exact earlier runtime CarID-to-HUD dispatch
is not claimed. Menu artwork is not reused as the HUD image.

Original early-PC driver remains **UNKNOWN**. The existing exhaustive PC/PS2/
retail identity audit is reused: later Wildcat/Drew Bowler correspondence does
not prove the earlier blue TOMCAT assignment, and the PC Demo12-driver list is
not a vehicle-indexed table. Results uses editable **HUGH HAINES / REAL_FALLBACK**.
[Historics' original lot record](https://www.historics.co.uk/auction/lot/lot-168---2001-bowler-wildcat-200/?lot=5339&sd=1)
documents his off-road rally association and Wildcat ownership in May2001.
This is a period/manufacturer fallback, not an original game name, exact early
chassis identification or claim of2001 victories. Later original evidence wins
without deleting the fallback history. Race-marker blue is an explicitly unknown
SDK fallback; no unproven original RGB is invented.

## Frontend ratings audit

See `DEMO_FRONTEND_STATS.md` and
`research/vehicles/sdk/restorations/frontend-stats.json`. The new audit reruns
the existing `audit_demo_identity.py` registration parser against exact original
8.4.1/9.3.1 executable hashes and cross-checks catalog localization. All eight
shortlist targets are covered, including explicit UNKNOWN cases.

TOMCAT's native initializer is checked for **7/6/8/8**. Future Forester manifest
builds use original9.3.1 **6/7/5/4**; its accepted frozen build is not rewritten.
Retired RAV4 and Rav4Alpha have no qualified own record: existing RAV4
**5/5/5/5** stays explicitly an SDK placeholder, never Newrav's ratings.

Workshop Vehicle Details exposes four bounded display ratings, original/catalog
versus custom/placeholder classification, Restore and normal history. Editing
them changes only frontend record values, not physics. Original evidence stays
separate and source-corrupting/mismatched PROVEN manifest values are rejected.

## Generated-icon improvement

`mr-native-v2` is confined to generated full/mini UI images. It adds brighter
studio fill, normal/view-dependent softbox highlights for complete supported
material groups and the original flat side orthographic HUD camera−90°/0°.
Full-icon framing stays independent. Source textures, geometry and ordinary
D3D9 material previews are unchanged. This is authored icon lighting, not exact
original MR reflection emulation. Explicit v1 generation/composition remains.

Same-car comparison against original blue artwork:
`.research-output/vehicles/v-def4/icons-side-source/comparison.png`.
RAV4 v1/v2 comparison:
`.research-output/vehicles/v-def4/icons-side-rav/comparison.png`.
These are private renders; no AI-created or repainted assets were used.

Generate → Apply → native UI compilation → Undo/Redo → Restore → reopen was
tested on an independent Workshop copy. The style survives persistence and
single-pass composition; opaque source geometry is never modified. Both UI roles retain their original camera poses and exact independent alpha
masks. The HUD remains a flat side view, as requested by the owner. Existing accepted RAV4 icons are not silently
rebuilt; regenerate/apply in a derived Workshop project to opt in. TOMCAT uses its
recovered original artwork rather than replacing it with a generated approximation.

## Validation and preservation

* Full Windows checkpoint:1341 tests,0 failures/errors,2 existing optional
  private-fixture skips,85.020s. Final narrow rating/provenance/HUD-camera changes
  additionally pass48 focused tests (current focused-side.json), including six new source-free cases.
* All33 native forward/reverse records and source marker bytes,55 name checks,
  Results/unlock,99 single-getter audio probes and existing T2 AI chains pass
  x86 emulation with native calls mocked. Native display stats are asserted
  independently; this does not execute the full game.
* 376 nonshared resources of the accepted32-car reference are exact. All6225/988
  prior physics/setup rows and previous UI-bank records are retained.
* Two Workshop builds produce291 identical DX/DXT; first/final builds have414
  exact resource files and identical native extension/RVP. Three launcher
  preflights pass; no game was launched by this task.
* 1759 protected pins remain unchanged, including accepted V-DEF1/2/3 and source
  model sets. Live root `d3d8.dll` and `PlayerState.xml` changed during the task;
  they were observed, not written or restored by this work. Exact old/current
  hashes/timestamps are in `preservation-final.json`. Current-Proxy environment
  verification passes with `hash_gate=disabled`.

Private evidence is under `.research-output/vehicles/v-def4`; source-only summary
is `V_DEF4_PROVENANCE.json`. Existing executable, clean archive, wrappers,
Randomizer and accepted projects are not installed over or edited. No push or
publication. Game selection/steering/spin, full race, Results, damage events,
wear, championship save/re-entry and actual Randomizer coexistence remain owner
tests for this exact TOMCAT build.

## Owner checklist / stop

1. Launch the final CMD; confirm TOMCAT beside retail Wildcat and accepted
   Forester/RAV4 ordering, full blue CarSheet, separate matching HUD icon and
   correctly elevated rotating frontend model.
2. Enter a fresh race. Inspect original body/wheels, steering/spin, tyre contact,
   suspension and especially wear/handling of the historical-compatible profile.
3. Brake from rear/quarter views: check both source lenses, core/halo alignment
   and no glowing blue panels. Break front/left/right glass and inspect frames.
4. Finish, confirm editable fallback HUGH HAINES in Results, return to menu and
   re-enter. Use disposable candidate state for save/load and existing Randomizer
   checks. TOMCAT32 is intentionally not a new AI-pool entry.
5. Roll back by closing the game and launching the accepted V-DEF3 CMD. Do not
   copy candidate state/resources over retail or accepted builds.

Stop here for review. No Newrav/next Demo restoration, additional slot, fleet
import or DLL deployment is started.
