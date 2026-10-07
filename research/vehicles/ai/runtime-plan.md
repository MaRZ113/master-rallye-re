# R5V-H.0.1 runtime handoff — historical / superseded

This was the H.0.1 test procedure. Its forced-ID26 Results-name and native
post-Results StringList Dump checks were later completed; see
[runtime-results.md](runtime-results.md). Do not use these H.0.1 candidates as
the current natural-pool test. The active H.1 instructions are in
[natural-t1-runtime-plan.md](natural-t1-runtime-plan.md).

## Historical H.0.1 status

The H.0 forced ID26 actor path is **CONFIRMED_BY_RUNTIME**. This handoff tests
the newly added Results-name selector and the separate neutral Loading/Attract
and native Dump guards. Both current candidates remain research-only and must
be launched from their verified runtime package roots.

## Candidate A — ordinary hardened, no randomizer

This is the separate ordinary Hardened EXE requested for stock/player tests.
It contains G.1/G.2, neutral hardening, and the bounded display-only ID26
Results selector; it contains no forced AI hook and no opponent randomizer.

* EXE: `.research-output/vehicles/ai/hardened-ordinary-no-randomizer/runtime-package/MRallye.exe`
* SHA256: `391d5d864699b6e945eed43fd8e7bc28b28639b24b222428ab79231e7cc3a819`
* Runtime Root: `.research-output/vehicles/ai/hardened-ordinary-no-randomizer/runtime-package/`
* Candidate manifest: `.research-output/vehicles/ai/hardened-ordinary-no-randomizer/candidate/MRallye.manifest.json`

Prelaunch verification from the checkout:

```powershell
python tools\vehicle_hardened_runtime_package.py verify `
  --runtime-root '.research-output\vehicles\ai\hardened-ordinary-no-randomizer\runtime-package' `
  --source-root '.research-output\vehicles\unlock\runtime-package' `
  --candidate-manifest '.research-output\vehicles\ai\hardened-ordinary-no-randomizer\candidate\MRallye.manifest.json' `
  --profile ordinary-hardened
if ($LASTEXITCODE -ne 0) { throw 'Ordinary hardened package verification failed' }
```

Use this candidate for a short ordinary Quick Race control: ID0/T1 player,
one human, stock opponent count, and a stock course. Expect the normal stock
AI pool; Car1 must not be forced to ID26, and no randomizer policy applies.
This checks that the separate baseline is useful, but does not by itself prove
the new Dump or Results fixes for ID26 AI.

## Candidate B — forced ID26 AI, hardened

Use this package for the H.0.1 Results and Dump retest.

* EXE: `.research-output/vehicles/ai/forced-id26-proof-hardened/runtime-package/MRallye.exe`
* SHA256: `9255c9d7cb27336d0a5324bd193719c768f09f5bb7d37e30bab384031b0de0e7`
* Runtime Root: `.research-output/vehicles/ai/forced-id26-proof-hardened/runtime-package/`
* Candidate manifest: `.research-output/vehicles/ai/forced-id26-proof-hardened/candidate/MRallye.manifest.json`

Verify before launch:

```powershell
python tools\vehicle_hardened_runtime_package.py verify `
  --runtime-root '.research-output\vehicles\ai\forced-id26-proof-hardened\runtime-package' `
  --source-root '.research-output\vehicles\unlock\runtime-package' `
  --candidate-manifest '.research-output\vehicles\ai\forced-id26-proof-hardened\candidate\MRallye.manifest.json' `
  --profile forced-id26-ai-hardened
if ($LASTEXITCODE -ne 0) { throw 'Forced hardened package verification failed' }
```

Then launch only the package's `MRallye.exe`, from that same directory. Use a
fresh profile; do not copy PlayerState. In a normal single-player T1 Quick Race
with three opponents, select stock ID0 as the human. Confirm the existing G.1
locked-ID26 behavior still shows native locked art/text and blocks committing
the locked car. Start the race only with the ID0 player.

The active-race state should remain four cars/one human, with Car1 forced to
ID26/T1 and its native DriverID; Car2/Car3 should stay ordinary T1 opponents.
Human-check the distinct Mercedes actor and AI movement. Finish the race.

At Race Results, verify:

* the ID26 AI row exists and no longer says `GALOCAL UNKNOWN`;
* its displayed driver name follows the selected DriverID in the active race;
* other stock result names and vehicle icons remain normal.

Capture an Observatory snapshot labelled `h0-1-forced-results` and preserve
its raw sidecar. The active-race capture from H.0 does not include NameList;
this new Results capture is needed before the display fix can be marked
`CONFIRMED_BY_RUNTIME`.

On the Results screen, invoke native Debug->Dump once. The game must remain
alive, `Frontend/RaceResults/PointsList` must be safely represented, and output
must continue past the Results entries. Capture the post-Results state as
`h0-1-forced-dump`; preserve JSON and raw sidecar. Do not infer allocated-empty
from textual `{}`.

Finally test one Restart/loading transition and verify that the game returns
to a normal Quick Race rather than being redirected into AttractMode. This is
the human check for the legacy Loading false-trigger hardening. Idle-menu
Attract remains a separate, statically untouched path.

## Exact package facts

Both packages stage the final G.1 VehicleSelect scene at the runtime Root with
SHA256 `6cdf398b892dbe01d2a1258030d2785e568cd993e4cf01d9dc4378ae9207341d`,
and include the pinned Mercedes assets. The G.1 resource source contains a
generated profile in its working tree; the hardened packager copies only
profile-pinned resources, not PlayerState files or backups. On-disk verifiers
currently return `PASS` for both profiles.

The required G.2 sound profile remains stock ID0. The forced candidate is not
a randomizer and does not change NumCars. Neither candidate changes natural T1
pool membership.

## Stop rule

If either package verification fails, do not launch it. If the new Results
candidate still shows `GALOCAL UNKNOWN`, preserve the Results capture and stop
for a focused selector correction. If native Dump still crashes, preserve the
complete crash point/raw output and stop; do not broaden into generic Broker
formatter redesign. Natural T1 pool inclusion was outside H.0.1; the current
natural-pool procedure is documented in
[natural-t1-runtime-plan.md](natural-t1-runtime-plan.md).
