# Dakar 2 platform audit — 29 October 2026

Baseline: `75c9138ca4b28e5af982534c0d131f5bcb25c5ce`, initially clean `research/vehicles`. Scope is source qualification only. Master Plan v7.3 is retained in full, together with the previous repository implementation checkpoint. Historical future plans are context, not authorization for additional imports.

## Platform selection

| Owner-local source | Verified identity / discovery | Technical readiness |
|---|---|---|
| Xbox USA ISO | XDVDFS, 456 files; XBE Dakar 2, title ID 41430017, region mask 1, certificate version 2 | Selected: original x86 loader and D3D8 declarations traced; Pajero and Hino L1 recovery succeeds. L2 WARN |
| GameCube USA multilingual RVZ | GPDE51 revision 0; RVZ1/Zstandard; FST 358 files and original DOL | Container metadata recovered. Big-endian GX geometry/display-list/shader decoding NOT TESTED |
| PS2 extracted directory | SLES_508.79; SYSTEM.CNF VER 1.02 / PAL; 388 files, 2313882518 bytes | Container metadata and EE entry verified. VU/VIF/GS model pipeline UNSUPPORTED by this decoder. Original disc ISO MISSING INPUT |

Personal/historical priority remains separate from readiness: Mitsubishi Pajero first, independent source-confirmed truck second. The provisional Xbox > GameCube > PS2 convenience ranking was tested against actual resources. Xbox wins because its loader supplies checkable stream formats, references and native draw evidence. Neither archive access nor a familiar CPU alone proves a vehicle decoder.

## Exact source boundary

Sources remain read-only under `E:/RallyWorkshop_Sources/sources/{Dakar 2 Xbox,Dakar 2 GameCube,Dakar 2 PS2}`. Source arguments are configurable; no installation duplication is required. The decoder pins executable/container hashes, not folder names. Full per-file/member sizes, hashes, offsets and first-32-byte signatures are in [DAKAR2_CORPUS_MANIFEST.json](DAKAR2_CORPUS_MANIFEST.json).

| Source | Bytes | SHA256 |
|---|---:|---|
| Xbox / Dakar 2 - The World's Ultimate Rally (USA).iso | 7825162240 | f57211cdf11cab202c184591e4fb3730b2665119fcc213bc46a2f670c0cc5093 |
| Xbox default.xbe | 1650688 | 715db4e407b38c0a6d14ea0ee9d08ebc524b9ece92ceeaa70b5fb81a5ec32378 |
| Xbox ALL.RBB | 204040 | c82744f12b8322a2bde93d19bc270f6e365523d22c38235b12253fb7673b889a |
| Xbox ALL.SBB | 55214080 | df98579418da0ed2b0b0bc79a7c6e1558a7b356c84abbbbe086a19cb3a2d62e9 |
| GameCube / Dakar 2 - The World's Ultimate Rally (USA) (En,Fr,De,Es,It).rvz | 947815584 | ad9db1374df7a87ef4d0adff16fb2e58b02c0816abc97a8312700e0042004190 |
| GameCube main.dol | 1409856 | f724f2d46b6add117f6205b9133ac6d45bc56a5d04af276dedde49586a9acd64 |
| GameCube ALL.RBB | 425504 | c6b693d6f728841b6e290c6e57ee5e2ba46edf1696fc6ddc4f931d16a698dfdc |
| GameCube ALL.SBB | 43563008 | 7b95f9cd09ada0468b9fa12fe5dcb34616c2275248fabc1f1ef4347f02562816 |
| PS2 SLES_508.79 | 1540368 | 28a8c98d095147878e4f36c60546c5010f5db704b607c557a2b5ac50f4dbd16b |
| PS2 ALL.RBB | 232096 | 687e8eb641bb994196975194f33bb9fe1277779accfcd9cfec0ead99a093bbc0 |
| PS2 ALL.SBB | 103088128 | 23ae4be1e8bbb497821973d5598f6bb64ced78c7de6b0302b54830fc5a1fa393 |

Xbox partition base 0x18300000; descriptor at 0x18310000 contains both MICROSOFT*XBOX*MEDIA signatures. GameCube logical size 1459978240, disc magic C2339F3D; RVZ chunks 0x20000, 11139 groups, compression type 5. PS2 extracted files do not establish original disc sectors or a whole-image hash.

All three ALL.RBB indexes contain 76 resources: 36 VEH, 18 HIR, 18 VPD and one each VSR/XMD/XTX/SHK. ALL.SBB has 244 named entries per platform. This shared catalog does not establish byte-identical model payloads: Xbox, GC and PS2 payload layouts differ.

## Tool and executable evidence

- Existing UVS v1, D3D9 previewer and Source Garage reopening are reused. New bounded readers are original project code. No third-party implementation is vendored; no untrusted legacy exporter binaries were run.
- REA was checked first. Its available Windows provider rejects XBE and raw x86; installed Ghidra 12.1.4 headless was used instead. Original XBE sections were mapped explicitly at original VAs into a private analysis image, not converted into a purported original PE. Ghidra pseudocode is static interpretation, not original source. Ghidra is Apache-2.0.
- XBE certificate and nine library records identify XDK 1.0.5344, including D3D8, D3DX8 and XGRAPHC. The format report lists actual native resource-loading/buffer addresses.
- GC DOL entry 0x80003100 and original sections were inspected as PowerPC big endian. PS2 ELF entry 0x100008 was inspected directly using installed Emotion Engine Reloaded `r5900:LE:32:default`. Scratch-only Rabbitizer 1.16.2 (MIT) independently checked the first 20 original R5900 words, including SQ and branch 0x10002c → 0x100018.
- Original GC/PS2 path strings were observed, but full loading functions and GX/VU/VIF/GS rendering paths remain untraced. Entry-point analysis is not model support. No original-game/emulator rendering was tested.
- Python 3.15.0, stdlib Zstandard 1.5.7 and existing Pillow 13.0.0 were used. RVZ audit optionally requires Python 3.14+ `compression.zstd`; Xbox recovery does not depend on RVZ. Existing Pillow BCN API is reused, without copying implementation code.

Primary research leads: [Dolphin RVZ specification](https://github.com/dolphin-emu/dolphin/blob/master/docs/WiaAndRvz.md), [xemu disc handling](https://xemu.app/docs/disc-images/), [XboxDev XBE loader](https://github.com/XboxDev/ghidra-xbe), [xemu texture handling](https://github.com/xemu-project/xemu/blob/master/hw/xbox/nv2a/pgraph/vk/texture.c), [NV2A registers](https://github.com/xemu-project/xemu/blob/master/hw/xbox/nv2a/nv2a_regs.h), [Rabbitizer](https://github.com/Decompollaborate/rabbitizer). Dolphin/xemu GPL code was consulted as documentation, not copied or redistributed. No verified ready-made Dakar 2 vehicle exporter was found in the bounded search; this is not a claim that none exists.

The [GBA.SBB research post](https://gbatemp.net/threads/question-about-the-sbb-file-format-in-dakar-2-used-by-acclaim.459181/) concerns a GameCube GBA resource, not a demonstrated vehicle importer. Its 13 BIN entries were found locally; that does not qualify GX reconstruction. The different historical thread URL remains preserved in the attachment.

## Stop boundary

No MR CarID, addon, roster edit, native compilation or physics tuning. Silver #271 owner launch and stiff suspension are a separate reversible Physics Studio follow-up; launch does not prove race completion, Results, damage or re-entry. No push/publication.

## v7.4 follow-up

The original L1 results above remain historical and immutable. New derived source-state previews, native matrix/cull/depth/pass evidence and qualified Nissan rigid-basis recovery are documented in [DAKAR2_RENDERER_RESULTS.md](DAKAR2_RENDERER_RESULTS.md). [DAKAR2_LOST_VEHICLE_COMPARISON.md](DAKAR2_LOST_VEHICLE_COMPARISON.md) adds measured PC RED/Silver versus Xbox comparisons. L2 still WARN; GC/PS2 boundaries and no-native-import scope remain.
