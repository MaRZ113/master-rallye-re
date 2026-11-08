# Recommended implementation roadmap

This document is a proposal only. No G1-G6 feature implementation is included
in R-MOD3.

| Phase | Scope and order | Gate before proceeding | Relative effort |
|---|---|---|---|
| G1 — Seven-AI stability and duplicates | First locate the failure on the exact published beta or a new isolated candidate. Start with six vs seven restricted T1/T2 on same-class vs outside-class player; retain the Full control only if needed. Do not replace the chooser until the failing instruction identifies the broken owner. | Exception code/EIP/parameters/registers/stack and roster identity before the failing stage; then one repeated-ID full race through Results, replay and cleanup. If seven-AI never repeats a CarID, discard pool exhaustion as the cause. | High, currently evidence-blocked |
| G2 — Forced player car | Implement fixed same-class Quick Race player ID using one prepared identity for menu, preview and Car0. | Select/highlight/name/preview and Race identity match; Retry, return and stock selection regressions pass. | Medium |
| G3 — Randomized player car | Reuse the G2 prepared-player pipeline and sample once at the new-event boundary. | Deterministic test seed; no reroll on Start/Retry; native PlayerType/DriverID/controller unchanged. | Medium-high |
| G4 — Forced AI roster | Add exact per-slot physical IDs at the native new-roster boundary, class derived from registry, native DriverID and participant construction preserved. | Quick Race fixed roster completes; repeated IDs only after G1; then separate campaign and Challenge preview qualification. | High |
| G5 — Forced grid positions | Permute native grid ordinals independent of physical identities. | One course passes movement/clearance, reset/replay and Results; expand by explicit course allowlist. Arbitrary coordinates remain out of scope absent a track-space API. | Medium for permutation; high for qualification |
| G6 — Per-mode opponent counts | Extend Cup/Master/Invitation/Challenge only after each count array, save, scoring, UI and mode rules are audited. Counts freeze at new competition/event creation. | One-step count increase per mode with stage/save/Resume, Results and restart; Challenge requires authored per-event objective checks. | Very high |

## Dependency reasoning

G1 is a prerequisite for any feature that can force or sample repeated
CarIDs. G2 provides the stable player identity primitive required by G3 and
clarifies precedence for G4. Grid order is a separate axis and can be
qualified independently once participant identity is stable. Mode-specific
counts should remain last: current research has distinct builders and
persistent state for Cup, Invitation and Master Rallye, while Challenge is
authored. A global engine slot ceiling does not make those modes count-safe.

The order can be adjusted only after new native/runtime evidence changes these
dependencies. Start each follow-on phase with exact candidate and clean
control hashes; use the existing published beta as an immutable reference.

## Release safety gates

- Never alter the v0.1.0-beta.1 tag/asset as an implementation shortcut.
- Keep the first prototype stock-only and run with no Vehicle SDK.
- Use one operation manifest/installer; reject overlap, wrong build and
  inactive/unmaterializable physical IDs before native writes.
- Maintain a feature-disabled passthrough path with original ABI/instructions.
- Treat synthetic tests as code evidence only; each new runtime capability
  needs a labelled human/gameplay result.
