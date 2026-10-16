# PORT3 fix6: UFO OFF, Mattserati and Tata keep the PS2 CAR after collisions

fix5 (IceCream) is user-confirmed in game.

## Mattserati and Tata damage

Under option A both failed closed on one "mixed" component (one that also has
exact vertices). Mattserati has two symmetric 16-vertex pieces in root.2: 8 exact
plus 8 unresolved vertices, 5–6.3 cm from the PC surface. Tata has a 71-vertex
root.0 piece with 9 unresolved vertices, 3 of them at up to 7.5 cm. Copying the
displacement of the nearest proven vertex was evaluated and rejected: those
vertices are 0.56 m and 0.28 m away. Instead, mixed components may use
surface-bound transfer up to `MIXED_LIMIT` = 0.08 m. PS2-only components keep
the 0.05 m rule, so crew bodies stay rigid. Only the Mattserati and Tata registry
arrays changed; the other 23 profiles are byte-identical. All 24 non-X-Trail
families are now eligible. `widened_components` in car/contracts.json lists the
exact pieces and distances.

## UFO OFF

The lamp registry rejected UFO because its OFF material is not carshiny.
PS2 conditional `root.9.1.0` is `$shader(carbrakelight)` with b_light + perspex.
It pairs with PC record 11 (`8.2`, 85v/90f, b_light + perspex) at XYZ residual
4.8e-7 and exact UV: an exact pair. The PS2 CAR route already draws UFO's
unconditional `root.3`, with the same material and textures, as mode 3 using
its own perspex layer (`mixed_reflection=false`). The new private OFF does exactly
the same: `off_followup::Profile::mixed=false` selects the asset's perspex
texture instead of the PC framebuffer capture. Carshiny families are unchanged
(`mixed=true`). New asset `port3-UFO-OFF.ps2model` (bd25d732…). The four earlier
OFF binaries are byte-identical to the runtime-verified ones.

## Verification

Canonical fixture build: CTest 24/24 and 34/34, Python 133 OK, baseline DLL
unchanged. With original fixtures: Mattserati (715 surface-bound) and Tata (15)
pass uniform-shift; UFO private OFF passes the full original-source identity
contract (0x152/36, loader winding, file-winding/relabel/shift negatives).
Docs tests: car 11/11, lamp-followup 6/6.

## Open

- Navara co-driver face: separate crew-face1 task.
- Reflection/lighting intensity versus PS2: the next phase.
