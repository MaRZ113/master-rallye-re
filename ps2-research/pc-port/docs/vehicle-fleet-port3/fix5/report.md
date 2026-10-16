# PORT3 fix5: IceCream PS2 CAR (untextured 0x42 record)

## fix4 runtime result (PID23616, DLL 776c5b05…)

Damage continuity with option A is confirmed on damaged private trees:
`fleet_car_private_submission` with private_damage_tree=true,
deformation_transfer=SURFACE_BARYCENTRIC and draw/restore hresult 0 for NewRav
F5845, Bruno F12452, Jump F27702, Patrol F35611 and Navara F72079/F72272. The
private OFF also continues on damaged NewRav, Bruno and Jump. Jump private OFF
healthy F23272, ON/glow F23334. The user saw no critical tearing beyond the
game's own damage style.

## IceCream

IceCream was not a damage regression: its PS2 CAR never certified (healthy F18516
included) with `descriptor_or_current_token`. All 20 sources were matched by
geometry, but source 3 (20v/20f, all texture slots Null) is submitted by the retail
game as FVF 0x42 (XYZ|DIFFUSE) with stride 16. `fleet_source_snapshot` and
`RaceDamageState::snapshot` only admitted 0x142/0x152/0x112, so the whole car
stayed Stock. The lamp path requires a certified body, so ON_CORE and glow also
stayed PC. The original-car fixture stores every record as 0x142/24, which is why
the offline test did not catch it.

It is the only untextured CAR source in all 25 families, and its car.dx UVs are
exactly (0,0) for all 20 vertices. For 0x42/16 the certificate now uses that
authored zero UV. Ordered positions and the loader-winding index certificate are
unchanged, and the result reproduces the pinned `native_uv_winding_sha256`
exactly. Other layouts are byte-for-byte unchanged.

Tests: `untextured_record_certificate` (0x42 equals 0x142 with zero UV, a non-zero UV
differs, a wrong stride is rejected). With original fixtures, IceCream source 3 is
rebuilt in the retail 0x42/16 layout and matches its pinned ordered position and
UV/winding certificate.

## Open

- Navara co-driver white face: a PS2 content defect, also present in the original
  game. It needs a deliberate texture/UV correction on the face triangles and is
  tracked separately.
- Mattserati and Tata damage stay Stock (option A fail-closed components).
