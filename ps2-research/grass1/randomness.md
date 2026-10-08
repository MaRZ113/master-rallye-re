# Random table and repeatability

`3b7880` is random-table initialization, **not** an image loader. Owner
construction calls it. When guard `42fe78` is zero, original instructions
`3b78c8/3b78cc` invoke `srand(0x30ff)` through `3f96e8`. The fixed seed is
executable evidence, not a preview choice or course-name hash.

`3f96e8` stores seed in the libc impure structure `+0x58`, reached through
global `4404dc`. `3f96f8` uses original EE instruction `00641818` at `3f9714`:
low32 state is `state*0x41c64e6d + 0x3039`; return is `state & 0x7fffffff`.
Stored state remains unmasked. Original words, not Ghidra's MULT surrogate,
establish this recurrence.

Initialization order:

1. Fill 1024 uniform floats at `4a8810`, one rand each, scaled by `2^-31`.
2. Fill 1024 **unnormalized** jitter Vec3s at `42fe88`, stride 12. Each candidate
   draws three numbers, computes `float(rand)*2^-30 - 1`, and rejects until
   `sqrt(x²+y²+z²) <= 1`. It samples a unit ball, not three independent final
   uniform offsets and not unit directions.
3. Fill a later normalized direction table at `432e88`. The placement hash
   reads the jitter table, not this direction table.

The diagnostic reproduces steps 1–2 in float32: **6,970 RNG calls** through
jitter, state **1,125,623,325** immediately after it. This is not the terminal
state of the entire original initializer, because step 3 is deliberately not
included. A different explicit diagnostic seed is supported at Python API
level and remains synthetic; canonical CLI uses the recovered seed.

Placement does not call rand. It indexes the fixed table with world XZ and
`CVT.W.S`, so equal lattice coordinates/rounding/table yield equal horizontal
jitter. It does not give random per-instance yaw, scale, tint or image in the
traced CPU path. The libc RNG is shared; reseeding may affect other systems,
but those consumers are not reversed here.

The table guard writer/reset lifetime is unknown. The owner call and zero-guard
seeded path are proved, not every possible first-initialization history.
Full population also depends on source order, clipping, region history and
live FCSR rounding. Stable jitter is therefore separated from an unproved
claim of identical full populations after every load/visit.

The diagnostic uses explicit nearest-even hash conversion by default, labeled
`EXPLICIT_DIAGNOSTIC_INPUT`, and exposes floor/ceil/truncate controls. It does
not infer the live FCSR from a screenshot. IEEE float32 and PS2 FPU/VU precision
are separately classified in [offline validation](offline-validation.md).
