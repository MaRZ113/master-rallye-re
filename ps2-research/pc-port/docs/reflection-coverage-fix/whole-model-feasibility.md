# Whole PS2 vehicle-model fallback

The user authorized considering a complete PS2-model transfer when existing PC
body partitions obstruct reflection restoration. It is a credible fallback,
but not an interchangeable PSM-to-DX file swap. This task makes no vehicle
asset replacement or physics changes.

PS2 strips/material groups and PC compiled draws can partition the same shape
differently. Forester rear/lights are a concrete example: a single PC draw
contains geometry from PS2 shiny and untyped materials. Other PC streams lack
normals (FVF0x142), although an original compiled source may contain them. An
entire PS2 visual body could preserve the original material boundaries and
normal/UV inputs, avoiding increasingly permissive PC material classification.

The smallest prospective test would be **PS2 WOOLDAND visual body on PC
Forester**, with original PC chassis, physics and pose ownership retained.
It requires these proofs before activation:

* A complete, stable current PC body draw set that can be suppressed exactly,
  without suppressing wheels, driver, headlights, UI or other vehicles.
* Original PS2 body subset, model-local axis/origin/scale and normal/UV/color
  layout; conditional children and LOD must be explicitly selected.
* Current PC body world transform and vehicle-generation ownership. Historical
  addresses, shared emitter or texture names are insufficient.
* Separate wheel, glass, driver, brake/light and damage contracts. Omitting these
  does not qualify as a complete vehicle-model port.
* Private decoded geometry/texture resources with hashes, checked allocation,
  rollback, Reset/device-loss and destruction. No original EXE/course mutation.
* An original-source material path for untyped/default PS2 groups and the literal
  `crashiny` typo, before claiming the entire model reflects uniformly.

A read-only model comparison and one opt-in visual-body pilot can precede a
full replacement. Source conversion would remain local/ignored; no proprietary
PSM, DX or original images would be committed or included in handoff. Native
physics collision would remain the original PC implementation.

**Decision:** retain this fallback for remaining mixed-source/normal-less body
regions; first test the present strict material correction. Full-model transfer
is not implemented or represented as already safe. The next runtime captures
will establish which obstacle actually remains and whether replacement is
necessary.
