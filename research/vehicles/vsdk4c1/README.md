# V-SDK4C.1 reproduction and evidence

All commands run from the `research/vehicles` checkout. Private inputs stay local.
See `docs/sdk/VSDK4C1_RESULTS.md` for findings, exact boundaries and owner tests.
No GT/MR resources are present in this source directory.

## Profiles

- `pajero-source-profile.json`: original Beta source hashes and explicit source
  selections; layered opacity/reflection proof, source-cull backfaces and the
  owner-approved actual-contour housing approximation. No numeric MatN heuristic.
- `subaru-broken-uv-profile.json`: hash-pinned UV-only continuation of the actual
  V-SDK4C repaired Subaru. Its input is deliberately not the frozen mixed-glass DX.
- `validate_candidates.py`: exact resource isolation, collision suffixes, protected
  EXE/DLL hashes, known mutable user-state exclusions and bounded cache prediction.

## Shared conversion

Use a fresh output path:

```powershell
$gt = 'E:/Games/GT_Model-Tools/VOL/GT4-Beta_Extracted/extracted'
$donor = '../corpora/retail/Data.sma_unpacked/DataGx/Vehicles/Navara'
python tools/build_gt4_vehicle.py --source-root $gt --profile research/vehicles/vsdk4c1/pajero-source-profile.json --donor $donor --output .research-output/vehicles/vsdk4c1/my-source-build
python tools/validate_gt4_vehicle.py --source-root $gt --profile research/vehicles/vsdk4c1/pajero-source-profile.json --donor $donor --candidate .research-output/vehicles/vsdk4c1/my-source-build --output .research-output/vehicles/vsdk4c1/my-source-validation.json
```

Existing Balanced texture normalization remains optional and explicit. The local
release uses the prior quality profile, not new blanket resolution reduction.
Continue from the existing author project to retain its physics/audio/UI/camera
profiles; update only source package/resource candidates and new owned texture.
The release author project is `vsdk4c1/pajero-author-r3/project`, and its sealed
roster config is `vsdk4c1/candidate-pajero-final/roster-config.json` under private
`.research-output/vehicles/`.

`vehicle_sdk.py roster-validate --config <config> --candidate <candidate>`
reconstructs and verifies the existing package without launching the game.

For Subaru, `base_glass_profiles` accepts an explicitly ordered list: first the
previous V-SDK4C redistribution, then this UV continuation. Every intermediate
SHA256 is enforced; it cannot silently run on the wrong baseline.

## Windows and native diagnostics

`validate_material_visibility.py` accepts before/after family directories,
preview profile, viewer and output. It makes fixed-camera CW/CCW/NONE and
reflection-mask/env comparisons for race/frontend. NONE remains a diagnostic.

`validate_rally_workshop.py --binding` and `--reflection` exercise real Tk
controls, save/reopen, GPU differences, stock/addon builds and history/restore.
`validate_texture_viewer.py` checks seven zoom levels in two real windows.
`validate_native_glass.py --uv-only` verifies the repaired Subaru continuation,
original x86 switch/deformation replay and per-zone diagnostic captures.
`validate_vehicle_damage_native.py` checks original native instructions and the
qualified alpha adapter. Unicorn/Capstone are optional local research tools.

The local test invocation includes those pre-existing ignored tool modules:

```powershell
$env:PYTHONPATH='src;tools;.;tests/synthetic;.research-output/vehicles/scale1/python-tools'
python -m unittest discover -s tests/synthetic
```

REA confirmed the original PC loader and exact executable identity. Its private
evidence/snapshot are under ignored `vehicles_scratch/vsdk4c1-*`; original native
environment semantics also use the prior `research/r4d_1/` evidence. No native
metadata edit was made, and the REA target was closed after export.

Owner gameplay, collision routing, renderer ordering and measured FPS are still
required. Source coverage or a successful GPU diagnostic is not gameplay proof.
