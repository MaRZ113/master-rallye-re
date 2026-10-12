# R-CAM1 — Freecam on all RaceTest courses

## Result

The camera certificate now admits structurally verified `RaceTest/<course>` roots instead of requiring the literal `RaceTest/France1` name. This makes the existing Freecam path available to other supported RaceTest tracks while preserving the existing live proof requirements. It does not grant camera access from a course name alone.

The accepted root must still be the completed root job, have a matching `DataScene/RaceTest/<course>.xml` source, use the native success flags `(1, 1)`, and belong to the current race generation and owner. The existing offline-context, unique live RaceLimits owner, participant-state, single-camera identity, render-thread, and hook-ownership checks remain in the certificate and admission path. Non-RaceTest scenes, malformed course tokens, mismatched scene/source pairs, attract/replay/network contexts, and uncertain live ownership remain fail-closed.

The live certificate now carries the validated course ID. Camera bookmarks are stored per course: France1 retains the existing `camera-bookmarks.json` location, while other courses use `camera-bookmarks-<lowercase-course-token>.json`. Bookmark contents are checked against the active course so one track cannot load another track's camera poses.

## Scope by feature

| Feature | Course scope after this change | Gate |
|---|---|---|
| Freecam activation, movement, mouse look, roll, auto-level, cinematic FOV | Structurally verified `RaceTest/<course>` | Existing live camera/race/pause/focus admission |
| Camera bookmarks | Per verified RaceTest course | Course-bound file identity and live certificate |
| Gameplay FOV and synchronized camera/frustum path | Structurally verified `RaceTest/<course>` | Existing camera certificate and projection scope |
| HUD race-scene classification | RaceTest root plus its exact supported HUD child | Existing owner/job relationship; frontend remains separate |
| Road Preview | France1 only | Published physics-probe context is enabled only for a France1 certificate; route remains the 448-marker France1 route |
| Road Teleport | France1 only | Same France1 context plus existing paused/live-owner/road-target checks |
| Renderer-wide display, AF, MSAA and device features | No per-course restriction found in the reviewed production paths | Device/configuration gates |

Road Preview and Road Teleport intentionally retain their France1 restriction. The camera certificate's broader course support is not passed through to their physics observer: non-France1 certificates publish an invalid road context, and the teleport arm path also checks the explicit France1 predicate.

## Evidence and limits

The current production code's previous hard stop was `RaceEpoch::course_identity_verified()`, which compared the root scene and source to literal France1 strings. The production helper already validated the native root-job lifecycle and scene/source shape, so the certificate now reuses that validator for a safe course token rather than weakening the other checks.

The runtime capture `session-20261012-080732-30436.jsonl` contains an Italy3 state where the matching `RaceTest/Italy3` / `DataScene/RaceTest/Italy3.xml` root had flags `(1, 1)`, a unique live owner, valid participant states, one camera, and a supported offline context. The old result was `supported_course_job_not_verified`; this isolates the former France1 string comparison as the rejection. That capture is structural observer evidence, not proof that a human-operated Freecam flight on Italy3 has passed.

Synthetic native tests now exercise Italy3 and mixed-case course IDs, and reject path traversal and scene/source mismatches. Runtime acceptance remains to be checked on representative tracks, especially one track other than France1, plus a replay/Attract negative case. No Road Preview or Teleport behavior was expanded.

## Changed production surfaces

- `race_epoch.cpp`: general RaceTest root identity and course ID on the live certificate.
- `game_fov.cpp`: per-course bookmark loading and storage; France1-only road context and more precise teleport rejection diagnostics.
- `camera_bookmarks.cpp`: safe course-bound persistence with France1 filename compatibility.
- Tests: generic course certification, France1 road gate, per-course bookmark identity and path isolation.

\n