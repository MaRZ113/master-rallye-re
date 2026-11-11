# R-MOD1-B v6 — Change Mode stack fix

## Confirmed v5 failure

The owner reports that the exact v5 process passed retail verification, installed
all seven native operations, resumed, and left the retail EXE unchanged. Opening
Change Mode then hung with exit code `3489660927` (`0xCFFFFFFF`).

The emitted append helper at `0x70001500` kept its loop upper bound in
`[ESP]`, but allocated only that one DWORD. Before constructing the native
`enString`, it pushed the source-string pointer and emitted `LEA ECX,[ESP+4]`.
That address was the persistent bound slot, so the constructor's initial
`MOV [ECX],0` replaced the count. The next `CMP EDI,[ESP]` compared against
the string's state and could fail to terminate.

## v6 correction

`make_ui_list_code()` now allocates two DWORDs after saving flags/registers:

| Address | Purpose | Lifetime |
|---|---|---|
| `B = ESP` | configured exclusive opponent upper bound | entire append loop |
| `B+4` | temporary native `enString` object | one append iteration |

The helper uses `LEA ECX,[ESP+8]` after pushing the constructor's source
argument. At that point ESP is `B-4`, so ECX is `B+4`, never the bound.
After the constructor's native `RET 4`, ESP is back at B. `LEA EAX,[ESP+4]`
publishes the temporary object to the native list insertion call.

## Retail ABI and stack proof

The retail image was independently hash-checked as
`bf8aef32407eb6552c05045b8abef149f32983cedd9503b865069b444c5f96b4`.
Raw x86 disassembly / terminal bytes establish:

| Native routine | Exact terminal bytes | Stack rule used |
|---|---|---|
| `enString` constructor `0x004D11D0` | `0x004D1229: C2 04 00`; `0x004D1236: C2 04 00` | thiscall; callee removes its one stack argument |
| StringList insertion `0x00407B30` | `0x00407C65: C2 0C 00`; `0x00407C82: C2 0C 00` | thiscall; callee removes 12 bytes |
| string destructor `0x005B4C00` | `0x005B4C0A: C3` | cdecl; caller removes the pushed object pointer |
| localized lookup virtual target `0x00485BB0` | `0x00485BC8: C2 08 00` | callee removes the two selector arguments |
| localization singleton `0x00485CF0` | `0x00485D1E: C3` | no stack arguments |

Per iteration, the two lookup arguments are cleaned by the callee; the
constructor's pushed text argument is cleaned by `RET 4`; list insertion's
three arguments are cleaned by `RET 0xC`; and destructor argument cleanup is
the explicit `ADD ESP,4`. The loop returns to ESP=B with the bound intact.
Exit adds eight bytes, then POPAD/POPFD restore the exact entry ESP and flags
before replaying `8B 54 24 14 89 74 24 28` and jumping to `0x00479DD3`.

Stock already provides ONE/TWO/THREE. For requested maximum N, this helper
appends exactly `max(0,N-3)` localized entries, with selectors `3..N-1`.
The bound and navigation clamp still map to semantic counts 1..7. The localized
labels are the existing audited sequence ONE, TWO, THREE, FOUR, FIVE, SIX,
SEVEN; no new label strings or native list ownership behavior were introduced.

## Regression coverage

`tests/synthetic/test_r_mod1_native_plan.py` inspects the actual emitted bytes,
derives the effective ECX/object addresses from ESP, models the native RET
cleanup, and verifies the loop bound remains unchanged when the constructor
writes the object. It also requires the corrected displacement and rejects the
old overlapping forms. A separate test checks the call conventions against the
exact retail bytes when the pinned corpus EXE is present.
