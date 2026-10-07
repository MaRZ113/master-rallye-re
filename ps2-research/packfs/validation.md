# Validation

Run date: 2026-10-07. Source/build boundary is the exact four hashes recorded in
`input-provenance.json`. This is offline/static validation, not PS2 runtime.

| Check | Result |
| --- | --- |
| Fresh input SHA256 and sizes | PASS, all four files available |
| Pure Python canonical PAK decode | PASS, 269668 bytes, exact golden SHA256 |
| Independent FFmpeg 8.0 LZO oracle | PASS, all 33 blocks, byte-identical decoded image |
| Structural directory | PASS, 3736 nodes, 137 directories, 3599 files |
| Hash membership and complete reachability | PASS, 1024 buckets |
| Child/sibling graph and inline parent paths | PASS, all 3735 nonroot nodes |
| File ranges | PASS, 3599 checked, zero invalid/overlap/gaps |
| Compressed file-header inventory | PASS, all 3345 use (1,1,8192) |
| Targeted resource extraction/full decoding | PASS, 8 resources |
| GXI size sanity | PASS, 6 extracted GXI satisfy exact 4-byte-per-pixel equation |
| PS2 tests | PASS, 26/26, canonical integration enabled, no skips |
| Existing `tests/synthetic/test_library.py` | PASS, 22/22 with PYTHONPATH=src |
| All CLI commands | PASS: info, decompress-pak, list, find, verify, extract |
| CLI input-overwrite refusal | PASS, exit 2 and explicit message |
| JSON reproducibility | PASS, repeat generation gives identical bytes |
| Compileall | PASS, PS2 tools/tests |
| Git diff --check and new-file whitespace checks | PASS |
| Proprietary output ignore checks | PASS, source inputs remain external, decoded/extracted/Ghidra output ignored |
| Full decompression of all TNG.000 resources | NOT RUN, outside targeted extraction scope |
| Manual PS2 runtime/graphics | NOT RUN |

The tests cover literal states, extended lengths, short matches, M1/M2/M3/M4,
overlapping copies, two blocks with a short final block, every truncation of a
synthetic frame, bad sizes, wrong decoded output, missing/invalid terminal,
trailing bytes, invalid root/count/section/string/relocation/node/hash/child
graphs, range bounds, host path traversal, symlink escape and hard-link/input
overwrite protection. Extraction tests use tiny synthetic files; proprietary
bytes are not embedded in source or fixtures.

Optional canonical tests require `MASTER_RALLYE_PS2_INPUT`. Missing inputs
produce explicit `INPUT_UNAVAILABLE` skips. They were present in this run.

Reproducible metadata hashes:

| File | SHA256 |
| --- | --- |
| tng-manifest.json | 295314f2c1cfc7e16217b6399709ac512d5f60bac40d45887a2301abd3c4f7e3 |
| input-provenance.json | fa8802bdbecb19d0a60add8729cf42e60f81e7e53d7e562e77fb47502260974e |
| graphics-targets.json | 343f21ece8bd55e150fddf31976187cd0a5d07a4bd49b86f6a0abe73253d8bc7 |
| extraction-provenance.json | 150dce175022ecfa2d90e241021aa8ed842e2b3f2976b2b3ca18ab657318b923 |
| golden-validation.json | fd9a50b5ebee4a5c2b78840b79743a1dba4699263e78631558f5456a8e9e5b6e |

Metadata uses explicit LF newlines, independently of the host's default.

## Repository boundary

Worktree: `D:\Game\Master Rallye\master-rallye-re-general`.
Branch: `master`. Starting HEAD: `68e5f10f51cf2d5524ac15b41787beeba1f28d44`.
The checkout was clean on entry. Git initially refused normal `switch master`
because the existing `master-rallye-re` worktree also owns master; the explicitly
requested switch used `--ignore-other-worktrees`. No new branch/worktree was
created. The existing research/general-re ref was not changed.

This track edits only `ps2-research/`. Later status showed concurrent changes
under `modernization/renderer/`, including its existing research/r-gfx5 area.
Those changes belong to parallel work and were not edited, staged, reverted or
tested by this track. They were independently committed as
`940d4edf39392118b796d832160528fbe75702ec` (`fix: bound ui anchor lifetime and
normalize renderer config`). Final HEAD is that commit, while the historical
research/general-re ref remains at starting HEAD. Final status is only
`?? ps2-research/`. Historical directories were untouched **by this track**.
No PS2 commit or push was made; all PS2 source/metadata/docs remain reviewable
additions without touching the shared index. Canonical original files were
rehashed after extraction and all four remained unchanged.
