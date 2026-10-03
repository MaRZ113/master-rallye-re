# U3 reported normal-UI Player1Name observation

**Current: U3 FULL PASS; R-BROKER1 CLOSED / END-TO-END CONFIRMED.**
See [final controlled round trip](final-closeout.md). The initial observation
below is retained as history; it is not the current closeout status.

Evidence source: user's controlled-session report supplied for this closeout.
`CONFIRMED_BY_RUNTIME` for the reported observations below; the researcher did
not execute the game or independently inspect the reported raw captures/save
files in this task. Sequence timing and executable identity must be recorded in
the next controlled test. No runtime dumps or save XML are committed.

| Boundary | Observed result | Grade |
|---|---|---|
| Normal Game Options UI → live Broker | Settings/Player1Name: 1P → U3TEST, String, revision 1, GLOBAL, SaveFile PlayerState | CONFIRMED_BY_RUNTIME |
| Eligibility | SaveGame=True, SaveOptions=False, SavePlayerState=True | CONFIRMED_BY_RUNTIME |
| Same-session race consumer | Modified player name visible during race | CONFIRMED_BY_RUNTIME |
| Disk name value | Supplied PlayerState.xml and PlayerState.xml# both contain 1P; no U3TEST | CONFIRMED_BY_RUNTIME (reported file evidence) |
| Reload | After full restart: 1P, revision 0 | CONFIRMED_BY_RUNTIME |
| Persistence from tested sequence | NOT OBSERVED | Not U3 FULL PASS |

Reported backup/current generations differ at Frontend/QuickRace/Car0: **0 → 15**.
This corroborates an active native PlayerState write and one-generation backup.
It does **not** establish whether that write preceded or followed the name edit.

Correct semantics: eligibility → explicit owner requests mode 3 → serializer
filter → queued disk writer → successful reload are separate boundaries.
The [new static caller map](playerstate-save-trigger.md) resolves the trigger
owner question. It also finds a name-editor close save, so absence of a universal
mutation hook alone cannot explain this U3 outcome. Request execution, deferred
IO errors, physical output root and exact UI ordering remain possible gaps;
none is selected as the diagnosis without the next observation.

Historical status at the initial observation: PARTIAL. The later
[mapped ordinary QuickRace confirmation](u3-save-trigger-test.md) and restart
load-back completed successfully; see [final closeout](final-closeout.md).
