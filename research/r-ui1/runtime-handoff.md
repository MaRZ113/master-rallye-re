# Separate human UI test

Switch to `research/r-ui1` for these adapter/checker commands. Capacity tests
use `research/r-ai2-1` separately.

Use an isolated retail install, fresh profile and preserved original. Stage ONLY
`.research-output/r-ui1/MRallye.exe` (size3121214), verify SHA256
5507f3ebc474931084f9ddf2b06a3f7afe186c4e29a2dbd81519b86d00f32966.
No randomizer DLL, R-AI2 policy shim, capacity candidate or XML overlay.
Preserve the isolated original PlayerState/profile too: Next uses native save.
After testing restore both EXE and original profile (or reset the fresh profile);
do not leave saved5..7 counts for the original Three-only UI.
Enable native developer Dump as in prior tests; use the audited Observatory adapter.

1. Quick Race, one human, normal Race. Visit Opponents One..Seven using both
   keyboard and mouse arrows. Confirm text, no clipping/overlap, minimum/maximum
   clamp and no wrap. Capture `ui-opponents-one`, `two`, `three`, `four`, `five`,
   `six`, `seven`, with full prefix `ui-opponents-` for each label.
   Next may be used to verify the numeric count on the following setup screen;
   return with Back. Start is a separate boundary.
2. Five/Six/Seven are MENU ONLY. Leave without starting those counts. They remain
   menu-only for this Stock candidate even after independent capacity PASS until
   roster eligibility/integration is separately prepared. Two-human expanded counts
   also have no start authorization in this handoff.
3. Select visibly Four. Next commits numeric4. Use stock T1 ID0 TOMMEK DIRTBEAST,
   Track10/ItalyS4, GhostOFF, one human. Start; capture `ui-four-race`. Verify five
   independent cars/four normal AI, HUD/progress/collision/damage. Finish; capture
   `ui-four-results`, five rows/times/icons; Replay and frontend return.
4. Re-enter: verify committed Four remains. Change course/vehicle/difficulty in
   frontend and return to confirm the selection persists; restore ID0/Track10 for
   any repeat race. Close/restart the process and inspect the native saved selection.
   Keep any Five/Six/Seven persistence checks strictly in the menu.

Capture:
`python tools/r_ai1_observe.py --observatory <audited-directory>
--candidate <staged-MRallye.exe> -- capture <label>`.
Check menu:
`python tools/r_ui1_opponents.py check-menu <candidate> <snapshot.json>
--expected-ai N --observatory <audited-directory>`.
Four race/results: use `check-race` /`check-results --expected-ai 4`.

While browsing, QuickModeSelect/NumOpponents is index0..6;
QuickRace/NumOpponents may still be the previously committed count until Next.
Checker matches selected text source to list item, not English string parsing.
It enforces fresh exact-profile JSON/raw integrity and returns only
BROKER_FRONTEND_MATCH_ONLY /BROKER_STATE_MATCH_ONLY /BROKER_RESULTS_MATCH_ONLY.
It cannot prove visible text/layout, real input interaction, actors or completion.
Preserve captures/raw pairs and human observations locally.

Do not merge this with capacity candidates or the randomizer. Separate human
validation first; integration is a later phase. No9 or generic-N experiment.
