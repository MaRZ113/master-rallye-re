# R-GRID8 remediation boundary

R-GRID8 produces a course-by-course start-clearance map. It makes no course or
gameplay change. Do not edit RaceTest XML, StartArea markers, course geometry,
collision assets, or the global `0x0048EB40` grid formula during the audit.

For every non-clean course, record one primary result, issue tags, affected
CarN slots, capture label, and a short observation. The audit tool refuses to
record a non-clean result without affected slots. Distinguish vehicle overlap,
static geometry, terrain/boundary contact, unstable impulse, and invalid
position rather than collapsing all failures into “bad start.”

Only after all 36 resources have runtime results should a separate remediation
pass compare the failures. Prefer course-specific StartArea refinement or
localized geometry changes if only a small subset fails. Preserve the original
heading, race direction and 1–4 car starts. Re-test each changed course at
normal counts and eight cars. A later change to the native grid formula needs
separate broad regression evidence.

Do not infer 9+ capacity or generic-N from the eight-car start positions.
