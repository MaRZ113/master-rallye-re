# MR Heritage Garage

## Reusable Demo restoration (V-DEF2)

Use `tools/restore_demo_vehicle.py` with a per-car manifest under
`research/vehicles/sdk/restorations`, a private roots configuration and the
previous frozen roster. Source hashes, geometry/face selections, identity,
artwork and physics policy belong in the manifest, not another converter.
Original sources and existing author/build directories cannot be output targets.

Forester's corrected V-DEF1 build is now owner accepted. The new Demo RAV4 is
available at private `vehicles/v-def2/owner-candidate/Open-Restoration-Workshop.cmd`
under `.research-output`, with a separate CMD launcher inside its first build.
Its CarSheet and SIDE HUD icon are generated from the authentic white/blue
model through Workshop; mismatched historical images were rejected.100 compatible
Demo physics fields and21 explicit retail substitutions are documented. Driver
unknown: Results uses the car name, not a fabricated person. RAV4 ID31 and the
32-record candidate remain owner-test pending. See `V_DEF2_RAV4_OWNER_TEST.md`.

Earlier V-DEF1 examples below describe their original historical delivery.

Heritage Garage imports native PC Master Rallye resources, independently from the GT3/GT4 adapters. It does not apply Classic MR Style or execute a Demo cooker.

## Workflow

1. Open **Heritage Garage** in Rally Workshop and select a local Demo installation containing `MRallye.exe` and `DataGx/Vehicles`.
2. Inspect the edition and choose a family. Original source files stay read-only. Unknown EXEs are catalogued; import needs a known fingerprint or an independently qualified shipped-source fingerprint set. Unsupported rev127, missing models and missing exact local texture dependencies are refused.
3. Preview the compatible source in the normal interactive Previewer.
4. Choose a unique runtime namespace, an exact retail physics family and an explicit tuned retail audio profile. Supply your original retail `Data.sma` to create the editable, independently pinned physics profile. Profile7 is Navara audio: a deliberate fallback, not authentic Demo Trooper sound.
5. Optionally supply a source-pinned native feature recipe. Every pane and lamp triangle must have explicit evidence. Unknown effects are retained, not guessed. Qualified recipes can preserve intact surfaces and add native broken-glass / `blight` alternatives.
6. Create the Heritage project. Its private source snapshot, compatible models and generated Vehicle Select / Results art enter the existing Library.
7. Configure an explicitly selected isolated roster, Validate and Build. Current production builds admit only the qualified29/30 roster layout. A different addon may be omitted from this separate test roster; its project, previous runtime and reservation ledger must remain unchanged.

## Preservation and editing

`native-import` contains immutable original local bytes; `heritage-import.json` pins them and the compatible DX/DXT baseline. Normal Workshop edits live in reversible overlays. Save, reopen, Undo, Redo and Restore use the existing service. Do not edit source snapshots directly. Reimport from the original installation to change source input.

Rev131 to135 upgrades only the reviewed record prefix; existing rev135 resources pass through. Same-family supplied DXT stays unchanged. A missing DXT may be reconstructed from a matching local GXI using the reviewed bottom-up BGRA mapping. There is no cross-car texture substitution.

Physics, camera extents, marker RGB, material/texture inspection, Shadow Studio and other qualified authoring remain available. Race wheels recovered from frontend geometry are a source rest-pose diagnostic, not proof of live suspension placement.

Native glass/brake adaptations and Previewer D3D9 captures are offline evidence. Owner D3D8 testing must confirm selection, spawning, both player/AI roles, braking, individual glass zones, damage, sound, Results and re-entry. No increase beyond30 active vehicles is gameplay-qualified by this milestone.

## CLI

Use the source checkout with `PYTHONPATH=src;tools;.`:

```
python tools/vehicle_heritage.py catalog --source <demo-root> --retail <unpacked-retail> --output <new-catalog.json>
python tools/vehicle_heritage.py preview --source <demo-root> --family Trooper --output <fresh-preview>
python tools/vehicle_heritage.py create --source <demo-root> --family Trooper --name "Demo Trooper 9.3.1" --runtime-family HeritageTrooper --physics-donor Trooper --audio-profile 7 --retail-sma <original-retail-Data.sma> --features <qualified-local-recipe.json> --output <fresh-author-project>
```

The last command creates an author project, not a game installation. Open it in Workshop and configure its matching isolated roster. All copied MR assets remain private. Archives for source review contain code, documentation, tests and hashes only.


## Complete Demo collection audit

Before adding a historical vehicle, consult `DEMO_VEHICLE_AUDIT_RESULTS.md`,
`DEMO_VEHICLE_COMPARISON_MATRIX.md` and `DEMO_VEHICLE_IMPORT_SHORTLIST.md` in
`docs/sdk`. The audit distinguishes shipped originals, owner-local rebakes,
renamed aliases and accepted imports using decoded surfaces/UV/materials.
Nested and GXM-only folders are included. Missing textures remain unresolved in
catalog comparison; malformed textures block staging. Existing staging fallback
behavior remains explicitly reported and is not source-fidelity qualification.

Forester9.3.1, cooked PCG Rav4 9.3.1, early WildCat8.4.1 and original9.3.1 NewRav are the recommended
future review order. Nov Wildcat points to Simmbugghini resources; the authentic
9.3.1 Wildcat and full NewRav/Tata DX sets are in the original corpus. No new
runtime identity, installation or gameplay qualification was performed.


## V-DEF1 canonical Forester

**Current owner revision:** open
`vehicles/v-def1/owner-fixes/release/Open-Forester-Workshop.cmd` under the private
`.research-output` root. It uses an independent retail Forester physics clone,
the original Demo9.10 side mini icon, donor white ON core/halo and measured
complete-only menu lift. Previous release-candidate remains rollback evidence.
Darren is owner-confirmed in race; corrected visual/tyre behaviors need retest.
See `V_DEF1_FORESTER_OWNER_REVISION.md`. The paragraphs below describe the
historical first candidate and its deliberately retained source research.

The selected main PCG Forester now has a persistent Workshop restoration and
CMD test candidate. See`V_DEF1_FORESTER_RESTORATION.md` and its owner checklist.
The old alternate Original/car.dx is not used. Original Demo artwork/geometry,
source-valued physics and PS2-qualified Darren Sutherland identity are retained;
WOOLDAND is the technical glass/glow/solver/audio donor. Front and both side
panes are qualified; no separate rear pane is invented. Native glow is separate
source-pinned donor geometry with measured per-lamp fitting.

ID30/T2 local10 belongs only to the explicit experimental31-record profile.
Do not replace CarID29 or treat package/emulator checks as owner gameplay.
Open`release-candidate/Open-Forester-Workshop.cmd` under private`vehicles/v-def1`,then use the
existing Configure/Validate/Build controls. Original30-entry projects remain
unchanged. Actual race,damage,Results and re-entry require owner verification.

The Forester physics profile owns DefForesterTyre tables:24 original source
coefficients plus36 explicit retail solver defaults. Shared stock tables are
preserved; changing this profile does not globally retune other vehicles.
