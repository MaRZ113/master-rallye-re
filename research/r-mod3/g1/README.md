# R-MOD3-G1 — Duplicate Vehicle Support

**Status:** `FULL PASS / CLOSED` by owner runtime confirmation.

G1 addresses one bounded case in the stock-only R-MOD3 Quick Race path: after
the player and earlier AI participants consume every distinct vehicle in a
strict T1/T2 pool, `Duplicates=WhenNeeded` allows the next AI to draw again
from that same class. It leaves race participant construction, physical
CarID/Class/DriverID publication, controller allocation, start-grid placement,
and renderer behavior with their existing native owners.

The candidate is a development package separate from the published
`v0.1.0-beta.1`. It requires the exact supported retail executable and the
existing DirectInput proxy deployment. It contains no game executable,
vehicle assets, Vehicle SDK, addon manifests, Observatory, or course edits.
The original executable and graphical `d3d8.dll` are not modified.

The owner has now confirmed a complete eight-participant T2 race containing
repeated physical CarIDs. Broker evidence reports `Race/NumCars=8`,
`Race/NumPlayers=1`, seven AI, duplicate ID 8 in Car3 and Car7, separate
DriverIDs 6 and 5, all eight participants finished, and eight separate
results. This closes the G1 duplicate-participant lifecycle. The exact runtime
candidate SHA and original capture files were not supplied in this checkout;
the values are recorded as owner-provided closeout evidence, not as a locally
rehash-verified capture set. The separate post-dump/results crash remains an
Observatory unsafe-dump investigation and is not attributed to G1.

The old G1 build manifest and review archive retain their historical
`HUMAN_RUNTIME_PENDING` generation-time labels. They are not rewritten to
backdate the later runtime qualification. See [`validation-report.md`](validation-report.md)
for the closeout boundary.

Challenge Clone Army was investigated only for feasibility. No Challenge
behavior is changed; see [`challenge-clone-army-feasibility.md`](challenge-clone-army-feasibility.md).

