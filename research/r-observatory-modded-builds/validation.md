# Validation / evidence boundary

**READY FOR HUMAN RUNTIME**, not a Mercedes live-observation pass.
Base: closed R-AI1.2a4afcf52143c9b53a61ae5f59f1bdaabceb713594.
R-AI2.1 and R-UI1 are not merged. Their independent closeouts are indexed here
as commit metadata, not copied feature implementations.

| Current check | Passed | Failed | Skipped |
|---|---:|---:|---:|
| Full synthetic (existing353 +new39) | 392 | 0 | 0 |
| New profile/auditor/registry/checker/adapter cases | 39 | 0 | 0 |
| Native Mercedes class/local and initializer observations | 56 | 0 | 0 |
| Native R-AI1.2 regression | 824 | 0 | 0 |
| Native R-AI2 five-car regression | 44 | 0 | 0 |
| Native hardening (40Loading +12Dump) regression | 52 | 0 | 0 |

compileall src/tools/tests, diff-check, pristine/Mercedes exact-build verifiers,
both module verifiers and eight existing research EXE inverse verifiers PASS.
Current real Mercedes audit: ten matching bounded fingerprints and expected PE
layout. Actual Merc bytes changed only **in memory** for negative checks:
corrupted logger anchor -> INCOMPATIBLE; mutation outside anchors -> still
unregistered and rejected. Source EXE and external Observatory pins unchanged.

Synthetic audit fixtures are invented PE data, not copied retail bytes. Their
matching anchors cannot register an unknown hash. Build-specific pristine ID26
is rejected, merc ID26 accepted, class/local mappings invert and neighboring
stock entries are unchanged. Exact labels/active four-car context, family,
type/driver, capture hash/size/freshness and materialization paths are checked.
No automatic actor/physics/visibility claim. Physics constants for Mercedes
remain unestablished here; no fabricated canaries.

Native Mercedes emulation executes patched481E20/481E50 for all27 IDs, with
guarded memory/stack boundaries. Appended initializer runs native68E2A0, with
45A0B0 arguments captured at its entry. Its entire record/string allocator,
secondary scene constructor and renderer are not simulated. Report uses
NATIVE_STATIC_PASS and runtime_game_test=false. Reproducible command:

```powershell
python tools/scanner/research_build_emulate.py --install '<Ghidra12.1.4>' --source inputs/MRallye_merc.exe --project research-output/r-observatory-modded-builds/ghidra-project --output .research-output/r-observatory-modded-builds/native-registry.json
```

Use the Ghidra/pyghidra environment. Ghidra ProjectLocator rejects dot-prefixed
path components, hence this ignored phase project lives in `research-output`
while ordinary reports live in `.research-output`. No sibling project was used.
The previous local pristine Ghidra project was absent; a new ignored phase import
was created for regression execution. This is not a missing synthetic fixture.
No game source file was changed. No missing fixtures; zero skipped tests.

PartA branch totals independently: Challenge353, capacity351, UI351; zero
failed/skipped, compileall/diff-check and branch-specific candidate/state
verifiers PASS. Raw captures, logs, saves, generated EXEs/DLLs and Ghidra imports
stay uncommitted. The unrelated pre-existing `modernization/` files remain
untouched (tracked on another branch, untracked on these research branches).

Next: two first-active-race human captures in runtime-handoff.md. No post-Results
native Dump, no Restart before capture. No integration/mod distribution.
