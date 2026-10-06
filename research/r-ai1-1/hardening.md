# R-AI1.1 research hardening — 2026-10-04

Status: **HARDENED RESEARCH RUNTIME BASE — CONFIRMED_BY_RUNTIME** in the exact
composed randomized image below. Loading failure neutralization, NULL StringList
Dump continuation/survival, Restart and Replay passed human validation.
[Final closeout](runtime-closeout.md) records repeated fresh variation. Base-only
EXE was not separately launched; the specific NULL-XmlData trigger remains
static/emulation evidence. No capacity or public release work began.

Starting main checkout: branch `research/r-ai1-1`, HEAD `24ac105`, clean tracked
tree. Work continues on the user-approved `research/r-ai1-1-hardening` branch.
Existing untracked Ghidra project/ZIPs are preserved. Latest Ghidra12.1.4 and
installed ghidra-bridge export read-only pristine analysis; temporary emulator
transactions roll back without saving the project.

## Research profiles

Both deterministic builders start from the same **exact pristine** size/hash;
neither accepts an arbitrary already-patched executable.

| Profile | SHA256 | Ranges / size |
|---|---|---|
| pristine source | `bf8aef32407eb6552c05045b8abef149f32983cedd9503b865069b444c5f96b4` | 3,121,214 bytes |
| retail-rbase-hardened | `bbb9f0a8bb2523adf125582d16512c25f9b51db7a4104ee5edf8f7251865ae00` | 6 / 3,121,214 bytes |
| retail-r-ai1-1-hardened | `603f0c06ca2a502367baa7e49fcaeab9e2ab9a7d6c47dd46ed82ca27cb9840a1` | 10 / 3,121,214 bytes |

Base modifies only Loading failure redirect, StringList NULL guard, XmlData
nullable-getter guard and declared `.text` size. The composed profile adds the
existing355-byte MIXED code and its three existing hooks **byte-identically**.
It does not change the chooser design, Car0, NumCars, native driver bookkeeping,
capacity or registry. Guards/policy remain firstAI1, AIcount3, RaceType2.

One audited overlap is explicitly merged: `.text` VirtualSize file0x218,
original0x28D294, base0x28D2DC, composed0x28D463. The merge takes the maximum
declared end. Every other overlapping range is rejected. No image/raw size,
page count or allocation change. Inverse verification restores pristine exactly
and rejects any unapproved byte anywhere in the image.

[Manifest](patch-manifest.json) records VA/RVA/file offsets, original/replacement
bytes, purposes, caves and continuations for both profiles. The tracked manifest
now carries separate runtime-closeout annotations; generated tool manifests
retain their build-time PENDING field and never imply an automatic runtime test. It contains patch
descriptions/our code only, no proprietary executable or assets.

```powershell
python tools/r_ai1_hardening.py build ../corpora/retail/MRallye.exe .research-output/r-ai1-1/hardening/rbase-hardened/MRallye.exe --profile base
python tools/r_ai1_hardening.py build ../corpora/retail/MRallye.exe .research-output/r-ai1-1/hardening/randomized-hardened/MRallye.exe --profile mixed
python tools/r_ai1_hardening.py verify .research-output/r-ai1-1/hardening/rbase-hardened/MRallye.exe
python tools/r_ai1_hardening.py verify .research-output/r-ai1-1/hardening/randomized-hardened/MRallye.exe
```

Build refuses to overwrite existing EXE/manifest: reproduce to another fresh
ignored directory. Restore the isolated install using its preserved original;
no on-disk pristine source is overwritten. Research binaries stay ignored and
are not distributed. The intended eventual public mixed-class deployment is
still a removable external runtime mod with unchanged EXE on disk, not built here.

## Observable native layout

The exact profiles retain imagebase0x400000/size, active sink RVA0x2F7B7C
(VA6F7B7C, native references4D0623/4D05AE), vtable RVA0x29CEA8
(VA69CEA8, constructors64E4C0/64E560), sink object size0x30.
Main native command dispatcher `0x5B0990` case0x27 invokes Broker Editor opener
`0x65E990`. Broker-local dispatcher `0x65EC40` case2 obtains Broker via4D8EC0
and calls601D00. These opener/routes, vtable and logging function bytes remain
unchanged. Only the two documented branches **inside** Dump differ.

Research adapter `tools/r_ai1_observe.py` supports the two new exact hashes
after manifest inverse verification. Previous two exact profiles remain.
Its four public implementation hashes, basename/size/hash gates, UI commands,
native sink identity and JSON/raw selected-block integrity are retained.
Unknown builds/implementations fail closed. Public Observatory files/release
remain hash-identical and are not modified. Hardened captures carry
`build_profile` and `broker_dump_variant=native_hardened` at the wrapper layer,
not in native text. Recovery captures cannot pass the fresh oracle.

## Validation

- Baseline:285 passed,0 failed,0 skipped; compileall and diff-check PASS.
- Final synthetic:302 passed,0 failed,0 skipped, including17 new hardening tests.
- Loading native emulation:40/40 PASS; separate idle/type14/Attract byte checks PASS.
- Dump native fixtures:12/12 assertions PASS, including3 expected pristine unsafe
  paths and6 complete hardened outputs;9 full outputs parse unchanged.
- Existing chooser on hardened base:94/94 cases PASS (101 native invocations,
  including7 additional pristine guard controls). Legacy fixed selector248/248 PASS.
- Base/composed builds reproduce deterministically; both exact inverse verifiers PASS.
- Old fixed/general verifiers and raw-bound earlier human capture PASS.
- Research adapter offline parse/provenance and unchanged external file hashes PASS.
- `python -m compileall src tools tests`, `git diff --check`:PASS.

Native emulation is static proof only. [Loading](attract-loading-fix.md),
[Dump audit](broker-dump-null-fix.md), [human instructions](runtime-handoff.md).
Ignored logs/reports/candidates are under `.research-output/r-ai1-1/hardening/`.

Reproduce native tests with the installed bridge Python and latest Ghidra:

```powershell
& '<ghidra-bridge Python>' tools/scanner/r_ai1_hardening_emulate.py --install '<latest Ghidra>' --project _ghidra_project --candidate .research-output/r-ai1-1/hardening/randomized-hardened/MRallye.exe --observatory '<audited Observatory directory>' --output .research-output/r-ai1-1/hardening/native-emulation.json
& '<ghidra-bridge Python>' tools/scanner/r_ai1_emulate.py --install '<latest Ghidra>' --project _ghidra_project --general-source ../corpora/retail/MRallye.exe --hardened-base .research-output/r-ai1-1/hardening/rbase-hardened/MRallye.exe --output .research-output/r-ai1-1/hardening/chooser-emulation.json
```

The historical smoke/sampling handoff is completed. Human and raw-bound evidence
establish post-results Dump/liveness and subsequent normal loading/Restart.
Five captures include four fresh generations plus one Restart reuse; observed
variation is confirmed, uniform probabilities are not. The [runtime summary](runtime-closeout-summary.json)
and [closeout](runtime-closeout.md) are canonical. Opponent Capacity is deferred.
