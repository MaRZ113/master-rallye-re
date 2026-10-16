> Historical checkpoint: old build paths/hashes below are preserved provenance. For current builds use overlay/README.md and dist/current/build-report.json.

# PILOT1.3 validation

## Build identity and staging

- Repository: `master` at locked baseline `61cb84d5c7f28d3bd88a3f1f9a8ce16d4c178390`.
- `modernization/renderer/` matches the locked revision; no working-tree changes
  were made there.
- Baseline and PS2-enabled source trees were staged independently from the
  locked Git archive. Both interface generators ran twice per tree with
  deterministic outputs. The staged-only generator patch preserves PS2
  declarations and buffer-wrapper hooks.
- Patch 0001 applied cleanly to exactly the seven previously approved renderer
  files. No fuzzy patching is used.

## Current clean staging build

Command: `python ps2-research/pc-port/overlay/build_overlay.py`.

Environment: Visual Studio 18 / MSVC 19.50, Win32 Release, Windows SDK
10.0.26100; both builds used `cmake --build ... --config Release --parallel 1`.

| Variant | Build | CTest | Proxy check | DLL SHA-256 |
|---|---|---:|---|---|
| Baseline | PASS | 24/24 PASS | PASS, PE32/I386 and expected exports | `ab356bf70b0309e8db1e1ef8e9744e728bfde92e9a894f639e8971e44bfad593` |
| PS2-enabled overlay | PASS | 25/25 PASS | PASS, PE32/I386 and expected exports | Recorded in `overlay/build-report.json` |

The focused extension test also passes separately:
`ctest --test-dir ps2-research/pc-port/.build-overlay/ps2-enabled/build -C Release -R ps2_port_extension_contracts --output-on-failure` — 1/1.

Python integration tests: `python -m unittest discover -s
ps2-research/pc-port/tests -v` — 8/8 PASS. `compileall` and `git diff
--check` pass. The build report contains the PS2 DLL hash, exact patch hashes,
generator output hashes, and separate build/proxy results.

## Focused behavior covered

- Modes 0–3 return masks `0x00`, `0x1F`, `0x0F`, and `0x10`.
- Mode 0 has no active request and does not turn on CPU mirroring.
- Mode 2 never reads, writes, or restores depth-write state.
- Mode 3 never reads, writes, or restores alpha-test/blend states.
- Unknown mask bits and mask zero fail closed before any state read/write.
- Successful transactions restore the exact original values and only touch
  selected slots.
- A failed native writer that mutates before reporting failure is included in
  reverse-order rollback.
- Static integration checks retain exactly one native draw and return its
  original HRESULT. These tests do not replace a live D3D8 capture.
- The exact geometry predicate remains fail-closed against incomplete and
  mismatched resource identities.
- Mode selection is logged once at device setup when diagnostics are enabled;
  exact target identity/mode/requested-mask/applied-mask is logged at most once
  per device. No per-frame identity spam is emitted.

## Runtime boundary

The user supplied the earlier runtime symptom and successful mode-1 draw/state
trace. Those raw trace files are unavailable in this checkout. PILOT1.3 has not
been run in-game, so the visual cause remains unresolved between depth-write/
draw-order behavior and alpha/texture-stage interaction. Status:
`IMPLEMENTED_PENDING_USER_RUNTIME`. PS2 visual parity is not established.
