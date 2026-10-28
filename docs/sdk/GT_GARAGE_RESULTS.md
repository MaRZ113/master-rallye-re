# GT Garage Lab — source corpus and reusable conversion

Worktree `master-rallye-re-vehicles`, `research/vehicles`; baseline
`9416ddbc976da283964ab0ea621884b1789e0fe4`. Local private evidence lives in
`.research-output/vehicles/gt-garage/`. No retail or extracted asset is included
in this source report. New D3D8 gameplay is **NOT TESTED**.

## Evidence levels and corpus

The read-only scanner validates RoFS ranges, decoded member budgets, selected
source structures and exact catalog joins. Checkpoints bind both source and
reader hashes; changed readers require a new report. Stop/resume is supported.

Local source: US SCUS_971.02, GT3.VOL SHA256
`27c84369911bf2352bbe5f6ba21830357c23cd82fe529b25c38c22986d37fa88`.
Original CORE SHA256
`fdcea2aa43231873592adee0fb96499f2e40979e0269191af1eafcf95da12b0b`.

| Denominator | Result |
|---|---|
| 5,333 volume entries | 574 day/night model members discovered |
| 574 inspected model members | 572 structural PASS, 2 MISSING INPUT (empty ho0100) |
| 572 structurally parsed members | 562 distinct decoded model hashes |
| US / EU / JP catalog entries | 244 / 244 / 242 |
| Exact member associations | 244 / 231 / 242; 13 EU references missing in this US source |

The exact association is GTAR table30 CAR u64@48 → table5 key@0 → model key@24
→ IDDB label → exact day member. It is separate from Sound Lab associations.
Color IDs join original carcolor.db and carcolor.sdb records; no RGB tint is
presented as an original colorway. 368 day/night members expose multiple colors.

`inventory-v6.json` is the current complete structural inventory. L0 does not
qualify source materials, all LODs or rendering. Representative `qualification-02`
keeps sb0097, ma0101 and do0014 L1 UNSUPPORTED for undecoded CLUT references.
Clio silver/blue are L1 WARN with structural MR outputs and documented effects/
rig approximations; L2 CAPTURED means diagnostic images exist, not visual parity.

## Shared architecture and synchronization

GT3 has its own ModelSet1 hierarchy, source lighting interpreter and explicit
edition gate while sharing bounded VIF/GS readers and the MR compiler with GT4.
Only the qualified CORE permits the implicit UV STMASK 0xc0c0c0c0; original
instructions at 0x24e4a0 were checked with Ghidra R5900 and Rabbitizer. This is
not proof of GT3 VU lighting parity. No GPL implementation was copied.

The independently developed automatic importer is retained. `derive` supplies
the source profile; the source-color project bridge and GUI call that same
implementation. Standard mode fits LOD0 to donor geometry, limits textures to
256px and adds donor tyres/crew and inferred glass/brake states. Full mode keeps
GT tyre imagery and translated passes. Neither mode proves all original effects.
257/287 derived profiles is not 257 playable vehicles.

Approved wheel UV gate: automatic external face bindings require finite source
UVs on all used packet vertices. The decoder enforces the same rule even with
old profiles. On Clio, external1 retains the face image; two external0 packets
without UV remain environment/effect passes. Image identity is still a recorded
source-image candidate, not recovered native external-slot dispatch.

The shared gzip reader limits both stored and expanded inputs to16MiB. Tests
cover malformed/oversized streams, no-UV/mixed-slot bindings and preservation
of automatic native glass/brake controllers through no-op Classic rebuilding.
See `research/vehicles/gt-garage/SYNCHRONIZATION-2026-10-28.md` and the independent
`AUTO_IMPORT_RESULTS.md` for the Heritage work and its separate evidence gates.

## Original colors and editable versions

Clio `re0011`: Iceberg Silver, Illiad Blue, Mars Red, Nocturne, model key
`0x66796560c18b1`, exact US CAR key `0x75ee9ab2b5d3d528`.
Raw source SHA256 `5e4cc32a11096bc061bc908b65d291907132d889e7638935a56b2b563ee77956`.
The source project pins immutable model/profile/color tables/identity. Each
original color owns its own Workshop project; manual edits remain in that
version. Source Undo/Redo/Restore selects versions; it does not overwrite Paint
history or copy ambiguous manual edits between colors.

The GUI supports Open inventory, Scan/Stop, Create from selected, source color
selection/build, source history and Open selected in Workshop. Creation requires
the actual source model, original color tables and a read-only retail donor.
CLI creation supports either an explicit profile or `--inventory --car-key`.
Automatic creation verifies exact model and color-table hashes before deriving.

## Classic pilot and measured changes

The explicit full-resolution Clio pilot remains independent from automatic
standard-mode builds. Their fitment policies are not silently interchanged.

| Resource | Source Fidelity triangles / draws | Classic triangles / draws |
|---|---|---|
| car.dx | 2942 /87 | 2942 /87 |
| complete.dx | 3878 /107 | 4238 /107 |
| wheel.dx | 234 /5 | 324 /5 |

Original source multipasses include3426 body triangles; do not compare that
number directly with MR physical geometry. Approved Clamp-boundary subdivision
increases the unrefined MR body from1888 to2942 triangles while preserving
surface/winding and source image resolution. It reduces guarded texture cache
from16,855,040 to9,534,080 bytes. Draw count remains86. Repeated89-file builds
are byte-identical; original silver/blue geometry is identical.

Classic v2 uses SHA-pinned semantic roles and opt-in stages, retaining v1 Lancer
behavior. Clio changes the rim to stock-informed metallic shelf, recessed opaque
insert/backing, stock MR rubber and selected optical glass texels. Characteristic
original paint is retained. No arbitrary body decimation or decal deletion was
authorized for this production Clio; these stages report preservation. This is
a wheel/glass/material generalization pilot, not universal automatic livery
simplification. Mixed window/painted-frame draws retain their non-environment
path to avoid discoloring frames. Source GT lighting remains approximated.

The final owner-feedback pass uses measured presentation hub Y=.188m instead
of the provisional .320m. With .320m tyres and an arch top near .550m, this
removes the prior .090m overlap and gives about .042m static top clearance.
It changes presentation assembly only, not donor physics or recovered GT rig.
Bonnet source shape10 packets16/17 have exact oriented environment matches.
Reusing the existing paint partition kernel removes the abrupt dark reflection
boundaries; one added draw separates residual cutout coverage. The new Clamp
stage supports these independently derived UV partitions without indexing the
original parent vertex list. Source RGB/normals are retained; residual coverage
uses the documented129 reflection-alpha floor. Wheel-only compilation does not
apply body paint selectors.

Glass sampling now has explicit per-atlas reference axis, vertical direction
and crop controls. The windscreen band sits at the physical top; side and rear
windows sample the banner-free stock region. Source UVs, border texels and
unselected alpha remain unchanged. An attempted automatic height inference was
rejected because the shared front/rear atlas is ambiguous; no heuristic was
retained in production code.

Final Source Fidelity / Classic referenced textures:84 /87; native cache
9,535,104 /9,282,176 bytes. Actual dimensions, role selectors,
resource hashes and limits are recorded in the private exact recipe/report.
The owner explicitly approved the corrected exact report:
`c38d712cef80cfc5a43b30f187afe0152478d1dac7617e87a5501e3e85ffcf61`.
The separate Classic runtime is built. This authorizes construction, not gameplay
qualification. The old report and provisional candidate are superseded.

## Owner candidate and limitations

Source Fidelity launch:
`.research-output/vehicles/gt-garage/t/s2/candidate/Launch-SDK-Roster.cmd`.
Approved Classic launch:
`.research-output/vehicles/gt-garage/t/c2/candidate/Launch-SDK-Roster.cmd`.
It contains Subaru27, Lancer28 and Clio29 in an isolated qualified30-slot layout.
It is an alternative to Pajero/Trooper29, not a fourth simultaneous addon.
Current root PlayerState.xml is copied unchanged. Launcher verify/environment/
allocation preflight and collection validation pass; no game was launched.

Clio retains donor physics/collision. The explicit pilot hub/WB and body-datum
adaptation are editable MR authoring values, not recovered GT3 wheel-instance
transforms or factory dimensions. Native wheel rig, dynamic fitment and handling
remain owner-testable. The automatic standard variant uses a separately reported
donor scaling policy. No physics tuning or new capacity patch was introduced.

Owner checklist: stock/Subaru/Lancer unaffected; Clio menu and UI; race wheel
orientation/fitment; transparent glass/deformation; brake OFF/ON; lighting and
reflection differences; race completion/Results/re-entry and AI. Test exact
Classic separately from Source Fidelity. D3D9 captures cannot qualify D3D8.

Both candidates pass collection validation and all three launcher preflights.
Their resource-root difference is confined to20 Clio-family paths. Subaru,
Lancer, stock audio/physics/UI and current PlayerState are identical between
them. `candidate-differences.json` records exact hashes and paths.

Final evidence includes `qualification-classic-03` (all-side/wheel/alpha/
reflection/wireframe captures and two identical Core rebuilds),
`qualified-determinism.json` (complete source repeat and original color geometry),
`regressions-02` (actual Physics/Camera, Audio, Paint/Crew, texture windows,
native engine/multi-owner CPU replays, seven Heritage validations), and
`windows-classic-final-03` (actual Classic workflow, history and source restore).
Lancer's frozen v1 recipe still reproduces all81 resources exactly. The current
full suite has967 tests with two pre-existing optional fixture skips. Native
brakes/glass in the automatic Clio path remain separately owner-testable; the
explicit Source Fidelity/Classic pilot has no generated brake controller.

## Reproduce with private inputs

Use `tools/vehicle_sdk.py gt-garage --help`, `auto-import-gt3 --help` and
`gt-source-project create --help`. Scan the original VOL, select an exact catalog
CAR key, provide its decoded or gzip model and original color tables, and create
a fresh output directory outside retail data. Use `full` for source-preserving
inspection and `standard` for the documented donor-based approximation.
Validate/build via the shared SDK with explicit retail source arguments.
Classic v2 requires an independently qualified recipe; never apply the Lancer
default or another vehicle's draw selectors to an unknown car.
