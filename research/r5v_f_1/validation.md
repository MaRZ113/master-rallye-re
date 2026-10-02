# R5V-F.1 cleanup candidate validation

## Source and Ghidra evidence

Retail source `D:\Game\Master Rallye\corpora\retail\MRallye.exe` is SHA-256
`bf8aef32407eb6552c05045b8abef149f32983cedd9503b865069b444c5f96b4` and matches
the other supplied retail executable copies checked in the local research
directory.

Ghidra Bridge used the existing local Ghidra/PyGhidra installation and a copy of
the existing retail `MasterRallye` Ghidra project under ignored
`research-output/r5v_f_1/ghidra/`. The original project and binaries were not
modified. Bridge raw assembly captured:

```text
FUN_00480a20   shared T1/T2 capacity stores
FUN_0047b040   three Quick Race group-0x35 name selectors
FUN_004adfb0   Car0/Car1 key lookup and RET 4
FUN_004819b0   Vehicle Select groups 0x33 and 0x34
FUN_00481e20   forward dense class mapping
FUN_00481e50   reverse dense class mapping
```

At the capacity, Quick Race group and getter instructions, Ghidra memory bytes
were compared directly with the SHA-verified retail file bytes and matched.
Raw dumps and temporary bridge configuration are local ignored evidence only.

## Candidate

| Artifact | SHA-256 | Validation |
|---|---|---|
| `MRallye_id26_cleanup_test.exe` | `120fb40bbe012914b82847f2d78f126dca0a8d6a5459855a7e29386ee63419c9` | 72 non-overlapping byte operations; deterministic source-SHA-locked build and `--verify-existing` pass. |
| `Data.sma` | `d21ec114ae60b93720fa16e84592642c3d4055541fc8ba8b5e50ffc857e270fa` | unchanged copy of prior 8,015-member candidate archive; full ZIP CRC passes. Its `DataScene/FrontendScreens/VehicleSelect.xml` member retains `T3_Car12` and includes `T1_Car8`. |

Capstone disassembly confirms the capacity hook reaches a helper that writes
`[ESI+0x20]=8` and `[ESI+0x24]=7`, then resumes at `0x480A55`. The three Quick
Race call sites target a wrapper that calls the original `0x4ADFB0`, aliases
only returned 26 to0 (`CMP EAX,0x1A`), and balances the original callee-cleanup stack contract.
The group immediates remain `0x35`. The existing Vehicle Select group
`0x33/0x34` aliases remain `PUSH EBX`.

The ID26 record uses a red RGBA canary; ID0's stock record is untouched. The
physical slot, sparse map, Trooper ID25 profile, race ID and runtime family are
unchanged from R5V-F. The archive is byte-for-byte the previous R5V-F archive;
no new art or asset is included.

The full patcher and validation outputs remain under ignored
`research-output/r5v_f_1/cleanup/`. The ignored package validator rechecks the
retail/source hashes, deterministic patcher output, all 72 byte ranges, emitted
x86 behavior, archive CRC and both Vehicle Select widgets. Its result is in
`research-output/r5v_f_1/cleanup/VALIDATION.json`. No candidate was launched in
the game; human steps and exact hashes are in
`research-output/r5v_f_1/cleanup/TEST_INSTRUCTIONS.txt`.

## Tests and runtime status

- `tests.synthetic.test_vehicle_registry_id26_patcher`: 6 passed after cleanup
  patcher changes.
- Full repository synthetic suite: 228 tests passed.
- Cleanup P0: **OWNER-REPORTED FULL PASS** for the candidate hash above.
- ID26 red marker: **OWNER-REPORTED RUNTIME-CONFIRMED**.
- ID0 stock-colour runtime comparison: **NOT REPORTED**; static patch does not
  alter ID0 initialization. The F.2 prompt explicitly makes this non-blocking
  for Mercedes source research.
- Mercedes candidate: **NOT GENERATED**; this report only clears the source
  audit gate.
