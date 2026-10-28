# Toyota 4Runner visual polish and bridge hardening

28 October 2026. Parent: `77bbe6f696bf8c882637ba7dd21c2ac15ee8a534` on
`research/vehicles`; starting working tree was clean. The actual latest native
bridge was inspected; older `c5bd91fc` source-adapter archives were not treated
as its implementation. No third-party implementation was vendored.

## Evidence and preserved baseline

The owner reports actual D3D8 loading, driving, body deformation and functioning
breakable glass on the previous pilot. Seven supplied gameplay captures show
the defects below. This is limited owner-confirmed gameplay evidence; it does
not qualify finish/results, menu re-entry, every material or the new candidate.
The exact previous `cross-game-4runner/pilot-delivery` remains available for
rollback. No screenshot was used to reconstruct source mesh geometry.

Final authoring uses its exact immutable UVS copy, SHA256
`05cb2b9db5b3c103cd623b8c1282099ac9f1f1f93593ad95d8243003f41e33dd`.
The earlier neutral scene `246cae8b...05ad3d` differs only in the recorded
`metadata.implementation_sha256.universal_vehicle_scene.py` value. Original
geometry, transforms and texture sidecars are identical. Both exact revisions
are explicitly admitted; arbitrary new scenes are rejected by this pilot policy.

The pasted brief references Master Plan v6.9, but that attachment is absent
from the supplied attachment folders. The complete retained v6.8 and all its
historical checkpoints remain intact; the new status is appended without
inventing or summarizing a missing v6.9 document.

## Diagnosed and corrected defects

| Area | Actual cause | Correction / evidence |
|---|---|---|
| Front side panes | GlassI and GlassE are shared sheets extending across door/frame/headliner. Old contiguous ranges omitted GlassI38/26 and GlassE corner/upper subsets while making painted lower edges transparent. | Clip both original face layers to one source-atlas rubber-frame aperture. The original UV mapping maps that boundary to Y/Z; interpolate original positions, normals, UVs and colours. Keep everything outside opaque. Accepted windshield source selection and both intact/broken attributes remain identical. |
| Left/right window asymmetry | Triangle ranges depended on unrelated source triangulation. | Separate explicit source node/triangle ownership from the convex aperture. Front side aperture bottom is about Y0.8486m rather than old selected minima Y0.7844/0.791m; no body/pane translation. Full boundary and per-triangle barycentric source evidence are in `semantic-apertures.json`. |
| Partial brake lights | Redness at triangle corners selected only parts of very large source lamp/paint panels. The old corner footprint also omitted right-rear Body292. This was a semantic footprint/UV-mask error, not an after-pruning Body index shift: Body draw0 previously stayed unpruned. | Clip original Body surfaces within the reviewed lower red lens atlas islands before assigning native state draw IDs. Include Body292. Clear indicator/reverse sections, painted bumper and headlights stay ordinary diffuse. Separate OFF/ON lens geometry uses common native blight authoring, with no enlarged glow. |
| Beige flat mirrors | Existing source cap geometry is present; the original shared atlas interpretation gives no qualified MR reflective inset. | Optional MR grey/chrome interpretation only on source MirrorL/R triangles53–55; original housing/mount and source baseline remain intact. No real-time rear-view camera is claimed. |
| Flat paint | Source diffuse conversion had no qualified MR environment helper. | Optional conservative opaque paint-only selections use retail silverpaint with reflection weight46/255. Mixed trim/window/lamp triangles remain diffuse. Material Studio supports strength and disable, independently of glass alpha. |
| Empty cabin / hand in air | Only the Navara seated crew was copied; source did not supply these MR controls. | Optional original Navara steering wheel draw0 triangles100–117, matching car.txt sw Index100 Size18 and an independent18-triangle DX component. Same rigid offset as the unchanged driver. Bounded minimal dashboard selection, recorded fit and dark closed rear backing; no steering animation claim. |
| Rear dark glazing | Source rear windows belong to Body atlas, not GlassI/E. | Optional static aperture-bounded glazing and dark inner volume. No invented rear glass damage controller. Original dark rear treatment remains the default fixed variant. |
| Apparent floating wheels | Original model has sparse visible chassis geometry; original TRK rest hubs are intentionally retained. | Optional48-triangle body-fixed frame/crossmembers inside the wheel envelopes. This is a safe simplified structure, not reconstructed moving axles. No wheel-contact rods falsely attached to static body; no hub, ride-height, collision or physics changes. Dynamic suspension articulation remains owner-test territory. |

## Shared implementation and reversibility

`semantic_aperture.partition` is source-game independent. Explicit UV/position
projection, convexity/finite/index/channel/allocation checks, inside/outside
conservation and composable barycentric ledgers prevent triangle-renumber drift.
No unknown material name or alpha sample automatically authorizes clipping.
The small 4Runner policy supplies reviewed nodes, atlas boundaries and evidence;
there is no separate donor-specific DX compiler or native controller grammar.

The Source Garage Create MR dialog exposes five independent optional MR visual
choices, all off by default. The CLI offers `--mr-visual-kit`; Python API accepts
individual boolean `visual_options`. Choices and exact source/hash/transform
records are saved in `mr-visual-kit.json`. Generate a fresh variant to change
structural kit choices; do not mutate the original neutral scene. Workshop
Undo/Redo/Restore cover subsequent supported Studio edits within each variant.
Restore returns to that variant baseline, not to a different kit selection.

Private phase root: `.research-output/vehicles/4runner-polish/`.

- `fixed-final/workshop`: corrected glass/brakes, original dark rear glazing,
  original diffuse paint/mirrors and original crew; optional kits off.
- `adapted-final/workshop`: independent MR adapted variant with all five choices.
- Each has its own author, unchanged source baseline and independent30-entry
  alternative CarID29 candidate under `builds/source-fidelity/candidate/`.
- `comparison-final/`: original / fixed / adapted real D3D9 OFF/ON, left/right,
  windshield damage-case, reflections, cabin and underside captures.
- `windows-mainloop/`: actual Tk create/open/provenance and D3D9 validation.
- `studio-final/`: supported edits, reopen, Undo/Redo/Restore validation.

No accepted Subaru/Lancer/Pajero/Trooper/Clio project is overwritten. No original
MR executable, retail Data.sma, installed proxy, source installation, original
wheel resource, CarID capacity or unrelated Randomizer file is changed.

## Qualification boundary

Focused and complete Windows results, deterministic resource hashes, exact
resource differences, collision/wheel/physics conservation, launcher preflights
and protected-file verification are recorded in the private phase reports and
current regression matrix. These checks cannot qualify new D3D8 visuals.

The new candidates require the focused owner checklist: side glass/door/frame
from both sides, intact/broken windshield and side panes, both rear red lens
clusters OFF/ON without bumper artifacts, mirrors/paint, optional rear backing,
crew/steering, and frame clearance during steering and suspension travel.
Finish/results and return-to-menu/re-entry remain pending unless separately
reported. Stop after this one car; no fleet/other donor campaign or push/release.

## Final available validation results

-35 focused tests PASS;1102 full Windows synthetic/CPU tests PASS,2 existing
  optional skips. Logs: `focused-final.log`, `full-windows.log`.
-42 real D3D9 comparison captures; both intact/broken windshield attribute sets
  remain exact. Per side37 clipped triangles, minimumY0.848615m. Brake lens19
  triangles, Y0.482775–0.596776m, confined to the two original rear clusters.
- Byte-identical full real native resource regeneration:21 fixed and26 adapted
  DX/DXT files. Original five wheel resources, physics profile values and
  fitted collision bytes match the accepted pilot exactly.
- Actual Tk creation with all five options, Validate, provenance, frontend and
 20 D3D9 captures PASS. Final `windows-mainloop` exits0 with clean UI shutdown.
  Earlier manual-loop harness teardown exited1 after its action checks;
  scheduling close through Tk's real mainloop resolves the harness failure.
- Studio edit/reopen/Undo/Redo/Restore PASS; six opaque paint/mirror strength
  and disable checks PASS on a disposable copy, with collision rebase intact.
- Both native candidates retain30 entries and260 patch operations. Fixed304
  resources; Adapted309. All three launcher preflights pass for each candidate.
  Full runtime folder difference ledger:18 fixed /25 adapted files including
  control manifests/art/player seeds; original accepted vehicle-family model
  and texture namespaces are unchanged.
- Accepted previous pilot:693 files retain both hashes and mtimes. Historical
  protected snapshot:2492/2493 match. The installed `D:/Game/Master Rallye/d3d8.dll`
  differs from that older snapshot (current observed SHA256
  `339174529605b6b4602715470ac67e0bf39d7f95197b0d07fe2dbd048a960ea1`).
  This task has not copied, installed, restored or modified that proxy. The
  historical mismatch is recorded explicitly, not presented as a clean match.

Review archives are generated from the final scoped commit under `review/`:
`source-review.zip`, `changed-files.zip`, with SHA256/CRC/member checks in
`archive-manifest.json`. Proprietary assets, binaries and images stay private.
