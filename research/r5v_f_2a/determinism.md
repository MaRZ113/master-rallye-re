# R5V-F.2a determinism

## Cook A/B result

**NOT RUN.** There are no retail-cooked `complete.dx`, `car.dx`, `wheel.dx`, or
DXT outputs in the working tree. Consequently, Cook A/B hashes, output equality,
timestamp analysis, and reproducibility classification are all **UNKNOWN**.

The retail code has independent DX and DXT cache tests. Both use a `0x14`
metric tolerance, but the metric's semantics are not established. A valid
pre-existing output could therefore bypass the native source cook. Any future
determinism experiment must begin with a clean, isolated target cache and
capture evidence that each role reached the source path before hashing.

## Separate source consistency observation

The selected package's 25 existing DXT companions matched the prior offline
GXI→DXT encoder byte-for-byte. This means the source's GXI/DXT pairs are
internally consistent under that encoder. It is not a Cook A/B result and does
not prove byte identity with retail's `0x00558B30` texture cache writer.

## Required next record

For both clean runs, record source manifest SHA, retail executable/archive
hashes, the exact isolated path mapping, debug messages, all output sizes and
SHA-256 hashes, and whether the cache was absent or rejected. If bytes differ,
classify the difference at field/region level and prove any timestamp-only
change before calling it nonsemantic.
