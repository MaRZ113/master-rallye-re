# R-GFX2 findings and acceptance state

**READY FOR HUMAN RUNTIME — NOT CONFIRMED_BY_RUNTIME.** The native proxy source,
complete ABI, bounded observational trace, tools, mock tests and Win32 build are
available. Human stock-parity and game capture evidence remain required.

Starting branch: modernization/renderer-recon. Starting HEAD:
`0caf0a21c5e1a9a72cb11c3e6a83991ece003e56`. New branch:
`modernization/d3d8-proxy`. [starting-git.json](data/starting-git.json) records the
initial older checkout and clean restoration of the committed R-GFX1 state.

The available pristine MRallye.exe was rehashed before target-specific analysis:
SHA256 `bf8aef32407eb6552c05045b8abef149f32983cedd9503b865069b444c5f96b4`,
size3121214, MachineI386, ImageBase0x00400000, timestamp1006791005,
entry VA0x005C4602 / RVA0x001C4602. Section/import identity is preserved in
[target-build.json](data/target-build.json). No game binary is included or altered.

| Result | Evidence grade / limit |
|---|---|
| Local proxy source forwards to explicit native system path | SOURCE_REVIEWED; loader-in-game provenance pending |
| 16/97 slots, x86 stdcall COM ABI, struct size guards | HEADER_VERIFIED + BUILD_VERIFIED; mock vtable invocation tests |
| Stable known-IID identity, native result/refcount return, parent hold | SYNTHETIC_TESTED; target runtime still pending |
| Raw children retained after mapped-flow audit | STATIC_INFERENCE / SAFE_TO_KEEP_RAW; not exhaustive dynamic proof |
| All graphics arguments unchanged; no added native getters/draws | SOURCE_REVIEWED + 105 ordinary slot forwarding tests |
| F10 next complete interval, hard overflow, Reset invalidation | SYNTHETIC_TESTED; game key/Reset behavior pending |
| Valid bounded JSONL, exact matrices, unknown states, caller module/RVA | SYNTHETIC_TESTED with native-generated JSONL |
| Exact-build offline owner joins | SYNTHETIC_TESTED; unknown hash/module/method fails closed |
| Stock lighting/fog/shadow/camera/material behavior | UNOBSERVED_RUNTIME in R-GFX2; R-GFX1 remains static input |
| Visual parity, all-call coverage, overhead, device loss | PENDING_HUMAN |

The compiled DLL imports bcrypt, USER32 and KERNEL32 only. The required factory
and validator exports are present at the inspected native ordinals5/3/2. /MT
avoids a redistributable CRT DLL. Current DLL hash/size are in proxy-build.json;
the build itself is intentionally ignored and not committed.

Normal logs capture provenance/create/reset/resource metadata and periodic counts.
F10 writes one complete Present-to-Present interval. State storage has no presumed
defaults and never queries or changes native state on its own. The engine's cache
constraint is documented as an architectural requirement for later changes.
Resource identity remains last-known metadata because raw Release is unobserved.

Offline classification is deliberately narrow. Mapped particle, stock-shadow,
packet UI/video and debug owners can be suggested; the two common mesh tails stay
UNKNOWN for vehicle/terrain/road/sky identity. Static-owner matching alone is not
semantic runtime confirmation. No new conclusion corrects or edits R-GFX1.

Important remaining limitations: actual native path/SDK/device parameters must be
observed in-game; raw-child or unexpected extension-interface escape could omit
calls; state blocks are conservatively invalidated; a short F10 tap can be missed;
one explicit large capture can hitch. Wine/Proton/overlays/chained proxies and old
Windows versions are unvalidated. These are handoff checks, not hidden parity passes.

All deliverables belong to this directory. No existing reverse research, Ghidra
database, installed game DLL slot, EXE, asset or runtime render state is modified.
No push and no R-GFX3 implementation are part of this phase.
