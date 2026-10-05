# R-OBS2 validation

Current static result: **AUDITOR READY; mercv2 FAMILY/REGISTRY AUDIT PASS; HUMAN CAPTURE PENDING**.

| Check | Result |
|---|---|
| Tracked merc v1 exact build | `retail-broker-v1`, exact profile `retail-merc-id26`, registry `merc-id26` |
| Synthetic cosmetic byte outside anchors | Accepted by family, local exact profile created/reused |
| Critical Broker anchor mutation | Rejected |
| Wrong PE machine | Rejected |
| Changed section layout/raw bounds | Rejected |
| Cache reused for same SHA and same audit | Accepted after re-hash/re-audit |
| Cache for changed SHA / altered content | Rejected and current bytes re-audited |
| Unknown registry | Generic Broker structure accepted; registry-aware vehicle check refuses semantics |
| Stock Dump walker | `native_dump=true` for active-race capture; `post_results_native_dump_safe=false` |
| Public Observatory distribution hashes | Still pinned and unchanged by source changes |
| User-provided mercv2 `MRallye.exe` | SHA `1fbb3489…`, family `retail-broker-v1`, registry `merc-id26`, all 10 family anchors compatible |

The target was read from the user-provided path in the sibling vehicle worktree; no sibling files were written. The current checkout stores its derived local profile and audit report under ignored `.research-output/observatory/`.

Full synthetic suite: **399 passed, 0 failed, 0 skipped**. `compileall`, `diff --check`, `verify-build` for tracked merc v1, and family audit/profile creation for mercv2 pass. No proprietary EXE or local audit cache is committed. The direct audit is static; it is not a runtime validation.
