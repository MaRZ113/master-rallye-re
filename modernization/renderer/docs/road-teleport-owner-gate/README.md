# Road Teleport — Vehicle Owner Gate Fix

## Result

The arm gate now joins the live one-car race participant and the physical D3D/physics observer track by verified participant semantics. It no longer compares `RaceCertificate.actor` with `NativeLinks.actor`: those pointers belong to distinct object chains. For the supported single-human-car route, the proof requires the current race certificate, typed `Race/Car0/PlayerType == 1`, exactly one current physical track with native `PlayerType == 1`, stable controller/handle/actor/body/backing links, unchanged track generation, no pending native recovery, a freshly read zero byte at backing `P+0x33`, and a readable zero reset-manager timer.

The periodic observer cache remains useful for event tracking, but its cached `track.flag.set` is no longer an arm veto. The current backing byte is reread at the arm boundary, so a stale cached set bit with a fresh native zero is accepted. A currently set or unreadable byte still rejects. AI tracks may coexist; multiple human tracks remain ambiguous and fail closed. The supported `single_human_car_race` certificate still restricts the actual teleport workflow to one human car.

`unique_current_human_controller_required` remains the compatibility-level arm rejection reason. `owner_gate_reason` and the bounded `owner_gate` JSON record provide the specific subreason and the race participant, physical actor/controller/backing, track counts/generation, cached and fresh flag, pending state, and timer evidence. Gate counters are cumulative for the current observer installation.

The physical actor is pinned in the request and remains the identity checked at native selection. No native Reset ABI, transaction bridge, Broker state, or physics state is directly written by this fix. The observer and owner gate are diagnostic/admission code only. An `armed` request is not proof that native relocation was consumed or that the chassis reached the marker.

## Static basis

The existing research in `docs/r-cam1-a3j/complete-relocation-analysis.md` records the typed `Race/CarN/PlayerType` assignment and the separate native physics handle/controller construction. `docs/r-cam1-a3j/broker-transform-routing.md` records the `Controller/CarN` Broker adapter relationship to the backing object. Those historical files were not edited. This fix adds the typed participant value to the live `RaceCertificate` and requires its current value to agree semantically with the unique physical `PlayerType == 1` controller.

The equality failure and stale-cache behavior were also present in the prior runtime log `session-20261011-231455-3788.jsonl`: the certified lifecycle actor and physical NativeLinks actor differed; the observer had one human track and three AI tracks; arming rejected all five attempts under the generic gate reason. This evidence diagnoses the gate; it does not establish a teleport runtime pass.

## Validation

- Win32 x86 Release build: passed.
- CTest: 21/21 passed.
- Renderer Python suite: 189/189 passed, including exact-retail observer verification tests.
- Root synthetic suite: 630/630 passed.
- `compileall`: passed.
- Proxy verification: passed; PE32/I386, expected exports present, no recursive D3D8 import.
- `git diff --check`: passed (Git emitted only existing CRLF/LF normalization warnings).
- Human in-game retest: pending.

Built DLL (ignored build output, not archived): `modernization/renderer/.build-msvc/Release/d3d8.dll`, SHA-256 `346ead0409b29d7b71897910deaa6b3f30662ae3de0d3abaa5358a168c028a72`, 2,226,176 bytes.

## One-session runtime handoff

Keep the current exact-build configuration and run one ordinary France1 offline race with the observer and road-teleport diagnostic enabled. Pause the native game, enter Freecam, move near a live road target, press the arm key once, then capture F10 while still paused. Expected owner proof is `owner_gate.accepted=true`, `owner_gate_reason="accepted"`, one verified participant and human controller, current `P+0x33 == 0`, no pending recovery, and a readable zero manager timer. If the cached flag says set while the fresh value is zero, `apply_flag_snapshot_stale=true` is expected and must not block arming.

Only after the arm result and diagnostic look correct, resume normally and allow one ordinary stock recovery/reset to exercise the already-existing transaction observation. Capture the session JSONL and F10 record. Pass means the gate arms only with the stated proof, the normal native path remains intact, and any later transaction stages are observed through existing diagnostics. Fail means an unexpected owner subreason, missing/stale links, a reset conflict, stock behavior altered before a verified arm, or a crash. Do not interpret `armed` alone as successful relocation.

## Source archive

`source-files.zip` contains the files changed for this owner-gate stage, plus this handoff. It excludes generated DLLs, PDB/OBJ/LIB files, the game executable, and runtime captures.
