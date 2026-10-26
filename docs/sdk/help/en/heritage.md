# MR Heritage Garage

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
