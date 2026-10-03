# T3 — Mercedes collision and damage

## Result

**CONFIRMED_BY_RUNTIME** for the tested native-retail Mercedes package:

- solid barrier contact produced normal collision response;
- no gross hull offset or pass-through was observed;
- external damage was observed working;
- internal damage was observed working.

Glass breakage is not expected for this early Mercedes model and was not
treated as a collision/damage failure.

These observations were supplied by the project operator as the completed T3
runtime result. No separate raw T3 capture was present in the branch inputs
when this record was prepared.

## tag101 structure

The native-retail cooked `car.dx` contains a finite, structurally valid
tag101. Rep A has 8 vertices and 12 triangles; Rep B has 34 vertices and 64
triangles. Both passed the current closed/Euler-2/convexity checks and a
zero-edit serializer roundtrip. Cook A and Cook B DX outputs were byte
identical for this exact source and cook environment.

Core hull geometry/topology matches the legacy revision-127 control within
the measured float drift. A bounded 36-byte secondary face-descriptor delta
remains semantically unresolved. Retail native production of the structure
and successful gameplay do not reveal an independent offline producer for
those descriptors.

## Boundary

The practical source-to-runtime package path can obtain a usable native
tag101 by delegating the cook to the original retail runtime. The unresolved
secondary descriptor semantics in R-DEMO2 remain open for a future
independent collision writer; R-DEMO2 is not marked solved by this result.
