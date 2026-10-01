# R5V-E0.2 validation and provenance

## Prior closeout

R5V-E0.1d.2 was recorded before this phase in commit `a8b9d88`
(`research: record R5V-E0.1d.2 vehicle race-colour runtime proof`). Its runtime
result is user-reported and documented there. E0.2 does not alter or retest
that result.

## Source and generated candidate

| Item | SHA-256 | Notes |
|---|---|---|
| Retail source `Data.sma` used for the candidate | `87EEC21C395245F7C08D43553F2E2E0341D66C0D1E16EB683D0C79C3F7C2B06F` | read only |
| Retail `VehicleSelect.xml` | `EC7FD6372FE5008B1039EB8E09890EF3B37396DAD1581568AF439CBB611B58E1` | 148,236 bytes |
| Carsheet container | `712D655CD01FE2A6C7B5D3F9FD6B47234FDCC0430F1FCF4A85E383454131547F` | 4,752 bytes |
| Diagnostic frame 5 | `370007A674232CB2BB6FDAB6FC00C2BEEF5247F7FBFCDBAEAE5D4D3E1F73D65D` | 128x128, 65,556 bytes |
| Generated scene | `7676532F4BFAD1A196A5AD39FA3941BFE9EBDD9E636A58C5A8FCF9F18CC3F95A` | only `T3_Car12` appended |
| Candidate `Data.sma` | `BB3C69CB97ADD992BF261F64C6ABAFAABAB946AB5CAE7E496D2D486C31A18020` | structurally validated; human reports E0.2 FULL PASS, but tested archive hash was not supplied |

The 8,015 files in `Data.sma_unpacked` were compared by path and content
against the source retail archive; there were zero differences. The packed
candidate also has 8,015 members. A member-by-member comparison against the
source archive found exactly one changed member, the intended Vehicle Select
scene. The source archive and source scene were not modified.

## Automated checks

The new synthetic tests cover T3_Car12 generation, generic T1/T2/T3 append
operations, a future T3_Car13 profile, current retail position-key rejection,
ID mismatch, locked template rejection, invalid frame/source hash, DXT
validation, source-byte preservation, idempotence and refusal to overwrite a
different candidate output.

Targeted command:

```powershell
python -m py_compile tools\prepare_vehicle_select_icon_overlay.py tests\synthetic\test_r5v_e0_2_vehicle_select_icon.py
python -m unittest tests.synthetic.test_r5v_e0_2_vehicle_select_icon -v
```

Targeted result: **8 tests passed**. The full synthetic suite also passed:

```powershell
$env:PYTHONPATH = 'src'
python -m unittest discover -s tests\synthetic -v
```

Full result: **220 tests passed** in 14.462 seconds.

The suite verifies tooling and packaging invariants; it cannot prove that the
game visibly draws the new widget.

## Runtime status and limits

The candidate archive is staged at
`research-output/r5v_e0_2/runtime-test/Data.sma`. No game executable or source
archive was changed. The owner reports **FULL PASS**: T3 local 11 / ID25 was
selectable; the 12th icon appeared in the correct slot; Trooper preview
remained correct; and the frontend stayed stable. This report was supplied by
the user and was not independently reproduced. The tested executable and
installed archive hashes, screenshot, and runtime log were not supplied, so
the observation cannot be tied cryptographically to the candidate SHA above.

The scene overlay can be regenerated from the verified local retail tree with:

```powershell
python tools\prepare_vehicle_select_icon_overlay.py `
  --source-scene "..\Data.sma_unpacked\DataScene\FrontendScreens\VehicleSelect.xml" `
  --output-scene "research-output\r5v_e0_2\overlay\DataScene\FrontendScreens\VehicleSelect.xml" `
  --asset-root "..\Data.sma_unpacked\DataGx\Frontend\VehicleSelect" `
  --manifest "research\r5v_e0_2\icon-mapping.json"
```

The full candidate was then built with the existing validated `mrtool.py
pack-sma` override workflow, changing only that archive member.

Demo builds were read-only and remained outside Git. Raw Ghidra Bridge output,
decoded icon previews, overrides and the full candidate archive remain under
ignored `research-output/` and are not committed.
