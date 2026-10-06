# R5V-G.1 vehicle unlock findings

## Final result

**R5V-G.1 Vehicle Unlock + Frontend Identity Architecture: FULL PASS / CLOSED.**
ID26 mirrors the native ID3/T1 Cup availability condition while remaining
physical ID26. Locked text, art, disabled accept, natural unlock, and Mercedes
identity are runtime-confirmed. Final Race Details captures and human visual
checks confirm `MERCEDES ML-320` in Master Rallye and Rallye Cup. The owner also
reports a stock ID0 Race Details regression PASS and full stage/Results PASS
on the final candidate. See `closeout.md`, `runtime-captures.json`, and
`validation.md` for evidence and limits.

## Architecture

Quick Race class reachability is separate from per-vehicle availability.
`FUN_00480B60` constructs class reachability; `FUN_0045A150` evaluates an
absolute vehicle ID against `Progress/UnlockedCars` and cheat bypasses. The
G.1 candidate mirrors ID3 only as temporary input to the stock availability
predicate and locked-reason selector. This allows ID26 to use
`Progress/UnlockedCars/T1CupCar1` without changing the physical registry,
T1-local7 mapping, Mercedes resources, or race identity.

Correct locked behavior includes all of the following: unavailable model
state, stock requirement text, locked thumbnail, disabled frontend commit
control, and blocked normal accept. `FrontEnd/Network/selectedCar` is the
highlighted/current vehicle identity and is not proof of commit; the runtime
oracle combines `UI/Enabled` with actual interaction.

Frontend vehicle identity has independent consumers. The qualified ID26
channels are Vehicle Select, Quick Race, Race Options, Vehicle Setup, and Race
Details. The Race Details writer is `FUN_0047C080`, group `0x35`, consuming
absolute `RaceData/CompetitorN/CarID`. Its three ID26-only wrappers preserve
the original lookup for all other IDs. No global `gaLocal` change or donor-ID
remap is used.

## Historical deployment correction

The first lock-art/control test used a runtime Root without the generated
VehicleSelect scene, so that observation did not evaluate the corrected XML.
The package staging and verification fix is preserved in
`runtime-correction-2.md`. A later corrected-Root run confirmed locked art,
disabled acceptance, and natural unlock. This deployment history is not a
current blocker.

## Scope boundary

No human split-screen Race Details test is claimed; those two paths are
statically covered. Challenge and Trophy/unlock-reward consumers were not
changed or qualified for ID26. Audio, AI pool eligibility, catalog ordering,
ID27+, T2 expansion, and generic SDK behavior remain outside G.1.
