# Reproduce V-PHYS2 and reuse it

All commands run from this repository on `research/vehicles`. Inputs remain
local/private; generated game assets and raw diagnostic captures are not source
handoff content. Python tools use the existing shared project/compiler.

```powershell
python tools/build_vehicle_physics_candidate.py `
  --project .research-output/vehicles/vlancer6/candidate-04/project `
  --profile research/vehicles/vphys2/fitment-260-physics.json `
  --output .research-output/vehicles/vphys2/my-fresh-fitment
```

Use `handling-260-physics.json` for handling. Output must be a new ignored
directory. Builder verifies original source archive, independent named family,
typed configuration, reference guard, optional collision selection, sealed
runtime resources, launcher environment and native allocation. It does not
launch the game. Edit profile and rebuild; do not hand-edit sealed XML/assets.

New optional fields in the existing physics-profile.json:

```json
"ride_height_reference_m": {"Front": -0.15, "Rear": -0.15},
"collision_fit": {
  "source_sha256": "<exact pre-fit compiled car.dx hash>",
  "core_draw_indices": [0, 1],
  "padding_m": [0, 0, 0],
  "evidence": "Describe the explicitly selected structural shell and exclusions."
}
```

Reference is optional, bounded +/-0.5 m, named-family scoped and applied only
to physical participant publication. Without it, the old behavior/code remains.
Collision fit is optional, bounded to scale [0.5,1.5], pins exact input, and must
be selected per vehicle. It never infers a core shell from complete bounds.

```powershell
python tools/diagnose_vehicle_fitment.py `
  --assets <candidate>/runtime/resource-root/DataGx/Vehicles/LancerEvo4 `
  --vehicles <candidate>/runtime/resource-root/DataGame/vehicles.xml `
  --family LancerEvo4 `
  --reference-profile .research-output/vehicles/vlancer6/build-04/preview-profile.json `
  --physics-profile research/vehicles/vphys2/fitment-260-physics.json `
  --output <private-output>.json
```

Optional `--modifications`, `--player-state`, `--player 1|2` expose effective
saved setup without editing it. Previewer uses equivalent `--physics-xml`,
`--physics-family`, `--physics-profile`, `--modifications-xml`, `--player-state`
flags on `tools/preview_vehicle.py <car.dx>`. It writes separate `.physics.json`
attachment frames and `.setup.json` force/setup diagnostics, then uses the
ordinary fixed-function renderer. These are static calculated frames only.

`diagnose_vehicle_wheel_arches.py` takes a pinned model and explicit vertex-index
selection; it reports approximate arch circles and longitudinal asymmetry,
never changes physics or promotes fitted centres into recovered source hubs.

`inspect_gt4_handling_spec.py --spec-folder <user-source> --labels <labels.json>
--output <private-report.json>` is optional. Raw rows stay private; the SDK does
not require bundled GT data. Other sources/custom vehicles can use donor-based
typed profiles and manual, documented provenance instead.

Native validation uses installed optional Unicorn/Capstone from the prior
research tool directory on PYTHONPATH. `validate_vehicle_physics_forces.py`
executes original retail functions with generated input blocks; it does not run
a race. `validate_vehicle_physics_candidate.py` proves XML/resource scope and
reconstructs the exact additional family adapter, while permitting only the
declared collision transform. Existing alpha payload and UI/identity code are
independently compared. Full synthetic tests use no bundled proprietary assets.
