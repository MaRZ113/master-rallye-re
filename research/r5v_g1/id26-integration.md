# ID26 stock-like unlock integration

## Existing test-unlock

The F.2f profile reaches a call wrapper from Vehicle Select at `0x004819CE`.
The wrapper first calls the native `FUN_0045A150`, then returns available for
physical ID26. This was a bounded accessibility aid for frontend and gameplay
testing. It is a **RESEARCH TEST-UNLOCK**, not recovered campaign semantics.

## G.1 candidate policy

The new fixed profile is `mercedes-g1-stock-unlock`. It carries the F.2f
Mercedes record, T1 local7 mapping, presentation strings, and frontend writer
hooks forward. At the same Vehicle Select call:

1. If the native record ID is not 26, it calls `FUN_0045A150` with the original
   record pointer unchanged.
2. If the native record ID is 26, it creates an 8-byte temporary predicate
   input whose ID field at `+4` is 3, then calls the same retail helper.
3. It returns the native helper result while preserving the original record
   pointer for the caller. The registry record and class/local map are not
   rewritten.

ID3's native case reads `Progress/UnlockedCars/T1CupCar1`. The global retail
`UnlockCars` and `UnlockAll` bypasses still run inside the unmodified helper.
The candidate no longer forces Trooper ID25 true; ID25 retains its native
`Bonus2` predicate.

## Physical identity protection

The candidate changes only the argument presented to the availability
function. It keeps:

- registry physical ID 26, class T1, local index 7;
- the `VehicleSelect/CarModel`, Quick Race and Race Options Mercedes identity;
- the red VehicleRecord[26] RGBA canary;
- runtime `CarID=26`, class 0, `CarType=Mercedes`, `WheelType=Mercedes` by the
  existing F.2f design.

Only runtime testing can establish that the full UI lock controls use the
returned result as expected in both progress states.

## Candidate construction

Source: exact pristine retail `MRallye.exe`, SHA-256
`bf8aef32407eb6552c05045b8abef149f32983cedd9503b865069b444c5f96b4`.
The patcher refuses other source hashes, verifies each expected original byte
sequence and the zero-filled cave, emits a complete range manifest, and can
rebuild/verify the candidate byte-for-byte. Candidate and outputs live under
ignored `research-output/r5v_g1/`; no executable is committed.

The built artifact is `research-output/r5v_g1/candidate/MRallye_id26_t1_cupcar1_unlock.exe`:
3,121,214 bytes, SHA-256
`ceb003aff00ee15d45d11fe838fbddfb4aa79baaaecce9a0068bf8b62cd40b8e`.
The manifest contains 73 non-overlapping declared operations. The key semantic
ranges are:

| VA / range | Purpose |
|---|---|
| `0x004819CE` (5 bytes) | Replace only the Vehicle Select availability call with the ID26 stock-mirror wrapper |
| `0x0068E2A0` (745-byte code-cave payload) | Existing registry/frontend profile plus the bounded ID26/ID3 availability wrapper |
| `0x0045A282` | **Unchanged**: the earlier unconditional ID25 test-unlock is omitted in this profile |
| `0x00481E20`, `0x00481E50` | Existing sparse T1 local7 ↔ physical ID26 mapping |
| `0x0047A65F`, `0x0047A6C4` | Existing ID26-only Race Options manufacturer/model fixes carried forward |

The patcher also retains audited registry, class-capacity, initializer, and
RaceTest relocation ranges. The adjacent manifest is the authoritative full
byte/range list; this table is a summary only.

This candidate is a research EXE. The long-term deployment target remains the
unchanged original EXE plus a removable fail-closed runtime module.
