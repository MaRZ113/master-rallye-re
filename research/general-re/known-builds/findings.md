# Exact known build support — runtime-confirmed closeout

## Scope and release boundary

This research checkout accepts exactly two hash-and-size profiles. Unknown,
arbitrary patched and demo executables still fail closed. The published
v0.1.0-beta assets/tag remain pristine-only and are not rebuilt or uploaded.
The release builder refuses to produce a v0.1.0-beta package from this extended
source. A future release requires separate versioning and release approval;
the exact additional profile's runtime confirmation is recorded below.
Canonical tool version is retained here; **profile metadata**, not that version
alone, distinguishes captures from this research checkout.

| Profile | SHA256 | Size | Active sink RVA | Vtable RVA | Evidence |
|---|---|---:|---|---|---|
| retail-pristine | bf8aef32407eb6552c05045b8abef149f32983cedd9503b865069b444c5f96b4 | 3121214 | 0x2F7B7C | 0x29CEA8 | CONFIRMED_BY_RUNTIME (existing) |
| retail-widescreen-freeze | bcf310a79133b03aa89ce51197a37516ee27c1b0e9da19788519e849e7a2f2f6 | 3117118 | 0x2F6B64 | 0x29BF3C | CONFIRMED_BY_RUNTIME |

## Independently verified static evidence

Final exact-build observation: **CONFIRMED_BY_RUNTIME**, per the owner's report.
Status identified retail-widescreen-freeze; patched-front-1 and patched-front-2
diff (revision-only hidden) showed zero added/removed, value, metadata and
revision-only changes. Only this exact profile is confirmed. The following static
evidence and original implementation validation are preserved.

Ghidra 12.1.4 from the installed ghidra-bridge environment, JDK 25, isolated
scratch imports under this worktree's ignored research-output. No input binary
is written. Raw Ghidra programs/decompilations are not committed. Derived PE and
assembly fingerprints are in [static-evidence.json](static-evidence.json).

Six function pairs have identical address-normalized instruction sequences;
absolute operand addresses are masked, small constants/object offsets are kept.
This is correspondence evidence, not proof that every callee is equivalent.
Decompilation, assembly, vtable words and direct switch-table bytes independently
support the actual addresses used by Observatory.

| Role | Pristine VA | Patched VA | Instructions |
|---|---|---|---:|
| Formatted logger | 004D0620 | 004D0310 | 72 |
| Debug clear | 0064E640 | 00652500 | 14 |
| Debug append/realloc | 0064E670 | 00652530 | 100 |
| Broker opener | 0065E990 | 0065FB20 | 82 |
| Broker local dispatcher | 0065EC40 | 0065FDD0 | 184 |
| Main dispatcher | 005B0990 | 0064A9F0 | 564 |

The patched logger loads active sink VA 006F6B64 and dispatches through its
vtable +4. Constructor 00652380 writes vtable VA 0069BF3C. Its first two words
are 00652500 and 00652530. The constructor allocates 0x800 bytes and initializes
buffer base +0x28, write end +0x2C, allocation end +0x24, visible start +0x20;
window helper remains +0x0C with HWND at helper +4. Clear/append assembly and
decompilation confirm those offsets and reallocation fixups.

Main dispatch 0064A9F0 bounds command ≤0x58, translates through byte table
0064B294, then jumps through 0064B1A4. Actual bytes for 0x27 select 0064B0F7;
CALL at 0064B10A targets Broker opener 0065FB20. No address-delta assumption is
used. Main native menu builder 0064B380 still makes Game/Reset 0x32/separator/
Exit 0x2F, matching the guarded runtime menu identity.

Broker local dispatch 0065FDD0 uses table 00660010. Index 2 points to 0065FE51,
which obtains the broker via 004D8BB0 and calls Dump 00650020 at 0065FE5E.
Menu builder 00660040 creates Debug/Dump with literal ID 2; assembly at
006601E9/006601F9/006601FE confirms the text pointers and ID. The recovered
runtime title is Broker Editor. Exact title, PID, file identity, six top menus,
Debug submenu and ID 2 are revalidated before sending the local command.

Flow Builder command 0x30 exists in the patched main switch, but its full
open-path safety is outside this bounded comparison. It is intentionally not
enabled for the new profile. Existing pristine Flow Builder remains supported.

## Freeze script provenance

The supplied standalone script is read only and is never executed. It declares
file offset 0x24A1BC, 75 11 → 75 00; the combined EXE already has 75 00 there.
Its MD5 allowlist (1f7cb6d6371feada438dc70df6beec4f and
4e87eb51874111a6065df64504f165f1) matches neither current corpus. Current pristine
MD5 is cdbfa8d5d82a7990fa8feee960acd885; combined MD5 is
f40d1b0ccd7fe71c23cf1eb0c1d8e664. Pristine bytes at the same file offset are
8B CF, further illustrating why its patch site cannot be reused across layouts.
Widescreen/freeze names reflect supplied provenance; this task does not establish
an exhaustive patch history or every widescreen/freeze behavioral effect.

## Implementation and validation

Immutable profiles select all live addresses from exact SHA256 plus byte size.
Three-state/two-buffer consistency checks and all pointer/size/window guards
remain in place. Live metadata adds build_profile_id and retains actual image
SHA256/size, sink pointer/vtable, baseline freshness and dispatch provenance.
Old pristine snapshots without the new optional field still parse/diff.

Process selection shows profile IDs and PID when multiple known instances run.
Unknown identities and wrong sizes are rejected. Tool allowlist remains 0x27
Broker (both profiles) and 0x30 Flow (pristine only); Dump remains local ID 2.
No injection, process writes, hooks, patching, persistence or arbitrary command
support was introduced. No game command/runtime experiment was run in this task.

See [runtime handoff](runtime-handoff.md) and
[future manifest design](research-derived-design.md). The new profile requires
no further observation for the completed two-capture gate.

Original implementation automated validation: **319 tests PASS**, 0 failures/skips; compileall
src/tools/tests and git diff --check PASS. Both input EXE hashes are unchanged
after analysis. Tests cover profile selection/size rejection, profile-specific
global/vtable reads, live metadata propagation, old snapshot compatibility,
multiple-process selection, changed recipient identity and the beta release guard.

Reproducible collection: use tools/scanner/broker_core_evidence.py with the
ghidra-bridge environment, --binary for the verified input, --analyze for a new
isolated project and --function for the addresses above. Export pristine and
patched functions under known-builds/pristine and known-builds/patched; export
0064A9F0/00660040/0064B380 under known-builds/patched-routes. Run
tools/scanner/observatory_profile_evidence.py with --pristine, --patched,
--exports pointing at that ignored known-builds directory and --output pointing
at static-evidence.json. The summary contains no raw executable/decompiler dump.
