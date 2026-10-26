# MR Heritage Garage — first native Demo import

27 October 2026 · `research/vehicles` · owner gameplay **pending**.

## Result

A genuine **Demo9.3.1 Trooper** is imported as independent `HeritageTrooper`,
CarID29 / T2 local9 in a separate30-entry test roster. The selected roster keeps
Mercedes26, frozen Subaru27 and accepted Classic Lancer28. Only this roster
omits addon Pajero29; its author project, prior builds and reservations remain.
No installed retail file is replaced. The final ISUZU display identity is an
explicit Vehicle Details overlay, qualified by the unchanged source livery;
namespace and CarID remain locked. This is not a31-entry claim.

The model is absent from the retail resource tree. Retail nevertheless retains
a Trooper physics family and a legacy registry reference; this is an independent
Demo-model import, not a claim that the name Trooper never existed in retail.
T2 is an explicit SDK test configuration, not a recovered historical Demo class.

Private evidence and launch shortcuts: `.research-output/vehicles/heritage/`.
`offline-acceptance.json` identifies the delivered Studio project and candidate.

## Reused research and source identity

Read and reconciled the actual `master-rallye-re-rdemo` worktree, branch
`research/r-demo-pipeline`, HEAD `a48afa147ef984e809f1f065299985aefaad6091`.
Its clean tree and history remain unchanged. Reused the existing main-tree DX
Upgrader; reviewed the small GXI/image modules individually. No package
initializers or unreviewed Cooker tree were copied over main SDK code.

The independent work establishes rev131→135 record-prefix conversion, matching
GXI→FEED bottom-up BGRA mapping, and a bounded native source-cooker workflow.
Past runtime evidence belongs to its exact tested Trooper/Forester packages;
it does not qualify this new independently registered candidate. Source `$chull`
edits and general Cooker reconstruction remain distinct from cache upgrading.
This import executes no Demo EXE or Cooker and preserves collision bytes.

Current corpus EXEs were confirmed original by the owner on27 October:

| Edition | Current original corpus SHA256 |
|---|---|
|8.4.1|`2d4a3b02d3cdb740dfdf3c11002c0026837dc19ba8e5211ad9763b35eb06e15a`|
|9.3.1|`611526d30be94879012efe54c56ceff428cb4d20a4bd49173370a4ebfe31a728`|
|9.10.0|`13eaa642d0aabdfc47911a8606b02d9fc8d57d74328b36a0d3d618aadf1e0b78`|

Older research EXE fingerprints can describe restriction-patched snapshots;
they must not silently be treated as these original corpus files. Trooper's
three shipped DX and three GXM hashes independently match the R-BRIDGE inventory.
The different R-COOKER `8238078c…` car hash describes a generated cache, not a
changed shipped model. Both evidence classes are retained separately.

## Edition catalog and qualified adapter

Catalog covers33 Demo family directories (including Alpha/copy directories)
and26 retail model families. Observed staging completeness:

| Edition | Families | Structurally stageable complete families |
|---|---:|---:|
|8.4.1|14|0 — rev127 unsupported; no revision-word shortcut|
|9.3.1|13|5|
|9.10.0|6|5|

These are source-folder counts, not playable roster counts. Missing complete
models, unsupported revisions and unresolved local textures are explicit failures.
Family comparison uses exact normalized model bytes and texture hashes; aliases
and near-equal floats are not declared identical. The private catalog records
original hashes, models/draw states, texture/palette-free image resources,
source mesh names, collision presence, exact named XML physics references and
shared audio/UI resource hashes. A folder name does not establish native audio
or UI association; untraced associations are explicitly unqualified.

The new Core adapter:

- Reads sources without executing them; rejects linked/oversize/malformed inputs.
- Preserves immutable `native-import`, original hashes and compatible resource pins.
- Uses the reviewed rev131 upgrader; rev135 passes through; rev127 refuses.
- Preserves same-family DXT; reconstructs a missing exact-name DXT only from local
  matching GXI. This supplied Trooper has one such missing crew texture.
- Generates independent namespace, pinned editable retail-donor physics and
  Vehicle Select / smallcarsheet artwork through existing shared components.
- Integrates the actual Heritage Garage dialog with Library, Previewer,
  Configure/Validate/Build and existing reversible authoring.
- Does not invoke GT Classic conversion, substitute another body or move hubs.

The legacy collection loader retains Navara-only default admission. The explicit
roster path now admits another donor only with a pinned typed profile and exact
recompilation of both retail XML members, plus effective-player validation.
This preserves old admission while removing a real SDK-only donor restriction.

## Trooper feature qualification

| Resource | Vertices | Serialized triangles | Physical draws |
|---|---:|---:|---:|
|car.dx with state alternatives|2372|1951|30|
|complete.dx|2500|2375|20|
|wheel.dx|220|252|5|

The original race model has1911 triangles. All1911 intact/off triangles retain
positions, winding, normals, colors, UVs and materials. The additional40 triangles
are alternative broken-glass / illuminated-lamp states, not mixed LODs.
27 native textures use423,936 payload bytes. Source body, spare wheel and
original driver/co-driver geometry/textures are preserved.

Front/left/right glass zones are explicit triangle selections from the actual
source window surfaces. Source rear body has no transparent rear pane, so no
rear zone is invented. Stock local Navara cracked glass uses explicit planar UV
fallbacks. This is documented native-MR authoring, not a claim that the shipped
Demo DX already had these damage switches.

Source `blight $perspex` GXM records1899–1910 uniquely match12 lamp triangles in
draw14, within7.16e−7m using the source (x,z,−y) axis mapping. Native `blight` keeps
those off surfaces and adds separate lit/glow alternatives. Derived red-only
texture treatment stays on the actual lens geometry; no enlarged body halo or
permanent diffuse illumination. Actual game intensity, damage and switching
remain owner tests.

The reusable wheel diagnostic now handles mirrored/reindexed native vertices.
Three independent wheel parts prove all four rest-pose transforms by positions,
UVs and triangle topology; maximum fit error8.94e−8m. This does not tune physics.
Frontend has separately shaded colors/normals; those are not assumed identical.

Physics uses unchanged values cloned from exact retail `Vehicles/Trooper`:
wheelbase2.4m, tracks1.65m, radii0.38m, nominal ride-height0.05m and droop0.1m.
The source frontend axle distance is2.395298m. No arbitrary geometry/physics
fitment offset is added. Independent family `Vehicles/HeritageTrooper` remains
editable in Physics Studio. Native collision is retained, not recooked.

Source Demo engine association is unqualified. Audio profile7 / retail Navara
is explicitly selected and shown as a fallback. No new synthetic audio or
proprietary samples are bundled. Existing follow-extent and Shadow Studio
controls remain available; five-mode/FOV hooks and physics tuning are out of scope.

## Validation and limitations

- Full synthetic checkout:910 tests, two existing optional private-fixture skips.
- Real Windows Heritage dialog: inspect, source3D preview, create, Configure,
  Validate, Build; native Previewer opened; physics Save/reopen/history/Restore.
- Two fresh Core imports:101 files identical, including feature recipes and art.
- Repeated roster derivation: identical native image/operations and resources.
- Two independently built packages:zero sealed game-resource differences.
- Runtime/launcher preflights and roster structural/semantic validation pass;
 313 sealed resources,185 frozen base resources preserved.
- Audio owner/lifetime/ABI/failure/stock paths pass controlled native CPU replay.
- Windows Audio, Paint/Crew, stock material references, texture zoom,
  material/binding/reflection/stock builds and Physics/Camera/art are rerun.
- Original EXE, graphics DLL, installed SMA and retail SMA match protected hashes.
  All60 original Trooper source snapshot files remain unchanged.
- Fresh candidate PlayerState is byte-identical to the owner's root save.

Detailed machine evidence stays private. An initial Physics GUI regression was
incorrectly paired with a Classic/Trooper baseline; it was rerun against the same
Source Fidelity/Pajero roster. Product assertions were retained; no geometry or
audio check was weakened to accommodate that harness mismatch.

No new D3D8 gameplay pass is claimed. In particular: race suspension fitment,
full collision/damage behavior, actual glass-zone triggers, brake glow appearance,
AI participation, audio, Results and re-entry require owner verification.

## Owner checklist

Use `Launch-Heritage-Trooper.cmd` in the private evidence folder. Use its matched
launcher/runtime; do not transplant a launcher or overwrite the original save.

1. Check the new Trooper menu name/art, stock cars, Subaru and Lancer.
2. Start a new T2 race as Trooper; inspect all sides, crew, wheel orientation and
   live suspension; test both player roles where practical.
3. Brake/release: rear light ON/OFF must stay on lenses. Check reflections on/off.
4. Collide: body deformation remains coherent; front/left/right glass damage
   should be independent. No nonexistent rear transparent pane is expected.
5. Verify explicit donor sound, cameras and shadow; test AI Trooper in a new race.
6. Finish, Results, exit and re-enter a race. Previous saved competitions and
   multiplayer remain separate qualification boundaries.

Class expansion findings are in [CLASS_SLOT_RESEARCH.md](CLASS_SLOT_RESEARCH.md).
No31+ runtime, new vehicle milestone, push or publication is started here.
