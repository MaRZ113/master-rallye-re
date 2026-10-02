# R5V-F.2a validation and provenance

## Provenance checks

- Current branch: `research/r5v-f-2a-native-mercedes-cooker`.
- Selected source root: demo-8.4.1 `DataGx/Vehicles/Copy of Mercedes`.
- Recomputed 59 root source-file sizes and SHA-256 hashes: **PASS**, exact match
  to the earlier machine inventory.
- Retail EXE SHA-256: **PASS**, expected pinned hash.
- Retail Data.sma SHA-256: recorded as provenance; original remained read-only.
- Retail 12.1.4 Ghidra Bridge exports: **STATIC PATH EVIDENCE** only.
- Demo-9.10 cooker report: reviewed as separate historical evidence; not
  substituted for retail-native cooking.

## Gate matrix

| Gate | Result | Evidence |
|---|---|---|
| Unique Mercedes source locked | PASS | 59-file content-addressed manifest. |
| Retail model loader / GXM reader traced | PASS, static | `0x0053C3F0` → `0x00609190` / `0x00609E90`. |
| Retail DX writer and expected rev135 constant | PASS, static | Direct call to `0x00551260`; raw pushes `0xD00D`, `0x87`. |
| Retail texture cook path traced | PARTIAL, static | `0x0053DCC0` reads GXI and calls DXT writer; exact path rebase/stem resolution remains open. |
| Complete/car/wheel retail cache misses | NOT RUN | No runtime log or output. |
| Required retail-cooked textures | NOT RUN | No native DXT output. |
| Cook A/B determinism | NOT RUN | No cooked outputs. |
| Retail model parser / semantic checks | NOT RUN | No rev135 outputs. |
| Authentic cooked tag101 collision | NOT RUN | No cooked `car.dx`. |
| R5V-F.1 regression | See test results below | No registry/patcher source changed. |

## Tests and regression

Command:

```powershell
$env:PYTHONPATH = (Resolve-Path 'src').Path
python -m unittest discover -s tests\synthetic -v
```

Result: **PASS**, 228 tests. No tests or helpers were added by this
research-only change.

F.1-specific regression tests passed:

- `test_deterministic_patch_and_no_source_mutation`;
- `test_emitted_capacity_stub_sets_t1_eight_and_t2_seven`;
- `test_sparse_mapping_and_donor_profile_are_explicit_and_isolated`;
- `test_quickrace_alias_wrapper_preserves_stdcall_and_only_aliases_id26`;
- `test_expands_storage_construction_destruction_and_secondary_array`.

Together they verify the cleanup candidate generator remains deterministic,
T1/T2 capacities remain 8/7, ID26 stays sparse-mapped to T1 local7, the ID26
display alias remains scoped, and the original Trooper ID25 path remains in the
patch profile.

The existing F.1 candidate was also read-only verified against a fresh
deterministic rebuild:

```powershell
python tools\patch_vehicle_registry_id26.py `
  'D:\Game\Master Rallye\corpora\retail\MRallye.exe' `
  'research-output\r5v_f_1\cleanup\MRallye_id26_cleanup_test.exe' `
  --verify-existing
```

Result: **PASS**, candidate SHA-256
`120fb40bbe012914b82847f2d78f126dca0a8d6a5459855a7e29386ee63419c9`, 72
operations, source hash matched. The stored F.1 manifest still says
`WAITING FOR CLEANUP P0`; that is a stale static manifest status. The separate
F.1 report records the owner-reported cleanup P0 FULL PASS. No runtime test was
rerun in F.2a.

An independent source check also passed: all 59 manifest hashes still match the
read-only corpus, the three selected GXM roles parse, their 25 distinct GXI
references resolve, and each has a paired DXT. The retail EXE and Data.sma
hashes match the values recorded in the manifest.

## Modification boundary

No retail/demo executable, Data.sma, unpacked canonical asset tree, registry,
class mapping, or game resource was modified. No candidate, model, texture,
GXM rebase, or package was generated. Ignored Ghidra output remains under
`research-output/r5v_f_2a/`; none is committed.

**Overall: BLOCKED.** Exact missing edge and next bounded step are in
[findings.md](findings.md).
