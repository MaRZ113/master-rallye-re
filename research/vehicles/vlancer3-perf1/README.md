# V-LANCER3 PERF1: native texture-cache thrashing

Branch: `research/vehicles`. Narrow correction to the delivered Lancer build.
Private candidate: `.research-output/vehicles/vlancer3-perf1/candidate/`.
Use its `Launch-Lancer.cmd` and matched launcher/runtime together. Do not copy
individual resources into an older sealed runtime.

## Evidence and cause

The user's Vehicle Select capture proves visible Lancer geometry and reports
about one frame per 15 seconds. The real game log is
`D:/Game/Master Rallye/MRRRenderer/logs/session-20261023-073802-21328.jsonl`
(SHA256 `4440e7f50a9545b3ce0521edfa09f10bc23af60b14fbfc06605f61cde1fe7575`).
Pristine-directory logs are older and were not used as this session's evidence.
Frames 3171 through 3238 each contain **137 CreateTexture events**, with
creation return address `005589D0` in the original EXE. Frame 3180 recreates
35,349,248 source-pixel bytes. Its 6,227 triangles / 162 indexed draws are not
an unusually large geometry workload. The trace has no per-frame elapsed-time
field: the exact 15-second timing is the user's observation, not a profiler result.

REA/Ghidra analysis and independently checked original PE instruction bytes:

- Exact EXE SHA256: `bf8aef32407eb6552c05045b8abef149f32983cedd9503b865069b444c5f96b4`.
- `0053CDF0`, instruction `0053CE94`: texture-manager field +0x38 starts at
  `0x02000000` (32 MiB).
- `0053D2F0`, `0053D4BD..0053D5C7`: charges original width*height*4 to +0x30,
  compares with +0x38 and evicts old loaded textures. The accounting does not
  shrink with TextureQuality, GPU format or compressed on-disk size.
- `005587E0`, call at `005589CD`, return `005589D0`: native CreateTexture path.

32 MiB is the original constructor's statically verified default. No live
process memory snapshot of the cache fields was taken; the user had closed
the game. The unchanged SDK native patch operations do not alter this budget.

The old GT4 clamp bake allocated at least four original widths on each clamped
axis even for ordinary [0,1] UVs, multiplying two-axis texture area by at least
16. The Lancer frontend alone consumed 33,103,872 bytes, leaving only 450,560
bytes for the rest of this 32 MiB cache. Menu/UI resources then competed with
it, explaining the observed repeated uploads. This is an asset working-set
failure; no renderer-DLL or executable patch is required.

## Correction

`guarded_clamp` now computes required extension in **texels**, uses the smallest
admitted power-of-two extent, and centres the source where feasible. It keeps
the original pixels and uses an affine UV remap; repeat axes remain unchanged.
No per-vertex clamp, downsample, polygon removal or guessed geometry repair.
The complete source interval, bilinear edge footprints, region-clamp semantics,
finite-coordinate checks and expansion bounds remain covered.

| Native source-pixel accounting | Before | PERF1 |
| --- | ---: | ---: |
| All referenced family textures | 33,431,552 B / 59 files | 10,903,552 B / 64 files |
| Frontend `complete.dx` | 33,103,872 B | 10,297,344 B |
| Race body `car.dx` | 32,182,272 B | 9,883,648 B |
| Standalone `wheel.dx` | 593,920 B | 331,776 B |

Different draw UV extents explain five extra deduplicated raster variants;
total charged memory falls by about 67%. There is no loss of source resolution.

Reusable SDK changes:

- Shared texel-bounded clamp baking.
- `texture_budget.py`: real DX/DXT dependency accounting and a bounded LRU model
  derived from the qualified native path. Union of frontend/race/wheel is
  conservative: these models are not claimed simultaneously drawn.
- GT4 build/validation rejects family working sets above a **16 MiB authoring
  policy**, leaving half of the native 32 MiB cache for other resources. This
  is not a newly discovered engine per-car limit or a guarantee for every race.
- Preview staging reports native residency; the command-line preview launcher
  warns above the authoring policy. Its D3D9 texture ownership does not emulate
  native MR cache eviction, so a fast preview must not establish runtime speed.
- `tools/analyze_vehicle_texture_budget.py` exposes the calculation for other
  converted vehicle families. No source assets or vehicle-specific thresholds.

## Validation and boundaries

Private evidence/reports under `.research-output/vehicles/vlancer3-perf1/`:

- `evidence/renderer-log-summary.json`, native REA excerpts and exact PE byte
  verification: observed upload storm plus cache admission/eviction evidence.
- `geometry-regression.json`: all three vertex position/normal/colour buffers,
  local/global indices, collision/bounds suffixes, draw order, material flags
  and wheel rig are identical to the preceding candidate. Only texture stems
  and affine UV representation change.
- `sampling-regression.json`: every emitted textured packet retains identical
  source RGBA pixels including alpha. Largest serialized affine error is
  0.00003052 original texels; no resampling/downsampling of source detail.
- `offline-validation.json`: deterministic DX/DXT regeneration, all source
  inventories and frozen Subaru resource/native-patch verification pass.
- `before.png` / `after.png`: same native preview executable and camera. Mean
  absolute channel difference is below 0.000012 / 255 in this view. Native MR
  mip/quality behavior still requires human comparison.
- `cache-before.json` / `cache-after.json`: serialized DX binding-order LRU
  simulation with an explicit **synthetic 8 MiB background reserve**. Frontend
  misses over three cycles change from 58/57/57 to 62/0/0. This is a model, not
  an actual post-fix game trace, and does not reproduce the full MR draw queue.
- Synthetic suite: 623 tests, one skipped, zero failures.
- Candidate resource verification and matched native launcher preflight pass.
  Existing native patch manifest/operations and both Lancer UI PNGs are
  byte-identical to the preceding candidate. Original EXE/DLL remain pinned.

This addresses the demonstrated texture churn mechanism. The revised candidate
has **not** been launched in Master Rallye during this pass. Actual frame rate,
long menu navigation, race loading and other vehicle/world working sets remain
human runtime gates. No FPS improvement is claimed as measured.

## Human test

1. Close the old game instance. Start **PERF1** `candidate/Launch-Lancer.cmd`.
2. Select Lancer, allow the first load to finish, then leave the rotating model
   visible for 20 seconds. Check animation and menu input responsiveness.
3. Switch to a stock car and back to Lancer several times. If responsive, test
   race loading/driving with the same graphics settings.
4. If the stall persists, provide the new log under the main game
   `MRRRenderer/logs` directory. Compare warmed steady frames: native
   CreateTexture should no longer repeat ~137 times on every frame. One-time
   uploads during first load or a vehicle transition are expected.

Subaru V-MESH4.13 remains frozen in its separate bundle. This candidate retains
the already qualified Mercedes ID26/T1 + Lancer ID27/T2 integration; it does not
add simultaneous Subaru/Lancer capacity. Physics, wheel fitment, stock vehicles,
Randomizer and renderer binaries were not changed.

## Reproduce

Use the existing V-LANCER3 profile and private GT4 source/donor inputs with
`tools/build_gt4_vehicle.py`, then `tools/validate_gt4_vehicle.py`. The new
budget gate runs automatically. Reproduce the cache comparison with:

```powershell
python tools/analyze_vehicle_texture_budget.py C:/private/vehicle/assets --output C:/private/cache-report.json
```

`--background-bytes` selects the explicit synthetic background reserve.
Subsequent project/runtime/launcher steps use the existing SDK workflow. No
new native capacity hooks, quality setting changes or retail asset bundles.
