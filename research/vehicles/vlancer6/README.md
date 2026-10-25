# V-LANCER6 — paint coverage and complete stock crew

Status: **ready for human gameplay testing; offline qualified only**.
Branch: `research/vehicles`. Private candidate: `.research-output/vehicles/vlancer6/candidate-04`.
Launch: `candidate-04/Launch-V-LANCER6.cmd`. Earlier V6 iterations are not the handoff.

The user's V5 gameplay confirmation is recorded separately in
`v5-human-confirmation.json`; it does not qualify these changed V6 assets.

## Changes

### Painted exterior

The old whole-packet coverage requirement rejected reflective paint packets
containing even one cutout island. A shared source environment packet could
also contain different triangle-local gains. This left adjacent bumper panels
and other paint without environment mapping.

`gt4_paint.prepare_paint` now requires explicit editable paint roles plus a
complete, oriented source environment-triangle match and compatible GS states.
It partitions existing triangles by their filtered UV coverage. It does not
create panel geometry, alter UVs, infer paint from MatN names or enable every draw.
UV guards use the original parent packet, including after partitioning.

Both models now have **35 source-qualified paint packets / 1,240 triangles**,
compared with **27 / 942** reflective triangles on these same source shapes in
V5. Coverage includes painted bumper bands, bonnet, fenders, doors, rear
quarters, roof surround, trunk, mirror casings and spoiler exterior. These become
47 physical paint draws after coverage partitioning; draw count is not coverage.
Deep grille/intercooler interiors, dark trim, glass, separate decals, lights,
rubber and cockpit materials retain their previous assignments. Source main-body
packets 0, 1 and 28 remain excluded. Coarse hidden spoiler/core supports are not
promoted without a qualified source environment correspondence.

**Controlled approximation:** 187 paint triangles still need coverage alpha.
On their source-covered texels only, the MR alpha channel uses a minimum of
129; zero-alpha holes stay zero. MR shares coverage and reflection weight in
this channel. Weak reflections can consequently be stronger on those cutout
edges, and damage reflection fading there remains approximate. The other 1,053
paint triangles retain the original per-texel reflection weights. This is not
exact PS2 environment/DATE reproduction.

### Complete stock driver and co-driver

The shared `crew.fit_crew` imports hash-pinned stock Navara geometry/materials,
using per-person rigid XYZ/yaw fits from the profile. It does not import donor
seats, cabin, steering wheel or body. Each model gains **544 stock triangles /
618 vertices**. UVs, vertex colours, normals, winding and stock DXT bytes are
preserved; texture names are content-addressed to avoid collisions.

The first diagnostic selection omitted material-batched character pieces:

| Stock draw | Selected purpose | Triangles |
| --- | --- | ---: |
| 0, explicit subset | Red shoulder and lap harnesses | 52 |
| 1, explicit subset | Helmet brow / inner shell closing the apparent openings | 48 |
| 16–20 | Suits, hands, faces, visors, outer helmets | 444 |

The missing belts and helmet sections reported by the user are now included in
both `car.dx` and `complete.dx`. They are original stock polygons, not generated
patches. Exact triangle selectors live in the editable profile under the source
hash. Private component inventory: `crew-audit/components.json`.

Projected helmet-to-roof clearance is at least **44.5 mm race / 42.3 mm frontend**.
All 618 crew vertices pass the projected side-envelope check. Cutaways and views
through the unchanged V5 glass were inspected. These are not a complete
seat/dashboard collision solver. Stock poses are static: steering-wheel hand
contact and seatback fit are approximate and need the user's camera inspection.
The original dark glass is retained rather than brightened to exaggerate crew.

## Validation and preservation

Private evidence is under `.research-output/vehicles/vlancer6/`:

| Check | Result / evidence |
| --- | --- |
| Deterministic DX/DXT rebuild, references, budgets | PASS, `offline-validation-final.json` |
| Original Lancer geometry, normals, colours and exact UVs | No missing original triangles; only 544 crew triangles added per model |
| Non-paint assignments | 127 frontend / 60 race original draws unchanged, `material-validation-final.json` |
| Wheels, source assembly, collision, donor physics, UI | Preserved; wheel DX byte-identical |
| Native brakes | Existing switch/materials retained; halo alpha outside source mask = 0 |
| Native damage CPU replay | 36 synthetic impacts, XYZ/RGB/returns match original native function; coverage-alpha losses 91 → 0; coincident-position splits = 0 |
| Synthetic suite | 643 tests, no failures/errors, 1 existing private-fixture skip; `tests-final.log` |
| Current viewer on stock Navara and Pajero | Asymmetric UV/winding/depth fixtures and brake/reflection toggles PASS |
| V5 reproducibility | Actual DX/DXT bytes reproduce, `v5-reproducibility.json` |
| Frozen V5, Subaru V-MESH4.13, SCALE29/30 | Own sealed launchers verify; 148 non-Lancer immutable resources match V5 |
| Installed original EXE / graphics proxy | Hashes unchanged; verify/environment/allocation self-test PASS |
| Extension rejection | Missing, truncated and altered payloads rejected in a disposable copy |

Crew increases the source-bound damage identity payload to **76,591 bytes**.
The existing external runtime now admits a **128 KiB private allocation only for
this damage policy**, within a strict 128 KiB cap. Existing <=64 KiB profiles
retain their allocation/bytes. No original EXE, graphics DLL, physics, CarID
capacity or native damage algorithm is changed. Allocation self-test executes
no game code; CPU replay is isolated Unicorn, not gameplay.

The vehicle-family texture charge is **12,199,936 bytes** (77 textures), below
the existing 16 MiB authoring budget. This is cache accounting, not a live FPS test.
The bundle uses V5's existing CarID27/T2 path and CarID26 baseline; it is not a
new SCALE roster. Frozen SCALE candidates are separate and unchanged. Generic
runtime-profile gate text remains conservative; only the user's V5 confirmation
is established gameplay evidence.

## Comparative previews

Private `preview-final/` contains:

- `crew-detail-fix.png`: omitted batches versus restored harness/helmet pieces.
- `crew-comparison.png`: V5/V6 through identical glass, side view and cutaway.
- `reflection-weight-comparison.png`: actual texture/vertex reflection weights.
- `reflection-coverage.png`: cyan explicit paint, amber other existing reflective
  materials, orange crew, grey non-reflective surfaces.
- `reflection-comparison.png`: reflections on/off, before/after.
- `damage-brakes-comparison.png`: CPU-damaged resources, reflections/brakes on/off.

`preview-captures.json` pins the 21 comparison captures to model hashes and
cameras. `crew-final.bmp` is an additional close cutaway. These are fixed-function
SDK Previewer captures, not original-game screenshots or proof of renderer parity.

## Human testing remaining

Launch the final candidate and compare reflections ON/OFF, especially the white
front bumper band, sides, roof and spoiler. Check crew helmets/harnesses through
front and side glass; inspect seating and hands. After impacts, check paint
coverage, coherent deformation and brake on/off confinement. Confirm loading
and performance remain acceptable. No suspension, ride-height or physics work
was performed. Collision fitting requested earlier remains a separate research
topic; the qualified donor collision is intentionally preserved in this pass.

Reproduction and future stock-crew fitting: see `crew-fitting.md`.
Private handoff archive contains source changes, documentation and tests only;
it contains no retail/GT model or texture assets. No commits, push or publication.
