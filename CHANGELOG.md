# Changelog

## v0.1.0-beta.1

- Adds independent Stock, T1, T2, T3, Full, Mixed, and Diverse opponent
  policies for Quick Race, Rallye Cup, Master Rallye, Invitation, and
  Challenge.
- Adds a selectable Quick Race ceiling of up to five AI in the default
  configuration.
- Preserves native roster generation and persistence for Cup and Master
  Rallye events.
- Keeps Challenge Preview synchronized with the opponent used in the race.
- Supports live policy changes at the next new roster boundary.
- Uses the original retail executable without modifying it and works alongside
  the existing graphical `d3d8.dll` proxy.

This beta has a known instability at seven AI with some T1/T2 player-car
setups. Compatibility is limited to the exact executable build documented in
`docs/COMPATIBILITY.md`.
