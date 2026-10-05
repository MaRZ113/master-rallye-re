# Deferred items after R-AI1.2 closeout

These are design notes, not implementation or runtime claims.

**R-AI1.2a - Challenge Preview Sync**, optional non-blocking polish:
when Challenge policy is not Stock, the frontend preview and actual race must
reference the SAME generated opponent roster. Generate once, preview reads that
identity, race consumes it. Never independently reroll a preview vehicle.
Trace the exact frontend owner separately; preserve rules, objectives and
completion logic. Optional exact authored DriverID preservation is a separate
policy decision, currently NOT IMPLEMENTED / NOT CONFIRMED.

**Original-EXE-unchanged deployment**: removable external loader/module,
exact supported-build checks, unknown builds fail closed. Current research
EXEs are proof infrastructure, not a public binary distribution format.

**R-UI1 - Quick Race Opponent Count UI**: future Four value has engine evidence
for four AI / five total. No UI change here. Five/Six/Seven opponent values must
wait for their own R-AI2.1 participant-capacity proof.

**R-AI2.1 - capacity beyond five**: six/seven/eight/generic-N remain UNKNOWN.
No Car5 actor, higher-count candidate or capacity investigation in this closeout.
