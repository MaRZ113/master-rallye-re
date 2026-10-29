# Dakar 2 resource and decoder evidence

Scope: exact Xbox revision in DAKAR2_PLATFORM_AUDIT.md. Generic RBB/SBB indexing is additionally tested against all three platforms. Xbox XMD/HIR/XTX payload assumptions are never applied to GC or PS2.

## Containers and native references

ALL.RBB is a custom engine resource block, signature `00 52 42 42`. ALL.SBB is a named-member table with embedded blocks; neither is an ordinary XPR/DDS/model archive. Xbox/PS2 words are little endian; GC words big endian, while resource type bytes remain literal ASCII. Catalog members include PAJERO_HI, PAJEVO_HI, NISSAN_HI, HINO_HI, tuple variants and BURNT resources. Full tuple/LOD/damage/equipment selection semantics remain unresolved.

RBB header: declared bytes +4, XOR of first two words +8, metadata XOR +12, block count +0x18, counts +0x1c/+0x20. One-block descriptor +0x24: flags, data offset, data size, relative-area size, resource/external/other/internal counts and data XOR. Directory +0x48 has 12-byte records: literal type, cache word, encoded reference. Qualified original references have low bits 1; resource offset is `reference & ~3`. External fields contain resource indexes; internal fields contain signed offsets relative to the field address. Only fields named by original relocation tables are interpreted. Original buffers are never patched in place.

SBB count +0, 52-byte entries from +16: name[32], offset, allocated bytes, key, declared bytes. Some declared lengths exceed allocation: Xbox 14, GC 3, PS2 12 entries. Reader records WARN and bounds each member to the smaller length. It never borrows bytes from the following member or silently repairs the source.

Build-specific Xbox static evidence, original virtual addresses:

| Address | Observation / independent check |
|---|---|
| 0x82020 | Word XOR reproduced against original container bytes |
| 0x82150 | RBB magic/header XOR |
| 0x821e0 / 0x82040 | Resource references and external/self-relative fixups |
| 0x8e360 | Named SBB 52-byte entries, RBB/SBB out-of-sync diagnostic |
| 0x8ac20 | XTX allocation/registration and native texture format fields |
| 0x8b4b0 / 0x8b270 | XMD declaration lookup, original 16 stream slots |
| 0x8b590 | Stream/texture binding and original index draw |
| 0xe5e30 | NV2A BEGIN_END primitive 6 and original 16-bit index submission |
| 0x8b360 | Blend dispatch; mode 3 SRC_ALPHA / ONE_MINUS_SRC_ALPHA |

XBE base 0x10000, retail decoded entry 0x7c452. Private mapped section image SHA256 `3bb24f84f505da020a92581a53a0079a7b47791330479f6fb300e6ab10c3d7b5`. Original section bytes/address maps underpin the evidence; inferred function boundaries/decompiler output are not original source. Private exports remain in ignored `vehicles_scratch/dakar2/`.

## Qualified Xbox subset

XMD starts float bits 0x4001eb85 (2.03), original flags, triangle/vertex counts, submesh count and relative array. Submesh records preserve index/vertex counts, primitive 6, texture references, declaration and stream slots. Supported declarations: 8, 13, 0x51a08, 0x51a13. Native table begins 0x1940b8 (20-byte records); attributes at 0x193bb8 corroborate:

- stream 0 float3 position, stride 12;
- stream 2 signed packed 11/11/10 normals; original words retained;
- stream 3 BGRA color bytes retained;
- stream 9 float2 UV0; optional stream 10 float2 UV1 retained;
- original 16-bit triangle strips; degenerate steps still affect parity. Derived totals must match original model triangle/vertex counts.

Neutral preview uses UV0/texture stage 0, not the complete multitexture shader. Materials retain model/submesh flags, declaration, selected original texture references and exact resource/stream hashes. Native table gives blend mode 0 for 8/51a08 and mode 3 for 13/51a13. This qualifies blend state, not the assumption that texture-0 alpha equals original final shader alpha.

XTX supports observed BC1 format 0x0c and BC3 0x0f, rectangular power-of-two dimensions 4..2048, 1..12 mips. All original compressed mip samples remain unchanged; decoded top-level RGBA is separate. Decode does not qualify reflections, shader alpha or lighting; other formats fail explicitly.

HIR: header 0x20, bone stride 0xd4; original local 3x3 basis/translation +8, parent/sibling/child +0x38, relative name +0x60. Only identity rest bases are qualified. Original translations/hierarchy are retained; normalization mirrors Z, with winding/normal conversion handled by existing UVS preview staging. Units are original unscaled values, not certified meters or settled suspension.

PAJERO: VEH 6 → HIR 48, `PAJERO_HI_0_0.LOD`, PAJ_ nodes. HINO: VEH 18 → HIR 72, `HINO_HI_0_0.LOD`. LOD root pairs start +8; mesh references +12+8*i resolve against that member's table. Original body/wheel/crew/attachment names and resources survive. All retained rest nodes are inspected; runtime visibility/equipment and pose remain unknown.

NISSAN: VEH 9 → HIR 54 is source-confirmed Nissan Pickup; D22 identity is not independently established by decoded metadata. `MID_R_EXHAUST` basis `[1,0,0,0,0,-1,0,1,0]` is nonidentity. Recovery fails closed pending original rotation-convention evidence. Hino supplies the successful independent truck test; Nissan is not forced through guessed transforms.

## Unresolved rendering gates

L1 structural recovery passes; **L2 remains WARN**. CW/CCW show complementary missing/striped surfaces. No-cull diagnostics show recognizable complete assemblies, but native culling and mixed-facing semantics remain unresolved. Original indices are retained, not flipped using normal heuristics. No global two-sided material repair is applied. `views-none` is explicitly diagnostic, never source-renderer parity.

Pajero's alpha preview exposes pale inner wheel/overlay surfaces. Vertex colors, UV1, secondary textures and original shader output alpha are retained but not fully reproduced. Glass/headlight coverage is approximate. Hino looks more complete in the diagnostic, which does not independently prove culling. Animation, dynamic wheels, lighting, reflections, active variants/LODs, gravity-settled pose and original runtime visuals remain NOT TESTED. These unknowns do not authorize MR conversion.

## Bounds and failure policy

Read spans max 256 MiB; filesystem depth/count/aggregate directory bytes bounded. RVZ SHA1 headers, range overlap, decompression window/output checked; no full-disc unbounded decompression. Only observed GC/Zstandard layout supported. RBB single-block/count/relocation/XOR/payload ranges checked; SBB overlap/path traversal rejected. XMD limits: 65536 vertices/submesh, 1M vertices and 3M indices/model before unpack. Nonfinite coordinates, unknown bases/declarations and invalid references fail closed. Existing UVS validates immutable snapshots, serialization, texture/output budgets and fresh contained output. Adapter has no MR authoring, CarID, physics or roster dependency.
