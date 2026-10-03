# Reported runtime validation plan

## Safety boundary

Use a disposable retail installation whose executable hash is
`bf8aef32407eb6552c05045b8abef149f32983cedd9503b865069b444c5f96b4`. The
existing command trigger checks this hash and only allows the Broker Editor
open command `0x27`, with its separate metadata-registration confirmation.
The Observatory itself takes no game input and requests read-only process
access. Do not edit, remove, commit, or save broker values.

The Broker Editor open path has the existing R-DEV1.2 classification
`LOW_RISK_BUT_METADATA_MUTATION`: it may append two interned names to in-memory
broker-key metadata. This test accepts that documented open-only side effect;
it does not extend the safety claim to editing or committing.

## First capture

1. Start the disposable retail game. If needed, set `Menues/Enabled=True` in
   the disposable install so the Debug window is available. Keep the Debug
   window open; the capture reader intentionally refuses the startup proxy
   sink.
2. Record the PID shown by `Get-Process MRallye` and verify the image path is
   inside the disposable install.
3. Open Broker Editor with the existing narrow trigger:

   ```powershell
   python tools\runtime\dev_command_trigger.py --tool broker-editor --confirm
   ```

   Type exactly `OPEN BROKER EDITOR WITH METADATA REGISTRATION` when prompted.
4. In Broker Editor, invoke **Debug → Dump** once. Do this immediately before
   capture; the process Debug history may contain an older complete dump and
   the output itself has no timestamp.
5. Capture the process buffer to ignored research output:

   ```powershell
   python tools\runtime\broker_observatory.py capture --pid <PID> --label frontend --output research-output\general-re\broker-observatory\captures\first.json
   ```

   The command writes `first.json` and `first.dump.bin`. If the parse fails,
   the raw sidecar remains for offline diagnosis. Do not stage either file.
6. Review counts and paths without displaying values:

   ```powershell
   python tools\runtime\broker_observatory.py summarize research-output\general-re\broker-observatory\captures\first.json --json
   python tools\runtime\broker_observatory.py summarize research-output\general-re\broker-observatory\captures\first.json --prefix Race/ --json
   ```

7. Compare parsed counts and several exact path/type/save-flag/SaveFile rows
   against the original visible Dump and Broker Editor. Take a screenshot of
   the editor and Debug window, note whether the game kept running, then close
   the editor normally. Do not select an edit,
   remove, Update, Commit Changes, Save Game, Save Options, or Save Player
   State action.

## Optional state comparison

**State A:** retail frontend with no active race. Capture it with label
`frontend` as above.

**State B:** enter a normal race in the same session, invoke Debug→Dump, and
capture it with a course/class label such as `italy1-t2`. This no-edit
transition can show which path groups are context-sensitive. Invoke
Debug→Dump immediately before the second capture:

```powershell
python tools\runtime\broker_observatory.py capture --pid <PID> --label italy1-t2 --output research-output\general-re\broker-observatory\captures\race.json
python tools\runtime\broker_observatory.py diff <frontend.json> <race.json> --prefix Race/ --prefix Vehicles/ --prefix Drivers/ --format json --output research-output\general-re\broker-observatory\captures\race-diff.json
```

This is a data-observation test only. Do not use it to infer race-participant
capacity, mixed-class policy, or XmlData internals; those remain separate
research questions.

## Future mixed-class profile (prepare only)

For a later same-course T1/T2/T3 comparison, labels may be `italy1-t1`,
`italy1-t2`, and `italy1-t3`. Reuse the `Race/`, `Vehicles/`, and `Drivers/`
prefixes and separately review root `CarN` XmlData leaves. Do not run this
profile or interpret mixed-class behavior during the present phase.

## Expected checks and interpretation

- The selected block's parsed total should equal its printed TOTAL and the sum
  of GLOBAL/SCENE/USER; the SaveFile list count should match its heading.
- One earlier owner-observed state had 7,843 total rows (6,929 GLOBAL, 914
  SCENE, 0 USER). This is a comparison clue, not an acceptance constant; the
  active scene and game state can change counts.
- The sample `Hud/Hud0/Needle/MinAngle` row used `ID=SCENE`, `Float`, revision
  0, and SaveFile `__NO_SAVE`. It is only a format sanity check.
- A refusal saying the sink vtable differs means the Debug window is not the
  current logger sink or the target layout differs; preserve the raw/console
  error and stop instead of bypassing the check.
- A changing-buffer refusal means the logger was active during both reads;
  invoke Dump again after output settles and retry once. Do not add suspend or
  write access to solve it.

No runtime check in this document has been performed by the researcher.
