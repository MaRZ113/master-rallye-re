# R5V-F validation and provenance

## Retail inputs

| Input | SHA-256 | Use |
|---|---|---|
| Retail `MRallye.exe` | `bf8aef32407eb6552c05045b8abef149f32983cedd9503b865069b444c5f96b4` | Exact patcher source; read-only. |
| Staged E0.2 `Data.sma` | `BB3C69CB97ADD992BF261F64C6ABAFAABAB946AB5CAE7E496D2D486C31A18020` | Known 8,015-member base containing the already staged T3_Car12 scene. |
| Staged E0.2 scene | `7676532F4BFAD1A196A5AD39FA3941BFE9EBDD9E636A58C5A8FCF9F18CC3F95A` | Read-only scene input for appending T1_Car8. |

The root installation `Data.sma` did not match the pinned 8,015-member E0.2
archive and was not used as a build source. The candidate build reuses the
explicitly hashed E0.2 archive, unpacks it under ignored `research-output`,
adds one scene node, then repacks it.

## Candidate outputs

| Output | Size | SHA-256 | Validation |
|---|---:|---|---|
| `MRallye_id26_t1_test.exe` | 3,121,214 | `DFF9E86A06A6E5312995CC81C5920AAF1739DE324D84B5605FF1C19B60748ABC` | 69 byte operations; source SHA guard; byte and overlap checks; deterministic rebuild and verify-existing pass. |
| `Data.sma` | 290,634,064 | `D21EC114AE60B93720FA16E84592642C3D4055541FC8BA8B5E50FFC857E270FA` | ZIP CRC/member checks; 8,015 members; one override. |
| Generated `VehicleSelect.xml` | 153,595 | `83006B28F88EA513C5ACA768B68BF16468C834F8F9242DFF18B19442EAB7A756` | Source-preserving overlay audit; T1_Car8 appended; T3_Car12 preserved. |

Member-by-member comparison against the E0.2 base archive found identical
member ordering and exactly one changed member:
`DataScene/FrontendScreens/VehicleSelect.xml`. It contains `T1_Car8` local7/ID26
with frame3 and Button7XPos, and retains `T3_Car12` local11/ID25 with frame5.

## Static binary validation

- Candidate is generated only from the exact retail EXE SHA.
- Registry allocation is `0xC34`; records0–26 end at `+0x580`; RaceTest rows
  begin at `+0x580` and end at the allocation boundary.
- Constructor, destructor, exception-unwind counts/bases, all 39 secondary
  initializer LEAs, and all 11 direct secondary consumers are represented in
  the categorized diff.
- ID26 uses the original full initializer and a separately owned name string.
- Forward/reverse maps, T1 capacity, ID26 display selector, and narrow test
  unlock operation are included in the structural self-check.
- The 328-byte candidate code cave at `0x68E2A0` was decoded with Capstone to
  check calls, branches, record offsets, and name-literal addresses.
- Candidate patcher `--verify-existing` rebuilt and matched both candidate and
  manifest.

## Tests

```text
tests.synthetic.test_vehicle_registry_id26_patcher: 4 passed
tests.synthetic.test_r5v_e0_2_vehicle_select_icon: 10 passed
```

The complete repository test suite is run at phase closeout. No original game
archive or executable was written by the candidate builders. Generated
executable/archive, unpacked archive contents, and Ghidra exports remain in
ignored `research-output` and are not committed.

## Runtime status

No game process was launched in this phase. P0 remains **WAITING FOR HUMAN**;
P1 remains gated on P0 FULL PASS. Save persistence and network support are
unproven. The prior E0.2 FULL PASS and E0 Trooper results are owner-reported
history, not a runtime observation from this phase.
