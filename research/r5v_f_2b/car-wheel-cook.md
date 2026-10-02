# R5V-F.2b car/wheel cook gate

This gate remains **NOT RUN** until `complete.dx` has passed
`complete-cook.md` validation.

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
files. No cooked files or runtime logs exist yet.
