# Bounded PS2 ELF UI evidence

Canonical SLES_509.06 SHA256:
`b15a80c516986bfd7f9fcfcfa2ec5fbf37643778c6363dde460006d7001a78f2`.
Addresses are virtual addresses in this ELF. Names below describe analysis
roles; they are not recovered original C++ symbols.

Analysis used the installed ghidra-ai-bridge exporter with the newest installed
Ghidra **12.1.4** at
`D:\Game\Master Rallye\_reverse-tools\ghidra-bridge-main\ghidra_12.1.4_PUBLIC`.
The existing ignored `PS2PackFS_MIPS3` project was opened read-only. Temporary
function discovery and R5900 LQ/SQ→LD/SD low-64-bit stack surrogates were rolled
back. Original words and surrogate locations are retained locally. No original
ELF or saved database was patched. Language is MIPS LE 64 / 32-bit addresses,
o32; PS2 extra argument registers and packed operations limit decompilation.
Conclusions use scalar reads, comparisons, strides and bytes, not GS/MMI
semantics. Some decompilation shows truncation or unimplemented instructions;
no conclusion depends on those truncated tails.

| Address | Role and concrete support | Grade |
| --- | --- | --- |
| 0x00380A08 | Builds image-bank path with `.psb` at 0x00486E60; calls bank loader; caches coordinate width/height | CONFIRMED_BY_ELF |
| 0x00380998 | Bank-load wrapper, calls 0x00386D28; explicit load-failure diagnostic | CONFIRMED_BY_ELF |
| 0x00386D28 | Opens resource, checks F001 and 0x7D, constructs bank and invokes the two section readers | CONFIRMED_BY_BOTH |
| 0x00387188 | Mapping count then two 32-bit reads per key/index; stores low u16 key/index in bank lookup | CONFIRMED_BY_BOTH |
| 0x00387258 | Image count, constructs each image via 0x003852E0 and calls 0x00387328 | CONFIRMED_BY_BOTH |
| 0x00387328 | Per-image triangle count, invokes record reader; in-memory stride 0x48 | CONFIRMED_BY_BOTH |
| 0x00387478 | Six float reads, ten integer reads, name length/read; `Null` comparison at 0x00487118; texture-handle creation | CONFIRMED_BY_BOTH |
| 0x002FD7D0 | Texture resource path suffix `.gxi` at 0x004846A0; delegates loading to 0x002F84F0 | CONFIRMED_BY_ELF |
| 0x003852E0 | Zero-initializes 12-byte image-vector object | CONFIRMED_BY_ELF |
| 0x003853D8 / 0x00385458 | Width/height from vertex X/Y min/max, triangle stride 0x48 | CONFIRMED_BY_BOTH |

HUD-owner families were bounded to necessary constructors/configuration:

| Address | Owner/candidate | Evidence and boundary |
| --- | --- | --- |
| 0x0014B040 | gaHudAiSpeedDial constructor | Name at 0x0044C2F0; vtable 0x0044C900 |
| 0x0014B290 | Dial configuration | Reads `Hud No`, gear/speed/needle offsets, direction, angle limits and maximum revs; delegates 0x0014B388 |
| 0x0014B580 | gaHudAiSpeedNeedle constructor | Name at 0x0044C3F0; vtable 0x0044C8C0 |
| 0x0014B6C8 | Needle initialization | Queries HUD owner state via 0x001931C0 / 0x00193220 / 0x00193280 / 0x001932E0; writes entity transform; reads vehicle output |
| 0x00146118 | gaHudAiMap constructor | Name at 0x0044BF40; vtable 0x0044CB00; confirms owner family, not course geometry |
| 0x00148804 | Pace-note owner registration site | Name reference at 0x0044C040; candidate family around constructor 0x00148800 |
| 0x0014DE74 | Rank family resource clue | References `HUD/newhud` at 0x0044C510; raw constant-construction xref, not proof of every consumer |
| 0x0014DB88 | gaHudLoader constructor candidate | Name reference at 0x0044C4F0; not decompiled for scene-selection semantics |

Map vtable candidates: configuration `0x00146960`, initialization `0x00147038`,
update `0x001461F8`; meanings beyond the generic AI slots are **STATIC_INFERENCE**.
GPS family names and separate map/GPS entities exist, but no dynamic map path is
claimed recovered. These are bounded UI2 leads, not permission to reverse all
rendering. Exact MAP128STRIPED name was not found in the scanned ELF ASCII
strings; constructed/non-string references remain possible.

Raw local exports/logs are under ignored `data/ui1/elf/`; source deliverables
are this address/field map and `tools/elf_ui_query.py`. A low-half 0x3039 match
in a time/random helper was rejected as a GXI-loader clue; a matching immediate
alone does not identify a format owner. RGBA is established by bytes/visual
reconstruction, not by that rejected ELF candidate.
