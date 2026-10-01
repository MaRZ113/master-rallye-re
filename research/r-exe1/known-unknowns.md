# Known unknowns and deliberate boundaries

## Resource system

- Per-root search precedence and duplicate archive-name behavior are not known.
- Exact case sensitivity and normalization rules beyond the observed separator rewrite are not known.
- Cache invalidation keys, ownership/lifetime, and all fallback/error paths need further static tracing.
- No claim is made that every asset extension is handled by one central loader.

## XML and brokers

- XML tree grammar and the complete generic XML-to-broker call chain are not reconstructed here; existing parser work covers the course Egg/list path.
- Merge precedence between defaults, scene values, global values, and user/player-state values is unknown.
- Entry offsets are partially observed, not a complete struct definition; scope/type enums beyond observed values remain unknown.
- The exact semantics of `SaveOptions` and `SavePlayerState` are hypotheses until their writer consumers are mapped.

## Graphics and assets

- `UsesAlpha` runtime consumer and exact alpha-test/blend state mapping remain unresolved.
- Texture-stage/environment reflection selection is not fully traced through D3D8 calls.
- No change to Blender material preview semantics is justified by this reconnaissance.

## Vehicle and race

- Vehicle destruction/object ownership, damage manager, wheel/suspension runtime structures, and physics-object factory neighborhood remain partially mapped.
- Existing vehicle registry slot limits stand as previously researched; R-EXE1 does not claim an extra slot.
- Course registry order, mode-specific race participant capacity, and course-selection-to-scene path need further tracing.
- StartArea interpolation, full FinishArea algorithm, tag100, SFL, and most RaceLine meanings remain UNKNOWN.
- Existing R5T-D1 SplitTime0 behavior is specific to its established evidence; no R5T-C conclusion is changed.

## AI, replay, frontend, and persistence

- No general AI steering/speed/overtake/recovery behavior is claimed.
- `LastMarker`, `WrongWay`, `PaceNoteOwner`, `PaceNote`, and `SplitPoint` are unresolved runtime keys; missing direct literal xrefs may reflect dynamic path construction.
- Ghost playback object setup is known, but replay recording, file format, cadence, and camera/replay integration are not.
- Frontend lock filtering and list population mechanisms are not proven generic; five CupSelect buttons do not set a career capacity.
- The actual player save filename/container, load/write entry points, versioning, checksum, and failure behavior remain unknown.

## Development/debug/network/other

- BuildData's callback table owner, UI dispatch, availability and output overwrite scope are unresolved.
- Debug/editor code presence does not establish retail reachability.
- UDP port 22222 is a static listener fact; protocol, host/client roles, mode gating, and maximum peers are unknown.
- A distinct weather controller, particle subsystem architecture, and replay camera system were not confirmed beyond data/class references.
- No confirmed cut content was identified.
