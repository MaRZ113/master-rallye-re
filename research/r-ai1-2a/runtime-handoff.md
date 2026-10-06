# R-AI1.2a human handoff

**COMPLETED**. Historical handoff retained; see runtime-closeout.md. Use an isolated retail installation with dev Dump
available and a profile that already unlocks Challenge11. No save edit needed.
Preserve original EXE/config and prior logs. Stage the four-profile MRallye.exe,
MRallyeRandomizer.dll and INI from ignored `.research-output/r-ai1-2a/package/four`.
Use all other mode keys Stock during this narrow test.

EXE SHA256:185900aa1cb0fd1ce4dbac4bfa48196fb0b3753b7dddcbb5418a965e812d9980

DLL SHA256:055c0f73a10e169ce03c8671c12be19914c1651125d9bff7805fb94d5ebb9e1f

Run `python tools/r_ai1_observe.py --observatory <audited-Observatory-directory>
--candidate <staged-MRallye.exe> -- capture <label>`. Exact profile support only.
Run one command per label below. Capture AFTER the
visible details or active actors settle, not merely from old persisted paths.

1. **Stock control:** Challenge=Stock; newly enter Challenge11. Capture
   `challenge-preview-stock`. Expected human Megane18, opponent Icecream23,
   authored PRIVATEER ICE CREAM VAN name/model unchanged. Start, capture
   `challenge-race-stock`, observe normal play.
2. **Mixed:** Back/reenter with Challenge=Mixed. Preserve a copy of the INI
   used at this generation. Note the opponent vehicle name/3D model, capture
   `challenge-preview-mixed`. Start and capture `challenge-race-mixed` after
   actors appear. Name/model/ID must agree. If RNG chooses authored ID23,
   reenter for another new attempt; a same-ID draw alone is visually inconclusive.
   Complete the Challenge if practical; rules/progression must remain normal.
3. **Retry:** use the native Retry/Restart of the same attempt; capture
   `challenge-retry`. CarID/Class/DriverID must match the original attempt.
   No new Begin/generation group should appear merely from Retry/loading.
4. **Hot config:** enter a NEW Mixed selection, preserve its INI and capture
   `challenge-preview-hot`. While still there edit Challenge=Stock; Start the
   already-previewed attempt, capture `challenge-race-hot`. It must retain the
   previewed identity. Then Back/reenter; new selection must show stock identity.
5. **Diverse + second event:** reenter with Diverse; preview/race must match.
   Then test Challenge1/RaceID25 (authored Frontera6 versus Tata2) under Mixed
   for one preview/active-race smoke. No hardcoded Challenge11 assumptions.

Preserve JSON/raw pairs and the complete MRallyeRandomizer.log locally; do not
edit capture metadata or commit game-state artifacts. The log contains explicit
PID/event/serial Begin/Use records. Stock is pass-through; Diverse may perform
multiple RNG operations inside one generation group.

Checker command: `python tools/r_ai1_2a_preview.py check-challenge-pair
<preview.json> <race.json> --preview-raw <preview.dump.bin>
--race-raw <race.dump.bin> --candidate <MRallye.exe> --module <DLL>
--module-manifest <module-manifest.json> --observatory <audited-directory>
--config <preserved-generation-INI> --log <MRallyeRandomizer.log>`.
If an identical tuple repeats, select the explicit `--generation <serial>`.
For hot-edit testing pass the preserved generation INI, not the later Stock file.
Both captures must belong to the same exact image/process and be fresh native Dumps.

Verdict is **CHALLENGE_PREVIEW_STATE_MATCH_ONLY**. Human proof must separately
confirm visible name/model equality, actual AI behavior, Retry and completion.
There is no driver-name/class widget in this preview; compare DriverID between
original race and Retry rather than claiming a displayed driver identity.
Do not test six+, expand UI, or begin the public loader.
