# R5V-I.1 historical payload audit — superseded as the qualification blocker

This audit correctly described the available historical/retail vehicle
corpora before the owner authorized an intentionally authored I.1 SDK
qualification family. Its statements about NewRav and demo Rav4 remain valid,
but `REAL_T2_PAYLOAD_REQUIRED` is no longer the current R5V-I.1 gate. The
current target is the Navara-derived, separately named `R5VQualifier` family;
see [the I.1 qualification record](i1-qualification.md). It is not presented
as authentic historical content.

The current retail corpus does not contain a ready, independent T2 vehicle
payload suitable for ID27 qualification.

`NewRav` is not a new-car candidate: the current stock audio matrix maps
physical ID12 to T2 local5 / `Newrav`, and retail already contains its cooked
car, complete, wheel and DXT resources. Reassigning that same family to ID27
would duplicate a stock physical vehicle rather than demonstrate generic
addon support.

The demo 9.3.1 corpus has a distinct Rav4/Rav4Alpha source family with GXM/GXI
resources, but it lacks cooked `car.dx`, `complete.dx`, `wheel.dx` and a
compiled DXT resource package. Retail `DataGame/vehicles.xml` contains no
Rav4 physics profile. This family could be considered only in a separately
authorized cooker/conversion and physics/collision qualification phase; this
R5V-I pass does not begin that work. See
[machine-readable payload audit](payload-audit.json).

**Superseded original gate:** an independent historical/addon T2 family with cooked
`car.dx`, `complete.dx`, `wheel.dx`, all required DXT dependencies and
vehicle-specific physics/collision data, with provenance sufficient to
qualify it as distinct from stock IDs 7–13. This remains relevant to future
content-authenticity claims, but is not required for the authored family-path
qualification currently prepared.
