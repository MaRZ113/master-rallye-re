# PC PS2 Port Architecture Handoff

This handoff records the first architecture-only stage. It contains no renderer
source code and makes no runtime claim beyond the status supplied in the
architecture brief.

Included files:

- `README.md` — ownership and current status.
- `docs/architecture.md` — inspected baseline boundary, proposed build
  composition, exact baseline files needing approval, and evidence boundary.
- `docs/pilot1.2-design.md` — France1 `bush01` draw identity, state transaction,
  configuration, lifecycle and test design.
- `validation.md` — checks actually run and limitations.

No proprietary game data, captured frames, renderer binaries, build products,
Course SDK files, or generated geometry are included. No course corpus or
external SDK is required to read this proposal. Native tests and runtime
validation were not run because this stage changes documentation only.

The ordinary renderer build remains the baseline build. The proposed
PS2-enabled build command does not exist yet; creating it depends on approval
for the narrow frozen-baseline integration seam described in
`docs/architecture.md`.
