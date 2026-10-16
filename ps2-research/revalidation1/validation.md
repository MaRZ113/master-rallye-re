# Validation

## Results

| Check | Result | Scope / note |
|---|---|---|
| Canonical PS2 input SHA-256 | PASS | ELF, CNF, PAK, 000 match validated identities |
| PS2 ELF header/PT_LOAD and frozen instruction-byte anchors | PASS | 620 original words and 10 data anchors match canonical mapped bytes; no semantic decode claimed |
| Original PC PE SHA-256 | PASS | Exact retail target used with REA |
| Selected France1 PSM/DX/GXI/DXT identities | PASS | Hashes and source offsets retained in inventory |
| Focused foliage source tests | PASS, 30/30 | Actual rerun with canonical PS2/PC/SDK inputs |
| PS2-port integration tests | PASS, 8/8 | Actual rerun against the PS2-enabled staged source root |
| PS2-port focused CTest | PASS, 1/1 | `ps2_port_extension_contracts` |
| Baseline proxy verification | PASS | Existing distinct DLL, verified this turn |
| PS2-enabled proxy verification | PASS | Existing distinct DLL, verified this turn |
| Baseline / PS2-enabled build | PASS in prior build report; not rerun | Documentation-only audit did not invoke a build |
| pytest | SKIP / unavailable | Active Python has no `pytest`; no installation attempted |
| compileall | PASS | Research tools/tests syntax check |
| `git diff --check` | PASS | Existing CRLF notices only; no whitespace errors |
| `modernization/renderer` unchanged | PASS | Scoped diff is empty |
| Course SDK unchanged | PASS | Reference remains clean at recorded HEAD |
| Raw PILOT1.3 trace/screenshots | NOT AVAILABLE | User/runtime report only |
| PS2 R5900 REA analysis | PROVIDER UNSUPPORTED | Typed capability error; no forced import |

Exact commands and exit-status interpretation are in
[command-log.md](command-log.md). No broad renderer regression suite or full
unittest discovery was needed because this pass changed no executable code.

The first CTest invocation omitted `-C Release` and CTest reported its
multi-config test as “Not Run”; the corrected `-C Release` invocation passed
1/1. The first invocation of the new ELF byte checker exposed an incorrect
repository-relative evidence path in that audit script; the path was fixed,
and the subsequent canonical check passed 620 instruction words and 10
anchors. Neither was a product test failure.

## Existing independent build report

The existing `overlay/build-report.json` records:

- baseline DLL SHA-256 `ab356bf70b0309e8db1e1ef8e9744e728bfde92e9a894f639e8971e44bfad593`;
- PS2-enabled DLL SHA-256 `a0035c53b749bcbdb2135174ebc73fdac366b8545ab255b370b6bb1823af11f9`;
- separate successful Release builds, CTest and proxy verification;
- deterministic generator outputs and exact staged patch hashes.

This is prior build evidence. It is not relabeled as an audit-turn build.

## Repository hygiene

At closeout, the only new tracked-scope files are under
`ps2-research/revalidation1/`. Existing dirty and untracked
`ps2-research/pc-port/` files remain preserved. No files under
`modernization/renderer/`, the Course SDK, original course assets, ELF, or PC
retail corpus were modified. No source commit or push was performed.
