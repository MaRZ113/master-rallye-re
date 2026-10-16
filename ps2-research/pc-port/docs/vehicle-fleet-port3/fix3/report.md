# PORT3 fix3: Jump private OFF, private OFF identity proven for all four families

## fix2.1 runtime result (PID26412, DLL 03c3de12…)

Single-car races, brake released. `fleet_private_off_submission` with
draw_hresult=0 and restore_hresult=0 for Mattserati F4548, Bruno F6610 and
NewRav F10291. The user visually confirmed reflections in the former OFF zones.
With the brake applied, ON_CORE and ADDITIVE_GLOW stay `healthy_exact_source`
(F4680, F6723, F10395). Damaged Bruno F7858 shows `unsupported_private_tree`
with 5 `fleet_native_damage_reflection` records at hresult 0. Bruno and
Mattserati keep one extra `no_family_lamp_layout` draw per frame; it is not
an OFF record.

## OFF inventory (lamp source registry, 25 families)

- 19 families have a two-texture native OFF source (lamp + perspex/glass/
  whitepaint) and use the existing exact Mode 4 path.
- NewRav (flat one-texture source), Bruno (UV revision) and Mattserati
  (geometry revision 0.008) use original private PS2 OFF meshes (fix1–fix2.1).
- Jump was `BLOCKED_NO_EXACT_OFF_PAIR`: PC record 29 (8v/4f,
  jumplights32 + perspex) versus PS2 root.21.1.0 has a measured geometry
  revision of 0.0024014 with exact UV. This is the Mattserati case, so fix3
  adds Jump to the private OFF generator with its measured asset limit 0.0025.
  That limit applies only to offline asset preparation; runtime admission
  remains exact.
- UFO stays Stock: it has no verified conditional carshiny OFF pair.

## Changes

- `lamp-followup/prepare_off.py`: adds Jump and records the loader winding.
  NewRav, Bruno and Mattserati keep their runtime-verified fix1 binaries
  (35245ca4…, 919cd663…, e7ae8b38…). The registry pins those exact files;
  only their embedded metadata predates the winding correction.
- New asset `port3-JUMP-OFF.ps2model` (7dae8307…, 1 mode-3 carshiny mesh,
  original normals/colours/UV/textures).
- `renderer/fleet_private_off_registry.hpp`: adds the Jump profile.
  `BrakeGlow::private_off_reference` grows from 3 to 8 entries, and a
  `static_assert` guards it against the profile count.
- CTest `ps2_reflection_pilot_contracts` (`MRR_FIX2_PRIVATE_OFF_DIR`) rebuilds
  every private profile from its pinned car.dx record in retail layout and loader
  winding. It checks topology, positionUv, exact geometry, ordered XYZ and
  ordered UV/index. It also checks that file winding, a relabelled layout and a
  1e-3 shift are rejected. All four pass.

## Open

Jump OFF and the 12 two-texture families not yet seen in runtime captures need
F10 confirmation. Damage continuity for 22 families is a separate decision; see
`../damage2/`.
