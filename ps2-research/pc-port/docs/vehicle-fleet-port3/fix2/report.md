# PORT3 fix2: flat native OFF layout, visible lamp rejections, per-frame fleet gate

Base: master 260b580 (PORT3 fix1, DLL cf49fd6a…). Assets and INI are unchanged
from the fix1 runtime kit; only `d3d8.dll` differs.

## 1. NewRav private OFF never reached its contract

Evidence: PID26244 (proxy cf49fd6a, original EXE). F10 frame 42468 is NewRav with
the brake released, healthy, single-car race with fleet CAR replacement active.
The native draw list holds exactly one 18-vertex/10-triangle shared-world draw.
Its tracked state is FVF 0x142 (XYZ|DIFFUSE|TEX1), stream stride 24, material
class VEHICLE_BODY_BASE. Frame 42565 (brake applied) has no such draw; the ON
core 14/10 and glow 28/28 draws are 0x112/32 and were accepted.

`race-fleet-26244-d1-f42468.jsonl` holds no `fleet_lamp_continuity` and no
`fleet_private_off_submission`. The fleet lamp entry admitted only 0x102/20,
0x112/32 and 0x152/36, so the draw returned before owner or identity checks.
Separately, `NativeLampContinuity::topology` had the same whitelist, and the
`no_family_lamp_layout` outcome was never logged. That made the rejection invisible.

The flat layout matches the source finding in `lamp-followup/findings.md`
("native OFF has primary cuindicate64, no secondary reflection texture").

## 2. Identity proof on original bytes

`fix2/prepare_off_fixture.py` loads the hash-pinned original PC NewRav `car.dx`
(615f00a1…), record 34, source vertices 2575..2592. It writes exactly the retail
0x142/24 layout to ignored `ps2-research/data/fix2/newrav-off-0x142.bin`
(SHA-256 e6957e18…). The script re-checks the pinned corner hash.

The canonical CTest `ps2_reflection_pilot_contracts` reads it through
`MRR_FIX2_NEWRAV_OFF_FIXTURE` and checks the unchanged production functions:

- `position_uv_corner_sha == off_followup NewRav positionUv`;
- `exact_native_lamp(18,10, geometry, positionUv) == true`;
- `RaceDamageState::snapshot`: ordered XYZ == `orderedXyz`, ordered UV/index == `uvIndices`;
- the same bytes relabelled as 0x102/20 are rejected; a 1e-3 XYZ shift is rejected.

A synthetic test shows that a 0x112/32 lamp and the same geometry in 0x142/24
produce identical topology, position/UV, geometry and `exact_native_lamp` results.
It also checks that a wrong stride produces an empty topology.

No hash, tolerance, owner, material, texture-generation, buffer revision or
render-state check was relaxed.

## 3. Changes

- `fleet_lamp_native.hpp`: admit 0x142/24 at the native entry. A flat-layout draw
  continues **only** as `layer==2` with a private OFF source. Otherwise it is
  rejected as `flat_native_lamp_layout_requires_private_off`. ON_CORE and
  ADDITIVE_GLOW transactions remain limited to their validated layouts.
- `kia_lamp_continuity.hpp` `topology`: admit 0x142/24. UV is already read from
  the last 8 bytes, which is correct for this layout. The Kia route still
  requires its own exact 0x102 identity.
- Every lamp rejection, including `no_family_lamp_layout`, goes to the F10 probe.
  With diagnostics enabled, it is also written once per family and reason to the
  session log (`BrakeGlow::claim_fleet_rejection`, 64 entries max).
- `fleet_frame_gate.hpp`/`fleet_frame_policy.hpp`: one race certificate per
  device/reset/frame. Entries of `draw_car_fleet`, `draw_fleet_wheel` and
  `draw_kia_wheel` return Stock immediately unless the frame is a live
  single-human-car race with one participant. Each of these effects already
  required that certificate. Their whole-frame suppression also needs a
  submission in the same frame. So outcomes are unchanged, and the gate only
  skips caller-stack walks and buffer copies.
- `frontend_model_native.hpp`: a shape pre-filter before `select_frontend_fleet`.
  The race world callsite is the same `0x17707E`, so every world draw used to
  walk the caller stack. Only shapes in the active profile, or a unique
  frontend-fleet source when fleet selection is on, can be selected later. The
  filter mirrors exactly those tests.

## 4. Measured motivation (PERF1 timing builds on fix1 sources)

In a multi-car France1 race, per-frame proxy cost measured: frontend 0.85–1.4 ms,
wheel 0.33–0.9 ms, race 0.22–0.5 ms, brake 0.17–0.37 ms, race_part 0.11–0.28 ms.
All fleet effects are Stock by design in that race. The gate and pre-filter
target exactly this waste. New numbers require a timing build of fix2.

## 5. Not changed / still open

- The fleet remains single-car-race only; opponents keep Stock models.
- Bruno and Mattserati OFF draws are not yet observed in a fix1/fix2 F10; their
  native layout is unverified. Their rejection reasons are now logged.
- The 22 unsupported full PS2 deformation maps remain Stock after damage.
- Reflection classification (~1–1.6 ms/frame) and the baseline `sha256_bytes`
  provider cost are not addressed here. The frozen renderer is unchanged.
- No global lamp brightness or colour change.

## 6. fix2 runtime result (PID21408) and fix2.1 correction

fix2 (DLL 81590049…) runtime, single-car races. The OFF draw now reaches the
private path for all three families: `fleet_lamp_continuity` layer OFF at NewRav
F3855, Bruno F10137 and Mattserati F12919. All three are rejected with
`private_off_native_uv_or_layout_rejected`. ON_CORE and ADDITIVE_GLOW stay
accepted with hresult 0 (F5437, F10250, F13039). The damaged NewRav F6410 keeps
7 `fleet_native_damage_reflection` records with hresult 0 and
`unsupported_private_tree`. Bruno and Mattserati also log a separate
`no_family_lamp_layout` draw; it is now visible and is not a regression.

Cause: the private OFF ordered UV/index contract (fix1 `prepare_off.py`) hashed
car.dx indices in file order. `verify_loader_winding.py` checks every
non-private fleet-damage dump in the Pristine logs: 250/250 records (NewRav,
KiaSportage; FVF 0x142 and 0x152). It finds the car.dx vertex order unchanged and
every triangle submitted as (b,a,c) for file (a,b,c); see
`flip_rule_evidence.json`. Position/UV corners, geometry and ordered XYZ do not
depend on winding and were already accepted at runtime.

`correct_uv_winding.py` proves each old pinned value equals the file-order hash.
It then replaces only `uvIndices` for NewRav, Bruno and Mattserati in
`renderer/fleet_private_off_registry.hpp`, `lamp-followup/contracts.json` and
`off_mapping.hpp`. `prepare_off.py` now emits loader winding. The fixture is
rebuilt in loader winding (SHA-256 511484311e…). The CTest additionally checks
that file winding does **not** satisfy the ordered contract, while the
winding-independent identity still matches. No tolerance or other hash changed.
