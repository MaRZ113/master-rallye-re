# Mercedes collision validation

## Authentic reference

The authentic source is tag101 in
`demo-8.4.1/DataGx/Vehicles/Copy of Mercedes/car.dx` (revision 127, 5,668-byte
collision record; full DX size and hash are in
[mercedes-source-manifest.json](mercedes-source-manifest.json)). Its full
`car.dx` SHA-256 is
`989905468d528bb35dec7901b03a08367b37a1fa4f8a32143428a782253d0791`.

The preceding F.2 audit reported finite values, closed/convex structural
checks, and a byte-identical zero-edit tag101 serializer round-trip for this
reference. This is static collision evidence only; it is neither retail full-DX
validation nor an in-game collision test.

## Cooker preservation

No retail-cooked `car.dx` exists, so authentic tag101 retention/build behavior
is **NOT TESTED**. The cooked-car gate remains blocked until a revision-135
output is parsed and checked for finite base/scalar and Rep A/B data, topology,
convexity/manifold constraints, and serializer round-trip. Compare the result
with the authentic Mercedes reference. Do not substitute donor collision.
