# Cross-phase consistency review

This is a bounded review of claims relevant to material, geometry, renderer
state and source/runtime boundaries. It does not reopen the other phases.

| Phase | Result retained | Evidence boundary / consistency note |
|---|---|---|
| CDELTA1 | Course/material pairing and source-string inventory | Directive presence is not a draw or object count |
| GRASS1 | Spatial-surface detail and owner/update chain | Spatial triangles do not automatically identify visual strips or visible instances; runtime pending |
| WATER1 | Water material, selected visual source groups and static render contract | Turkey3 unmatched source geometry does not by itself prove visible runtime puddles; no broad draw ordering |
| REFL1 | Vehicle environment-source and reflection contract | Static mechanism evidence remains separate from live texture residency and reflection-frame capture |
| GEOM1 | Source-coordinate comparison and selected surface correspondence | Geometry matches are source-level and must retain LOD/live visibility qualification |
| DRESSING1 | Authored object/group ownership evidence | Mesh/group counts are not live object populations; do not assert instance totals from names |
| TREEBLEND1 | `tree` vs `treeblend` handler/register/queue distinctions | PS2 executable evidence is from prior canonical ELF analysis; runtime VU residency and live GS state remain unknown |
| AMBIENT1 | `gaEntitySpline` owner/update/world-matrix chain | Static executable chain does not equal captured in-race pose |
| AMBIENT2 | Bird manager/spawn/flight path | Candidate spawn data and owner logic do not prove live counts/trajectories |
| RIGID1 | Authored rigid props and physics ownership leads | Do not infer visible draw population or final course placement from declarations |
| PC port overlay | Deterministic two-build overlay, one proxy per output, Stock default | Build/test evidence is not game visual confirmation; this audit did not modify/rebuild the overlay |

No new contradiction was found that justified changing another phase's source
or conclusion. Unknown active subsets, live draw identity, runtime camera/LOD,
and inherited state remain explicit limits across the source and renderer
studies.
