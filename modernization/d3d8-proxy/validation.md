# Validation — 2026-10-05

**Codex-side infrastructure: ready. Game runtime: pending human.**

| Check | Result | What it establishes |
|---|---|---|
| Pristine EXE SHA/size/PE identity | PASS | Target matches R-GFX1 exact image |
| Header hashes and16/97 method names/order | PASS | Pinned ABI completeness, no missing/duplicate slots |
| Deterministic generator and newline policy | PASS | Manifest/source/mocks regenerate identically |
| MSVC Release Win32 build | PASS | Actual I386 DLL/PDB/MAP produced |
| GPU-free native CTest | PASS,1 suite | Known-IID/ref balance, parent lifetime,105 ordinary slot forwards with argument/result checks, raw texture pointer metadata |
| Native observer contracts | PASS, same suite | Failure preservation, Reset/state blocks/UP invalidation, unsafe read, pointer reuse/registry cap, F10, capture overflow, output failure, FPU environment, concurrent observer writes |
| Python synthetic/offline tests | PASS,32 tests | PE failures, export manifest, self import, exact-build joins, CALL-vs-return RVA, module/method gating, unknowns, native JSONL, actual wrapper return PC, overflow closure and bridge build gate |
| python -m compileall modernization/d3d8-proxy | PASS | New Python sources compile |
| stdlib verify_proxy.py | PASS | PE32/I386/DLL, required direct exports/ordinals, bounds, no self/delay import |
| Read-only Ghidra12.1.4 bridge queries | PASS | Verified retail program, project read-only, transactions rolled back, outputs only new ignored folder |
| git diff --check and changed-path audit | PASS at finalization | New phase-only paths; no binaries/build trees/logs staged |
| Visual stock parity / game captures / reset recovery | PENDING_HUMAN | Not established by any preceding check |

Native contracts intentionally use SDK-typed mocks with unique argument values,
including pointers, enum/scalar words and distinct return values. The105 ordinary
slots plus custom COM/create/parent tests cover the113-slot surface. Metadata
observations are tested without a GPU or real game. The one native executable is
synthetic; its exe hash is intentionally UNKNOWN_BUILD, testing fail-closed joins.

Native frame-output tests read a small complete frame (exact identity VIEW matrix,
unknown WORLD, caller-module/RVA) and a completed but truncated8192-draw frame.
The latter stays unsuitable for full-event absence claims. Concurrent observation
tests use four threads with1000 updates each under the actual trace guard.
Output-open failure preserves control flow; a partial-write/disk-full event is
handled in source but has not been forced on the real filesystem.

The verifier parses the actual compiled DLL using only Python stdlib and reports
hash/sections/imports/exports in [proxy-build.json](data/proxy-build.json). It does
not execute the DLL. PE/hash/build tests establish neither stock pixels nor
universal Windows/Wine compatibility.

Reproduce checks using [build.md](build.md). Vendor headers retain exact byte
hashes across Git checkouts through this folder's .gitattributes. Synthetic native
outputs and raw bridge exports are ignored, not committed. Existing project tests
were not updated and are not a dependency of this phase's checks.

The byte-preserved upstream headers/notices contain pre-existing trailing blanks.
Folder-local attributes exclude only those vendor files' original whitespace from
diff whitespace checking; the proxy's own sources/docs/tests remain checked.
