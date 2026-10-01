# R5V-E0.1d.1 validation

## Static binary evidence

- Retail executable SHA-256 rechecked: `bf8aef32407eb6552c05045b8abef149f32983cedd9503b865069b444c5f96b4`.
- Existing XML-red candidate archive SHA-256 rechecked: `10f69fde8c9110abb69bb0c004904697af4e2ca024d4e38a24f97bbd04861072`.
- Archive baseline caveat: E0.1d recorded `D:\Game\Master Rallye\Data.sma` as `9bdf132cfde6e443e32f937b99289b07e9527457ae48fa9c7e0a373b52a28f30`. At this follow-up, that path hashes to `BA5734825209BA71CC8209CAF709DCC58F3D268ADB982D96DC45A1DC2C67E2D6`; `corpora\retail\Data.sma` and `!backup\Data.sma` both hash to `03C2B52D451B378C7EC634132EBFAB706616E33C57FEA2985B83DB66D3FD4B2F`. This phase did not write those archives, so the old E0.1d source hash remains a historical value and no unchanged-across-phases claim is made for the current top-level archive. The corrected test pairs only with the already checked XML-red candidate hash above.
- E0 baseline candidate SHA-256: `e19e80e64fcf2835d9883b115868e0cb8a0b63e05f48c8527580b2e0b531c0df`.
- The retail call-site bytes at `0x004A7659..0x004A766F` match raw Ghidra assembly: `52 E8 61 18 03 00 8B C8 E8 0A FE 02 00 84 C0 74 36`.
- `FUN_004D8EC0` epilogue is `POP EDI; POP ESI; POP EBX; ADD ESP,0x20; RET`; it does not clean the property argument.
- `FUN_004D7470` reads `[ESP+4]`, takes its object pointer from `ECX`, returns its flag in `AL`, and ends with `RET 4`.
- Ghidra P-code shows the stack-space argument and boolean result; assembly supplies the exact `RET 4` effect.
- The original retail `.text.VirtualSize` is `0x28D294`; the E0 baseline candidate `.text.VirtualSize` is `0x28D300`. The candidate builder is pinned to the latter exact SHA/layout.
- In the E0 baseline, helper range `0x0068E300..0x0068E30F` is file-backed and zero-filled. `.text` virtual end is exactly the helper start; extending by `0x10` ends at `0x68E310`, below `.rdata` at `0x68F000`.
- A raw source `.text` scan found no relative `E8`/`E9` target into the helper range; an image-byte scan found no existing absolute helper VA or RVA. Bridge `xrefs-to 0x0068E300` returned “Function not found” because the unallocated address is not a defined function; this is not treated as a clean xref result.

Raw Bridge logs and the isolated Ghidra project copy remain under ignored `research-output/r5v_e0_1d_1/ghidra/`.

## Generator and candidate

`tools/prepare_r5v_e0_1d_1_override_bypass.py` is fail-closed on source SHA, call-site context, section layout, cave contents, output paths, and overwrite attempts. It checks the three approved ranges and refuses other byte changes. The old `prepare_r5v_e0_1d_override_bypass.py` now refuses to emit the ABI-invalid helper.

New candidate SHA-256: `ce17e26a87f0d1f6aed4b96e77d2d57a4b3b7f9772c5f19f677af3c35d0a71fb`. Candidate bytes differ from the E0 source only at the hook call, helper range, and `.text.VirtualSize`; exact runs are in `patch-manifest.json`/`binary-diff.txt`.

## Human runtime status

- Red XML-only test: **RAN; bottom marker remained aquamarine/cyan-like** (user-reported).
- Old bypass: **CRASHED during race loading; invalid ABI candidate** (user-reported; not colour evidence).
- Corrected bypass: **RAN; user reports normal XML -> grey/white fallback and red XML -> red fallback; opponents unchanged**.
- Runtime colour writer / backing pointer: **NOT CAPTURED**; static VehicleRecord-tail producer path is documented in R5V-E0.1d.2.

## Automated checks

- Targeted ABI synthetic tests: **8 passed**.
- Full `tests/synthetic` suite: **208 passed** with `PYTHONPATH=src` using the installed `python` interpreter. The repository's documented `py -3` launcher is unavailable on this host; plain `python` needs the source directory added to its import path.
- `git diff --check`: **PASS**; only Git's LF-to-CRLF working-copy notices appeared.
- The final worktree and commit IDs are recorded in the closing report.

No executable, archive, source game asset, raw Ghidra export, or debugger capture is tracked by Git.
