# R-BROKER1 — CLOSED / END-TO-END CONFIRMED

Source: project owner's final controlled-runtime report. These observations are
`CONFIRMED_BY_RUNTIME`; no live test was executed by the researcher in this
documentation/UX closeout, and no capture or save file is committed.

## U3 — FULL PASS

Normal Game Options changed Settings/Player1Name from 1P to U3TEST. Live String
entry: revision 1, GLOBAL, SaveFile PlayerState, SaveGame=True,
SaveOptions=False, SavePlayerState=True. The name was visible in race.

PlayerState.xml contained U3TEST; its # sibling preserved the previous generation.
A later normal QuickRace SelectCar confirmation issued another native save:
current XML remained byte-identical and # became byte-identical to that same
U3TEST generation. Thus the normal trigger, one-generation backup and an
identical-result save's generation/write behavior are runtime-confirmed.

After a complete process restart, capture **u3-reloaded-after-save** showed
U3TEST, revision 0, GLOBAL, SaveFile PlayerState, SavePlayerState=True.
**UI → Broker → PlayerState.xml → restart → Broker: FULL PASS.**

For this observed String entry: mutation increments revision; persistence
serialization does not itself increment it; fresh-process load begins at 0.
Existing per-type revision caveats remain in [revision semantics](../broker-core/revision-semantics.md).

## Trigger model

Eligibility is not scheduling. Explicit frontend/gameplay owners request mode 3;
the [static call map](playerstate-save-trigger.md) remains authoritative for
owners beyond the runtime-tested action. Normal shutdown has no blanket
PlayerState save. The earlier live-name/reverted-reload result is consistent with
no successful PlayerState output in that sequence; it was not serializer failure.
It does not prove the earlier name-editor request never ran.

## Closed core and retained unknowns

Closed core: Broker path/interning, entry layout/types, EMPTY/UNBOUND, SaveFile,
save flags, scopes, revisions, XmlFilename loading, XmlData factory, Game/Options/
PlayerState modes, native XML writer and # backup, Options and PlayerState
round trips, restart load-back, and Observatory runtime validation.
Options round-trip closure is accepted from the owner's final core-completion
report; this note adds no unreported option value or test sequence.

Non-blocking UNKNOWN: exact normal SCENE bulk-clear owner and USER producer/
lifecycle. These do not reopen R-BROKER1. Other bounded static questions remain
research notes, not blockers to the confirmed core.

The exact retail-widescreen-freeze Observatory profile also passed the owner's
two-capture observation; see [profile findings](../known-builds/findings.md).
Unknown executable identities remain rejected. Published v0.1.0-beta remains
pristine-only; no new release is built or published.

The historical [single-trigger plan](u3-save-trigger-test.md) is completed,
not a request for another test. No U4 or subsequent research phase begins here.

## Small Observatory Diff Files fix and validation

Diff Files (and explicit offline `diff` arguments) accepts a full JSON path or
a unique validated-history match by filename, stem, label, or label plus .json.
The interactive action shows three recent examples. Missing matches say Capture
not found; ambiguous matches list concise candidates and request a specific
filename/path. Raw-only files, missing/corrupt pairs and invalid selected-block
hashes are rejected. Existing raw SHA/size checks remain mandatory.

**336 synthetic tests PASS, 0 failed, 0 skipped**; compileall src/tools/tests,
JSON/CSV parsing, relative documentation links and git diff --check pass.
Tests cover resolver forms, ambiguity/missing pairs, selected-block corruption,
offline diff integration and existing history/profile safety regressions.
This changes offline lookup/validation and evidence metadata only; no native
capture dispatch, process-memory access, game save or release package is changed.
