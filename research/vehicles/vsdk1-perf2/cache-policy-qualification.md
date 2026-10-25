# Read-only qualification: native texture-cache byte policy

2026-10-24. No cache-policy patch has been implemented or applied to c-fast.

## Source evidence

For exact retail SHA256
`bf8aef32407eb6552c05045b8abef149f32983cedd9503b865069b444c5f96b4`:

- `0053CDF0` constructs the texture manager. Instruction `0053CE94`, original
  bytes `C7 47 38 00 00 00 02`, writes `[EDI+38h] = 0x02000000` (32 MiB).
  The four-byte immediate starts at `0053CE97`.
- The same constructor independently allocates small manager/map nodes and a
  12000-byte initial handle vector. It does **not** allocate a contiguous
  32 MiB pool or derive that vector's capacity from `+38h`.
- Texture-manager loading `0053D2F0` adds source width×height×4 to `+30h`.
  It reads `+38h` at `0053D4D1` and `0053D5C2`. Unsigned comparisons drive the
  LRU eviction loop; `0053D5C7` is `JA 0053D4E1` when current charge exceeds
  the threshold. These reads do not index an array or set a texture dimension.
- GPU textures are allocated individually through the existing CreateTexture
  path. Their format, quality, mips and device capabilities are separate.

REA/Ghidra constructor and loader output plus independently decoded original
instructions support treating `+38h` as a source-pixel residency **policy** in
the observed path, rather than the size of an allocator slab or fixed array.
The scan of the texture-manager implementation found the constructor store
and these two budget reads. It is not a proof that every possible indirect
consumer throughout the executable has been typed and excluded.

## Bounded profile possibility

A future opt-in collection policy could admit only:

| Policy | Bytes | Constructor immediate |
| --- | ---: | --- |
| Native default | 33554432 | `00 00 00 02` |
| 48 MiB | 50331648 | `00 00 00 03` |
| 64 MiB | 67108864 | `00 00 00 04` |

All are far below signed 32-bit overflow and preserve the original unsigned
comparison semantics. A reviewed implementation would change only the exact
constructor immediate in the external suspended-process plan, pin the complete
instruction/source hash, reject an already changed preimage and keep the
default at 32. It should be collection-level, since the native manager is shared;
per-car budgets would misrepresent ownership.

Structurally this does not require resizing registration tables, CarID arrays,
model buffers or GPU-capability structures. It must not be advertised as a
larger supported engine roster, a driver-memory setting or a guaranteed total
process-memory ceiling.

## Required runtime qualification before a default change

1. Keep 32/48/64 variants separate and hold textures, UI, physics and audio fixed.
2. Verify the live manager value and LRU counters; compare the same cold/warm/
   re-entry and mixed AI/race sequences with identical graphics options.
3. Measure process private bytes/address-space pressure, device/reset behavior
   and repeated race/frontend lifetimes. Additional accounting allowance can
   retain more CPU image data and managed GPU/driver copies; actual RAM/VRAM
   growth is not simply the threshold difference.
4. Preserve all original eviction/destruction and failure paths. Do not retain
   leaked COM objects or bypass release to make a cache appear persistent.
5. Keep authoring bounds for oversized/malformed texture sets. The original
   loop stops at the just-loaded texture, so one oversized texture can exceed
   the nominal budget; the threshold is not a strict peak-memory guarantee.

The current live captures establish LRU releases during Lancer re-entry, making
bounded policy qualification relevant to full-resolution multi-addon working
sets. Bulk pixel I/O is a separate already justified optimization and remains
independent. A larger threshold has no measured benefit or gameplay qualification
yet, and this read-only note does not authorize silently changing current builds.
