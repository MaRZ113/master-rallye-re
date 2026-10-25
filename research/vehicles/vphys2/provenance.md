# Evo IV profile provenance

## Recovered local GT4 Beta data

`specdb/GT4_PREMIUM_US2560` from the immutable user source. Explicit labels are
in `gt4-handling-labels.json`; the reusable inspector records source/row hashes
and raw decoded rows only in ignored private output. Admitted layouts:
CHASSIS37, ENGINE113, GEAR45, DRIVETRAIN21. PDTools Beta metadata in the user's
local tool tree supplies comparative field names; it is not source ELF proof.

- CHASSIS codes: length4330, height1405, wheelbase2510, mass1230.
  mm/kg interpretation is consistent with earlier traced rig and official
  contemporary dimensions/minimum rally mass. Existing rig remains 1.49 m
  tracks and .32535 m visual tyre radius; no frozen wheel edit.
- ENGINE display power284, torque5000; 13 torque/rpm samples; shift65, rev70.
  Interpreted rpm codes span 1000..7000, torque code5000 is consistent with
  50 kgf-m. The candidate normalizes **ratios** of those codes into six MR
  knots; absolute peak torque is separately documented below. This is a
  resampling/translation, not a claim of native GT4 physics reproduction.
- GEAR exposes default final code4875 (interpreted 4.875), six-speed code6,
  but zero explicit gear ratios: they are generated/source-dependent and cannot
  be copied as a functioning MR transmission. Native MR donor array remains
  seven entries: reverse, neutral, **five** forward. Ratios are manual choices.
- DRIVETRAIN drive code2/type4WD data are retained privately. MR AWD is selected
  from **MR's own instruction routing**, not by assuming equal GT4 enum values.

## External primary comparison

[Mitsubishi's 1997 WRC history/specification](https://www.mitsubishi-motors.com/en/brand/motorsports/wrc/1997/)
states 4330x1690 mm, 1997 cc 4G63 turbo, 290 PS and 50 kg-m; its history describes
the 4WD system/sequential gearbox and the 1230 kg minimum for Group A/WR cars.
The engineering unit conversion 50 kgf-m *9.80665 gives 490.3325 N m.
GT4 Beta's displayed284 and official290 are distinct observations. The MR
curve plus native friction is not forced to claim either exact advertised power.

## Manual MR prototype settings

Independent unsprung masses, gyration radii, CG, spring/damper/roll rates,
application points, travel, alignment, steering, brake balance, LSD ratios,
engine inertias/friction and five-forward ratios are editable tuning values,
not GT4- or factory-measured physical parameters. Generic harddirt/surface
tables remain original. No private compound table, AYC or turbo model is added.

The 2.60 m candidate wheelbase is a **user-approved shell-fit calibration**.
Its basis is explicit V6 upper arch-edge geometry, not a revised real-car spec.
The 2.51 m controls preserve the nominal GT4 value. Neither exact concentric
arches nor ideal loaded wheel centres are asserted from that approximation.

Collision fitting scales an existing native hull to selected structural body
draws; it preserves topology and doesn't rebuild a GT4 collision surface. It
is documented separately from both real-car dimensions and visual mesh bounds.
