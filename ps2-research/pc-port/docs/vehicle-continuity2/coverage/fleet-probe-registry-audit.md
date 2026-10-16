# Source-only fleet probe registry cross-check

`fleet_probe_registry.hpp` is an audit-only derivation of the existing `car-candidates.json`, not a second runtime registry. Main integration should reuse the more complete `race_fleet_registry.hpp` produced by the fleet asset workstream; do not include both in runtime code.

- 25 paired playable PC families, explicitly excluding Forklift.
- 774 original physical source records, preserving family, resource path, record path, vertex/face counts and exact geometry SHA.
- Every geometry SHA is unique across these 25 families in the supplied source inventory. Repeated OFF/ON geometry within a single family may still exist; this uniqueness does not distinguish material branches, current owner or damaged topology.
- Original source inventory SHA-256: `c82cf0c4136a9d0d4f19dd8827a3d73ceb592769b54a5817a6457dac70675099`.
- Four focused Python tests pass: family coverage/exclusion, every original profile identity, cross-family uniqueness calculation and deterministic generated output.

This source-only metadata does not enable replacement. The proposed observer still requires a live current queue-to-owner join, native selected-tree membership, current VB/IB generations/revisions and WORLD. F10 activation limits and byte/record caps belong to the diagnostic implementation, not this source registry. No proprietary vertices, UV bytes, texture bytes or executable data are embedded here.
