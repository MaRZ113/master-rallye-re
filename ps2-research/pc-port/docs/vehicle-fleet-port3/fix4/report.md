# PORT3 fix4: PS2 CAR kept after collisions (DAMAGE2 option A)

Includes fix3 (Jump private OFF). Policy chosen by the user: option A in
`../damage2/README.md`.

## Policy as implemented (`car/prepare_contracts.py`, offline)

- Exact vertices (within 1e-5 of an original PC vertex, or proven through two
  neighbours within 0.005) keep their exact per-vertex PC deltas, as before.
- Each unresolved PS2 vertex is pinned to its nearest non-degenerate healthy
  PC source triangle: slot, three native vertex indices, barycentric weights.
- Components are PS2 asset connected components (shared indices or identical
  positions):
  - a component with any exact vertex admits its unresolved vertices only if
    all are within 0.05 m (surface-bound transfer); otherwise the family fails closed;
  - a PS2-only component (no exact vertex) is transferred as a whole if all of
    it lies within 0.05 m, otherwise it is rigid as a whole (no tearing).
- Kia (own runtime-proven state), UFO (already exact) and X-Trail (separate
  route) are unchanged. Their registry arrays are byte-identical.

Result: 20 additional families are eligible. Mattserati (mesh 2: 8 of 16
vertices beyond the limit, up to 0.063 m) and Tata (root.0: 3 of 9, up to
0.075 m) fail closed and keep the existing native-damage Mode 4 fallback.
Rigid components are recurring driver/co-driver bodies (≈285 + 210 vertices
at x≈±0.3 m, seat height, plus 110-vertex heads) and small front/underbody
details. No exterior body panel is rigid. Per-family numbers are in
`car/contracts.json` (`transfer_vertices`, `rigid_components`,
`max_transfer_distance` ≤ 0.0496 m).

## Runtime

`FleetDamageState::delta`: a vertex with no exact candidate and no static/rigid
entry takes Σ wᵢ·(currentᵢ − healthyᵢ) of its pinned triangle. A missing slot,
reference or index fails closed. All existing gates are unchanged: live owner,
race/lifetime, complete owner-bound source set, per-record material token,
loader-winding UV/index certificate, and multi-candidate delta consensus.

Events `ps2_fleet_car_replacement` and `fleet_car_private_submission` now carry
`deformation_transfer` (`SURFACE_BARYCENTRIC` or `EXACT_ONLY`),
`transfer_vertices` and `max_transfer_distance_m`. They never claim exact
identity for transferred vertices.

## Verification

- `car/test_contracts.py` (11 tests): vertex accounting, the 0.05 m bound, rigid
  components only beyond the bound, Mattserati/Tata fail closed, Kia/UFO/X-Trail untouched.
- CTest `ps2_frontend_model_contracts`:
  - `damage_transfer_contract` checks the barycentric formula, static
    vertices, and that an unknown slot, unknown vertex or changed material
    token fail closed;
  - with the original fleet fixtures (`build_fleet_port1.ps1`), every eligible
    family is checked: under a uniform 0.125 shift of every PC source record,
    every referenced PS2 vertex moves by exactly 0.125 except static/rigid
    vertices, which stay. 21 families pass (20 new + UFO).
- Full canonical build: CTest 24/24 baseline and 34/34 PS2, Python 133 OK. The
  baseline DLL is unchanged (b923a74d…).

Pixel or deformation parity with PS2 is not claimed for transferred vertices;
runtime acceptance is pending.
