# R4C Astero collision-translation runtime test

## Automated state

**RUNTIME VALIDATION: CONFIRMED_BY_RUNTIME** per the project owner's 2026-09-23 status update; this document retains the original test plan.

The ignored candidate is generated at:

```text
.research-output/r4c/runtime-test/Astero-car-collision-shift.dx
```

It translates all proven tag-101 positional geometry by `(+0.40, 0, 0)` source
units. Existing coordinate evidence identifies X as lateral, Y as up, and Z as
longitudinal. The physical side represented by positive X is left to the
runtime observation rather than guessed.

Automated audit: 132 changed bytes, all within 39 authorized source-X float32
records; zero unexpected changes; zero visual-geometry changed bytes. The
complete output reparses and validates.

## Human procedure

1. Back up the original `Data.sma`.
2. Replace only `DataGx/Vehicles/Astero/car.dx` with the candidate (renamed to
   `car.dx` in the unpacked tree).
3. Repack as a normal ZIP with 7-Zip and rename `.zip` to `.sma`, using the
   already runtime-confirmed method.
4. Launch an Astero race.
5. Approach a wall slowly with both vehicle sides and compare visible body
   contact with physics contact.
6. Check ordinary handling and damage cautiously.

Report: game load, car load, normal handling, collision existence, visible
offset and side, damage behavior, and any artifact.

## Interpretation

A side-dependent contact offset matching the source-X shift would validate the
first collision writer capability at runtime. Parser acceptance alone does not.
Failure should lead to the smallest tag-101 diff investigation; it must not be
answered by adding scale, rotation, or arbitrary hull edits.
