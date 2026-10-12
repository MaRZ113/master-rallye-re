# Next experiment

## Recommendation: targeted PC per-pixel overdraw capture

The next highest-value experiment is one bounded PC frame inspection of the already verified France1 target, capturing the target bush's color/depth contribution immediately after its draw and after subsequent candidate draws. Keep the same executable, proxy, resource generations, camera bookmark and Free Camera pose; use the diagnostic mode matrix only to compare the target's native state behavior.

Mode 3 reproduces the disappearance while changing only `ZWRITEENABLE`, which isolates depth-write state as sufficient for the observed symptom. The target is early in the captured frame, so later overdraw is plausible. A per-pixel/depth trace is needed to identify an actual covering draw. If the target contributes and a later draw replaces it, the ordering/overdraw hypothesis gains direct support. If it contributes no color even before later draws, investigate coverage, alpha and depth test inputs first.

This experiment does not claim to validate the PS2 renderer. It should precede a wider renderer redesign or any texture/ordering changes. Keep the original four screenshots and capture the exact selected mode in the log, so a future comparison does not depend on ordinal pairing.
