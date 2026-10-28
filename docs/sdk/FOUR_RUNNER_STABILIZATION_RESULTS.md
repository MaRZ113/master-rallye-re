# Toyota 4Runner Stable — v7.0 stabilization

28 October2026, `research/vehicles`, clean starting tree at
`450eb5d08dcc4a73d104357fd250b64e35dc92d1`. The latest source-review1315/1315
and changed-files19/19 hashes and both ZIP CRCs were reverified against this
revision. Original playable, fixed-final and adapted-final are frozen comparisons.

## Owner evidence and safe default

The owner confirms improved front side glass, correct lower rear brakes,
previously good windshield, playability, body deformation and breakable glass.
The five optional Visual Polish experiments are rejected by the owner in D3D8.
Exact previously tested launcher/path/manifest: **UNKNOWN**, not inferred from
a screenshot or commit. No new gameplay pictures accompanied this message;
the new regression findings are owner textual evidence. The older seven images
are not relabelled as new optional-kit evidence.

**4Runner Stable is a new candidate, PENDING OWNER D3D8 TEST.** Its entire
21-file converted DX/DXT assembly and prepared model/texture assets are
byte-identical to the requested `4runner-polish/fixed-final` starting point.
Original paint, complete56-triangle source mirrors, dark rear glazing, cockpit,
accepted crew and simple underbody remain. All three intact/broken pane zones,
lower brake OFF/lit/glow states, wheels, physics and fitted collision are exact.

All five rejected flags now fail before source reads/output creation; creation
UI shows them disabled and the old CLI `--mr-visual-kit` explains the rejection.
No cuboid, extra steering wheel, rear alpha cut, decorative frame or partial
paint environment draw is generated. Historical450eb5d code and private
adapted candidate remain for comparison, not as a promoted MR Adapted preset.

## Rejected-feature audit and disposition

| Feature | Exact source/code diagnosis | Disposition |
|---|---|---|
| Paint |48/604 original Body faces selected from four atlas rectangles; moved out of Body into a diffuse+env draw, opaque flags0/0, vertex weight46/255. Selected positions/normals/UV/winding were retained; reflection coverage is discontinuous by construction. | Keep complete original diffuse. Increasing intensity cannot repair missing coverage. |
| Native extra reflection pass | R4D.1 documents env stage1 MODULATEALPHA_ADDCOLOR/camera-space normals and feature bit4. Null-slot/full pass mapping is incomplete; Material Studio edits an existing qualified env draw, not an arbitrary pure-env overlay. | Separate reflection-only depth/blend ownership is **UNQUALIFIED** for this body. No speculative duplicate diffuse pass, alpha/two-sided workaround or new reflection candidate. |
| Mirrors | Old selection53–55 of56 triangles per MirrorL/R changed diffuse/env/alpha160 on a cap, not a qualified independent complete mirror volume/material. Source positions/normals/winding/UV were not moved; static tests did not qualify D3D8 multi-view appearance. | Restore both complete source meshes/materials exactly. No replacement reflective candidate. |
| Rear glazing | Three atlas masks and cuboid bounds[-.55,.38,-1.98]..[.55,1.315,-.52] had no containment against actual sloping3D cabin/roof/apertures. Owner sees wrong surfaces/protrusion. | Original opaque rear windows. No box, atlas-only rear glass or unsupported damage zone. |
| Cabin | Navara wheel draw0 triangles100–117 and20 dashboard triangles were added without removing/remapping the baked wheel graphic. Owner sees duplicate wheels. | Retain original cockpit and accepted crew; no3D control candidate or steering-animation claim. Artwork removal is unqualified. |
| Underbody | Four fixed beams stopped short of wheels. Existing mechanical_attachments/vfit4 qualifies single-hub unsprung caliper/rolling resources, not a telescoping/body-to-wheel or two-moving-hub axle solver. | Original underbody. Moving supports deferred; no disconnected rods or physics/hub/collision/ride-height changes. |

Private `rejected-feature-audit.json` retains selections, material values,
verified archives and hashed research references. Existing native research is
cited as prior evidence, not a newly executed binary trace or D3D8 proof.

## Independent upper brake strip test

Default-off `--upper-brake-lamp` / creation checkbox produces **Stable + Upper
Brake Test**, never a combined adapted kit. Only original `mesh-000` /
`node-mesh-000` Body595/596 upper spoiler faces are eligible under the exact
source-scene hash. The512px source red strip U50..70,V451..453 lies within
the original upper rear3D surface. Four clipped triangles cover160.1mm width
and17.57mm height, bounds X[-.075680,.084387],Y[1.311786,1.329351],
Z[-2.107080,-2.098981]m; no enlarged glow/roof/hatch/bumper geometry.

They are appended after the accepted19 lower triangles in the existing native
blight OFF/ON parts. Lower OFF/lit/glow attributes/materials remain exact; no
new controller, texture or headlight/tyre state is introduced. All other Body
faces/UVs/normals/winding, panes, wheels, physics and fitted collision are exact.
`upper-brake-lamp.json` records barycentric source provenance and bounds. This
is explicit MR brake authorship, not recovered Evo2 runtime lamp semantics.

D3D9 rear ON difference versus Stable is limited to pixel box[519,180,560,187].
Close-up OFF/ON retessellation/resampling differences remain local to the
upper-strip box[487,350,592,374]. Actual D3D8 binding, visibility and damage
still require isolated owner testing; Stable itself keeps this option off.

## Available validation and delivery

-59 focused tests PASS;1107 full Windows synthetic/CPU tests PASS,2 existing
  optional skips. Standalone legacy tests require `PYTHONPATH=src;tests/synthetic`;
  an initial invocation omitted that helper path, then the corrected run passed.
-45 real D3D9 comparisons,15 per fixed-final/Stable/upper-only: front/rear/sides,
  both mirror close-ups, cabin, underbody, intact/broken glass and upper OFF/ON.
  All15 Stable images are pixel-identical to fixed-final at the same cameras.
- Both full native regeneration runs are byte-identical (21 DX/DXT each).
  Exact accepted pane/lower-light/wheel/physics/collision checks pass.
- Actual Tk Create/Validate/provenance/frontend, disabled legacy options,
  20 D3D9 images and clean mainloop shutdown PASS. Studio edits, reopen,
  Undo/Redo/Restore and source hash/mtime checks PASS on disposable copies.
- Independent30-entry alternative CarID29 candidates; all three launcher
  preflights pass per candidate. Other accepted vehicle namespaces unchanged.
- Start snapshot includes4610 accepted/source/original files and all three
  previous comparison candidates. Current proxy hash was recorded **before**
  implementation as `339174529605b6b4602715470ac67e0bf39d7f95197b0d07fe2dbd048a960ea1`.
  Older `eb7ea3d9...29aaf4` differs; it is pre-existing. No restore/copy/install.

Complete supplied322686-byte v7.0 SHA256
`2df687c534ac42df8d62d43c06392d9bfb022b3e7adb8bce24da53eba5605afe` is retained
exactly and forms the canonical Master Plan prefix, including missing v6.9.
All4895 bytes of unique old repository checkpoints are appended verbatim as
historical records; no research or accepted history is replaced by summaries.

Private root: `.research-output/vehicles/4runner-stable/`.
`baseline/workshop` and `Launch-Stable.cmd` are primary; `upper-test/workshop`
and `Launch-Upper-Brake-Test.cmd` are an independent optional test.
Evidence: `comparisons/`, `windows-ui/`, `studio/`, native resource differences,
preservation, deterministic and plan-reconciliation reports. Source-only
`review/source-review.zip` and `review/changed-files.zip` exclude proprietary
models/textures/audio/previews/binaries and pin the exact scoped commit.

Test Stable first, then upper lamp alone. Finish/Results/re-entry and complete
AI/audio remain separate owner qualifications. No combined preset, donor/fleet,
Blender Bridge, roster expansion, push, release or unrelated merge is started.
