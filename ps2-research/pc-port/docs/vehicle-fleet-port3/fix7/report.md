# PORT3 fix7: UFO OFF under the retail dome order

fix6 runtime (PID30316, DLL d30ae3ea…): Tata F60088 and Mattserati F71793 damaged
→ `fleet_car_private_submission` SURFACE_BARYCENTRIC hresult 0 (PS2 CAR kept);
Mattserati private OFF continues on the damaged tree. UFO F74125: the OFF draw
reached the private path but was rejected with
`private_off_cold_or_changed_healthy_reference`.

Cause: PC record 11 (`8.2`) consists of five identical 17-vertex lamp domes with
one UV layout (contiguous ranges 0–16 … 68–84). The exact position/UV corner
identity and the ordered UV/index certificate are block-order independent and
passed; the ordered XYZ certificate is not, and the retail game submits the domes
in another block order than car.dx.

Fix: `ps2port::block_source_order` (fleet_off_deformation.hpp). For a healthy
owner whose ordered XYZ differs, contiguous index-components of equal size and
identical UV bytes are permuted (≤720 combinations) and an order is accepted only
if it is the unique one whose ordered positions hash exactly to the pinned
`orderedXyz`. The order is stored with the owner's healthy reference and applied to
every later frame, including damaged private trees, before the source-mapped
deformation. Profiles whose ordered XYZ already matches are unaffected.

Tests: the original UFO fixture with domes 0 and 3 swapped fails the plain ordered
contract, keeps the UV certificate, and resolves to exactly the source order;
a 1e-3 shift yields no order; two identical blocks at identical positions are
ambiguous and yield no order.

Observed separately (not changed): UFO body/glass reflection intensity versus PS2
belongs to the lighting phase.
