# Native Dump after Race Results

Current scope correction: the warning below still applies to **pristine and
older un-hardened profiles**. The new exact [research hardened profiles](hardening.md)
contain StringList and XmlData NULL guards and are prepared for post-results
Dump smoke, **PENDING HUMAN VALIDATION**. Their [current handoff](runtime-handoff.md)
supersedes the old active-only plan. This does not establish universal Dump
safety or change the public Observatory distribution.

**KNOWN STOCK DEVELOPER-TOOL BUG**. Post-results native Debug->Dump is **UNSAFE**,
including after returning to frontend in the same process. Restart the game
process before another Dump once Race Results has been entered.

**CONFIRMED_BY_EXE**: race-time result setup `0x47D340` publishes
Frontend/RaceResults/PointsList through `0x4D8880` with payload0. StringList
setter `0x4DE1C0` accepts NULL and stores type9 and payload at node+4. Native
Dump walker `0x601D00`, type9 path near `0x602004`, prints the StringList header
and dereferences payload+4/+8 without a NULL check. NULL is permitted by the
setter but not handled by the diagnostic walker. This mechanism is in pristine
retail; human stock developer-tool crash observations are separate from
mixed-class race behavior. `0x47D400` similarly creates a NULL TimeList in the
alternate result format; no general Dump-safety claim is made.

For pristine/old profiles, do not require mixed-return/mixed-results Dump after a finish. Capture during
active races and use visual observations/screenshots for finish, result identity
and frontend return. The earlier generalization phase did not patch Dump;
the subsequent bounded hardening is described separately. Preserved Broker
paths after exit are not actor evidence.

## Adapter and oracle integrity

The adapter retains the audited portable Observatory implementation hashes,
basename/size/hash checks, native command path and raw-parser implementation.
It adds exact allowlisted research images. Legacy fresh-v2, original general
and both new hardening profiles remain supported. All inverse manifests restore
exact pristine; unknown images or
changed Observatory scripts reject before use. No allow-any/force option.
External files remain unchanged; capture/settings outputs stay ignored in the
main checkout, under the selected phase directory.

The fixed live Dump does not export registered Race/Networked. Oracle now
requires actual Race/NumNetworkPlayers=0 and NetworkSyncActive=False; an explicit
Networked value, if exported, must be False. Registry/path presence alone
does not establish a live value. Race/RaceID and Race/RaceName are the observed
lifecycle names; older Race/ID and Race/Name labels were inaccurate.

Automatic verdicts remain **BROKER_STATE_MATCH_ONLY** and
**BROKER_SAMPLING_MATCH_ONLY**, never FULL PASS. JSON entries and selected block
must reproduce the raw sidecar through the pinned original parser. Captures
must carry exact profile hash and command-proven freshness. A five-sample
summary checks varied classes/IDs, mixed classes and at least two non-player
class outcomes. Human evidence is still required for newly generated races,
own actor identity, motion, contacts, results/icons and stable frontend return.
