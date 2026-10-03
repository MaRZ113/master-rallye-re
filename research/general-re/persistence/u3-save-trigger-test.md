# U3 closeout — one ordinary PlayerState trigger test

Status: **NOT_RUN**. One test, no automated save invocation or Broker editing.
Target: pristine retail SHA256
`bf8aef32407eb6552c05045b8abef149f32983cedd9503b865069b444c5f96b4`.

## Preparation

Use a disposable installation/profile. While stopped, copy/hash the entire
test profile/install baseline externally, including loose DataGame/PlayerState.xml
and its `#` sibling when present. Record executable identity, working directory,
native resource root and **absolute physical save paths**. Keep the originals
untouched; restore only while stopped or discard the disposable copy.

Enable the previously documented developer window setting if needed. Use
Observatory only to capture original Debug → Dump observations. Do not enable
developer saves, alter Broker values or patch/inject into the process.

## Exact action

1. Launch the disposable pristine game. Capture `u3-trigger-baseline`.
2. Through normal Game Options/name UI, change Player1Name to **U3TEST**.
   Record the exact accept/back sequence; capture `u3-name-live`. Verify String,
   live value U3TEST and SavePlayerState=True. Do not continue if the value is
   different. This UI's own name-editor exit can already request a save.
3. Enter **one-player offline Quick Race → Change Vehicle**. Select the **same
   already unlocked vehicle**. Do not confirm yet. Capture `u3-before-select`:
   require Settings/Player1Name=U3TEST, Frontend/InQuickRaceMode=True,
   Frontend/VehicleSelect/PlayerID=0. Record Frontend/QuickRace/Car0.
4. Copy/hash both physical PlayerState files **now**, with timestamps, outside
   DataGame. This separates any earlier name-editor writes from this trigger.
   If a file is busy, wait for an ordinary frame and repeat the read only; do not
   change attributes. Note if U3TEST is already present before confirmation.
5. Press the visible **SelectCar / Select vehicle confirmation button**, corpus
   Button ID 2. Do not use the negative/back action. Wait until returned to the
   QuickRace screen and the game has processed ordinary frames. Do not start a
   race, change setup or progress, or invoke any developer Save command.
6. Capture `u3-after-select`. Copy/hash PlayerState.xml and `#` again; retain
   the Debug log and any IO error. Read the XML semantically for Player1Name
   and QuickRace/Car0. Snapshotting is not itself a save-completion signal.
7. Exit normally; copy/hash again to distinguish subsequent writes. Restart
   the same executable/profile/root and capture `u3-reloaded`.

## Why this action

Independent corpus UI mapping + decompilation + assembly show:
positive ID2 → `00481340`, offline QuickRace branch → `004ADF50(0,car)` at
`00481456` → `005229B0(PlayerState,3)` at **00481495**. Saving is not guarded by
the car value changing. Confirming the same car avoids unnecessary gameplay
state changes while still traversing the save call.

## Expected results and interpretation

- Expected disk: PlayerState.xml contains **Settings/Player1Name=U3TEST**.
  Its `#` file is the immediately previous generation, which may already contain
  U3TEST if an earlier normal trigger saved it.
- Expected reload: Broker value U3TEST, revision **0** after typed reload.
- Already persisted before SelectCar: the earlier normal UI sequence saved;
  retain the timing evidence. The selected trigger still runs even if values
  and semantic diff are unchanged.
- Live U3TEST but no disk U3TEST after confirmation: retain actual output root,
  XML pair, times and Debug IO errors. This narrows the gap to request/queue/output
  or unobserved overwrites; it does not by itself prove filtering failure.
- Disk U3TEST then reload 1P: investigate load path/override order, not the save
  trigger. Stop without developer-control retries.
- Changed live name before confirmation: test precondition failed; stop and
  retain captures instead of interpreting the persistence result.

Report the exact button sequence, before/after/reload captures, file hashes and
log. No separate developer control is proposed: a normal static-confirmed trigger
exists. U4 and all broader persistence experiments remain outside this task.
