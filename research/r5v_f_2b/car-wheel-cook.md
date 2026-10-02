# R5V-F.2b car/wheel cook gate

The complete-only gate passed on 2026-10-02. The isolated car/wheel cook is
**AUTHORIZED, NOT RUN**.

For the isolated runtime tree, `car.gxm` and `wheel.gxm` are present while
`car.dx` and `wheel.dx` are absent. An offline Practice or Quick Race should
force normal retail resource loading only to produce caches. Capture the car
and wheel `Reading GXM`, `Making dx model`, and `Saved cached model` messages.
Exit as soon as both caches are written; do not do aggressive driving or
interpret this as gameplay validation.

Before accepting either output, require revision 135, modern parser PASS,
finite geometry, valid material/dependency closure, and a valid footer. For
`car.dx`, validate the tag101 collision data with the current R4G tooling.
Compare geometry and collision semantically to the selected legacy rev127
files. Preserve the isolated runtime copy and capture separate car and wheel
`Reading GXM`, `Making dx model`, `Saved cached model`, and subsequent load
events. No aggressive driving, gameplay acceptance, or original-binary edits
are part of this cook trigger.
