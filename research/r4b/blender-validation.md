# R4B Blender collision-overlay validation

Tested with Blender **5.2.2 LTS** (`d13f752e3b9c`). All outputs were written
under ignored `.research-output/` paths.

## Synthetic

The generated fixture contains tag 101, tag 102, and a separate unknown
remainder. Headless import, overlay creation, save/reload, and the existing R3
positions-only export passed. No game bytes are embedded in the fixture.

## Real read-only corpus sample

Headless folder import passed for Astero, Pajero, Forester, Bruno, SeatBuggy,
Ufo, and megane: 22 DX resources in total. Required car/complete/wheel samples
and the nonstandard `megane/sus.dx` path were exercised.

- Tag-101 overlays were present on resources that carry tag 101, including
  Astero car and both SeatBuggy car/complete.
- A and B overlay vertices exactly matched the shared source-to-Blender
  coordinate transform.
- Base sphere centre and radius matched parsed values.
- Collision helpers remained non-selectable wire displays and separate from
  render geometry.
- Save/reload retained collection/object metadata.
- Fourteen representative R3 zero-edit exports remained byte-identical.
- No Blender crash occurred.

The existing genuine declared/root-count diagnostics remained visible for
Pajero car, SeatBuggy car, and ChevyBlazer car. They are unrelated to the
collision overlay and were not suppressed.

## Boundary

The overlay is a forensic visualization. It does not add collision data to
resources without tag 101, edit collision bytes, or claim that Blender's
display proves runtime collision behavior.
