# Mercedes collision and damage runtime — T3

**Closed — `CONFIRMED_BY_RUNTIME` for collision, external damage, and internal
damage.** See [oracle-t3-collision-damage.md](oracle-t3-collision-damage.md).
The steps below are the historical test plan, not a pending gate.

**Gate:** determine whether the native-retail rebuilt Mercedes tag101 is
usable in ordinary gameplay, while keeping the secondary descriptor delta
unresolved.

## Candidate and known structure

Use the cache-only T2 package at
`.research-output/r-cooker3/oracle-t2-t3/runtime/`. Its `car.dx` SHA256 is
`5ec5f7480ddfc1380131a012b300a4cdeb28b869a1668b6f8bbe97210893ff44` and
contains the native retail Mercedes tag101 rebuilt from `car.gxm`.

The parsed 5,668-byte tag is finite and structurally valid. Rep A has 8
vertices / 12 triangles; Rep B has 34 / 64. Both are closed, Euler-2, and
convex under the existing checks. Core geometry/topology agrees with legacy
rev127 within bounded float drift. A bounded 36-byte secondary face-descriptor
delta remains unresolved. Do not call it meaningless or byte-equivalent.

## Human test

Perform this after the T2 package preflight, preferably in the same isolated
Practice/Quick Race session after recording T2 load evidence:

1. If available, use the Broker Observatory to record
   `Race/Car0/CarID = 26`, `CarType = Mercedes`, and
   `WheelType = Mercedes`. This is useful identity evidence, not a gate.
2. On a normal solid course barrier/obstacle, first make a controlled
   low-speed contact and observe collision response. Check for pass-through,
   gross hull offset, or severe instability.
3. Exercise ordinary damage through normal gameplay contact. Observe whether
   the damage system responds and whether the game remains stable. Do not
   infer damage from collision alone.
4. Save DebugView and concise observations under
   `.research-output/r-cooker3/oracle-t2-t3/results/`, with a screenshot/video
   only if it helps explain the result.

## Classification

Report collision and damage independently:

- If both behave normally and the game remains stable, classify this
  `NATIVE_RETAIL_REBUILD USABLE IN THIS RUNTIME CASE — CONFIRMED_BY_RUNTIME`.
  The 36-byte secondary descriptor semantics remain unresolved; the native
  retail writer supplied them.
- If collision behaves normally but damage does not, confirm only collision
  usability and leave damage unconfirmed. Note that physics/damage setup may
  be profile-specific.
- If collision fails or is grossly offset, report the concrete observation
  and preserve the secondary-descriptor question as unresolved. Do not
  immediately assign causality to those bytes.

This one vehicle runtime result does not establish a general offline tag101
serializer or universal damage behavior.
