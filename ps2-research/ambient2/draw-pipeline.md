# Bird world sprite draw, GS state and visibility

The bird uses the engine's ordinary en2d world-sprite path. Fresh canonical queries verified its concrete dispatch and cache construction instead of reusing HUD/water attribution by name. Existing PackFS/PSB/GXI parsing and shared DMA/VU infrastructure are reused.

```text
bird entity+4c en2d
  --21ea20 interface+4c, concrete vtable485a34--> 3301c8
  --mode0--> renderer ordinary en2d vector+14
  --3302b8 drain--> 337a98 world PSB consumer
  --bank/key, camera basis, paired source triangles--> 48-byte CPU vertices
  --362138 virtual5c/74--> 31f0a8 wrapper / 3201b0 cached packet producer
  --3376c0 mode8 / primary texture311c50--> state + cached geometry
  --317120 /31e010--> DMA CALL
  --316ce0 /316b88 /30ea80--> VIF1 DMA
```

These CPU arrows are CONFIRMED_BY_EXE; the Burdy source records add CONFIRMED_BY_BOTH. The en3d carrier is also queued by the generic entity dispatcher, but no bird PSM model is assigned in this allocator. Its queue membership is not another visible bird mesh.

`337a98` converts paired72-byte runtime PSB triangle records into four CPU vertices per pair. It steps source pointer by0x48 twice, first at`3381b0/1b4`, then`3386fc/338704`. Local X is `-0.5+signedX`; local Y is `0.5-signedY`. UVs and texture atlas rectangle come from original bank records. World translation and camera-facing basis are retained as described in the orientation document. Source/frame selection is independent of flight motion.

Cache allocator`31f0a8` creates a0x40 wrapper with vtable4854f0. Builder`3201b0` converts48-byte CPU vertices into64-byte VU records, four qwords each: control(count|0x8000,1,0,0), float RGBA packed channels×0.5, UV, XYZ/W=1. It batches at most32 vertices, stepping quads byfour. Original producer calls`31de48`, `31d7c8`, `31dce8`, `31ddd8` establish REF/UNPACK/MSCAL0xf and cache packet finalization. The generic MIPS decompiler stops on a later unsupported EE instruction; no conclusion depends on that tail. Position-only/full cache refresh helpers are`31ef10/31ed50`.

`3376c0` world branch selects materialmode8; HUD branch mode7 is separate. Common `312610` prolog resets selector42de60=0 before its mode8 case; selector is not guessed from an inherited previous draw. Primary texture bind is concrete virtual+c4→`311c50`; atlas CLAMP derives from cache+44/+48/+4c/+50. A secondary default texture binding does not prove a second reflection/environment pass.

| State | Original mode8 write / proof boundary |
|---|---|
| GIF/PRIM | Maskffc07fffffffffff, OR003e000000000000: triangle strip4, IIP1,TME1,FGE1,ABE1; other bits including FST/context inherited |
| TEX0 | Maskffffffe3ffffffff, OR0000000400000000: TCC1,TFX0 MODULATE; texture descriptor supplies VRAM fields |
| ALPHA | Maskffffff00ffffff00, OR44: A0,B1,C0,D1,FIX0; `(Cs-Cd)*As/128+Cd` |
| TEST | Maskfffffffffff9c000, OR41000: ATE0,ZTST2 GEQUAL; ZTE/DATE/DATM inherited; AFAIL1 irrelevant while ATE0 |
| ZBUF | Set bit32: ZMSK1, depth writes masked; buffer address/format inherited |
| TEX1 | Template maskfffff000ffe7fe1e, OR61; texture binding can overwrite filter/mip bits |
| CLAMP | Atlas region clamp WMS2/WMT2, rectangle min/max; high bits preserved |
| FBA | Register4a FBA_1 bit0clear; this is **not PABE** |
| FRAME/TEXA | No captured final words; inherited/unresolved |

The exact known-bit accounting is executable-derived in `bird-render-contract.json.GS`. Stored binary texture alpha is separate from TCC/TFX, vertex alpha, alpha test and ALPHA's blend selector. ATE is disabled; it is inaccurate to call this an alpha-tested bird merely because the atlas has cutout-shaped pixels. Final As/pixel output is not reconstructed from atlas alpha alone. Vertex-color preparation in`337a98` and the packet channel×0.5 are separate operations. Live fog, framebuffer masks, TEXA, descriptor/CLUT and texture residency need capture.

## VU proof boundary

Canonical initialization`311370` calls upload producer`317208`, which DMA-CALLs embedded chain442170. Its five MPG **commands** are44217c/442984/44318c/443994/44419c; instruction bytes start four bytes later. Counts256/256/256/256/201 target microPC0/100/200/300/400. Fresh hashes match the independently frozen WATER/TREE upload chunks; `upload-evidence.json` separates command addresses and payload addresses.

CPU geometry packet entry is micro0xf and selector0. The embedded ordinary path reads position/color/UV/control, applies world/view/projection and perspective Q, FTOI0 color/FTOI4 position, ADC/clipping, GIF output. Regular XGKICK is micro0xfa, ELF442950; shared clipping/flush includes micro3d7. Short original pairs are in `instruction-probes.json`; matching embedded operations are not a selected live packet capture.

```text
CPU REF/UNPACK + MSCAL0xf / selector0
  --confirmed upload producer + matching embedded input contract--> ordinary VU program
  --embedded transformation/GIF/XGKICK--> documented GS primitive/state contract
  UNKNOWN LINK: selected live VU micro-RAM/packet/frame and final inherited GS words
```

Status: EMBEDDED_PROGRAM_CONFIRMED, UPLOAD_PRODUCER_CONFIRMED, PACKET_CONTRACT_CONFIRMED, VU_ENTRY_CONFIRMED, OUTPUT_PACKET_CONFIRMED at static-program level; LIVE_RESIDENCY_UNKNOWN, LIVE_FRAME_NOT_CAPTURED. The CPU submission path is proved independently of that live boundary.

## Culling and activation

Specific recovered gates are both marker pointers, free pool, nonempty FlightList, probabilistic clock/count, strict spawn annulus and flying retirement beyond MaxFlyDist. Distances are horizontal relative to registry positions, not demonstrated camera range. Generic world rendering additionally checks en2d visibility flags/commands and uses ordinary camera/VU clipping.

No FlyBird-specific frustum, LOD, wind, weather, obstacle avoidance, altitude cap or terrain query appears in the traced controller/manager/draw path. This does not remove inherited scene/camera clipping or prove negative behavior elsewhere. The sprite queue drain follows its local model queue; no whole-frame ordering guarantee is claimed. Scene priority, existence, allocation, active queue membership, submission and visible count remain separate.
