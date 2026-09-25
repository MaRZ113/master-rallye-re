# Human runtime gates

## P0 — MENU / PREVIEW ONLY

Use the ignored candidate MRallye_slot25_test.exe with SHA-256 672d1945681900f3de5921e7a9032ea6d6e57d5e3fe1b49270e04994520222c2. See the adjacent TEST_INSTRUCTIONS.txt for safe placement and launch. Back up the retail EXE and use a disposable profile or back up game-local DataGame/PlayerState.xml; the game may auto-save and ID25 campaign persistence was not proved.

Boot, enter vehicle selection, select class 2 and cycle through all entries. Test whether an entry after the previous final car appears, can be selected, displays sane stats and shows Astero complete.dx preview. Move back and forth several times, leave and return to the screen, then exit normally. Note displayed name and selector marker position. **Do not start a race.**

Classify:
- **FULL PASS:** ID25 reachable, Astero preview, stable navigation and exit.
- **UI-PARTIAL PASS:** same core evidence but selector marker/layout is wrong.
- **FAIL:** entry unreachable, invalid stats/model, crash or unstable object lifetime.

## P1 — QUICK RACE, ONLY AFTER OWNER REPORTS P0 PASS

The owner must explicitly report P0 FULL PASS or UI-PARTIAL PASS before P1. Use the same candidate. Select ID25, start a simple Quick Race, check Astero body and wheels, steering/acceleration/braking/suspension, collision, visual damage/glass where practical, exit/finish, return to menu, then check original Astero ID16. A resource fallback with working physics is RESOURCE-PARTIAL, not full success. Do not intentionally save campaign/progress with ID25 selected. Stop after P1; Forklift is a different phase.

No human P0 or P1 observation exists as of this report.