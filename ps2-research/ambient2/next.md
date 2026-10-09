# Next research decision

1. **Authored or procedural?** Mixed: authored potential origins/configuration and sprite frames; procedurally triggered pools, independently randomized flight and a separate image-key animation controller.
2. **542 points versus population?** 542 FlightList origin records across36 courses, not birds. Default allocation16 can be overridden; active/submitted/visible counts require runtime state. Another55 milling points have a separately bounded dormant activation path.
3. **Can movement be reproduced?** The original main flight equation, operation order and RNG are specified and evaluated. Exact race reproduction additionally needs global RNG interleaving, owner/list registry and cadence; PS2 FPU parity is not claimed.
4. **Flocking?** No neighbor/leader steering in the traced flight chain. Bursts share an origin, then controllers vary independently.
5. **Animation ownership?** Separate `gaImageBankSwitcher` slot1; key0/1/2 cycle every five invocations. Ground image3 is distinct.
6. **New PC assets?** Proven PS2 Burdy sprite banks/atlases are available; no positive PC counterpart in the bounded scan. Future conversion/quad representation is likely needed, with PC absence still bounded.
7. **New PC controller?** A future controller/spawn manager and course metadata input are needed; ordinary final draw wrapping cannot supply this behavior by itself. No implementation has begun.
8. **Ambient systems sufficiently understood?** AMBIENT1 spline ownership and AMBIENT2 main bird flight are technically strong static candidates. Grounded-bird activation, live registry/cadence and rigid dressing remain unresolved; no claim of a complete ambient engine.
9. **Broaden all36 geometry now?** The GEOM1 bridge is useful for later expansion, but another unstudied behavior family provides greater breadth at the current survey stage. This is a priority decision, not a rejection of GEOM2's usefulness.
10. **One highest-value next phase:** **PS2-RIGID1 — bounded tumbleweed/haybale instance ownership and actual rigid update→world-transform path.** It addresses a separate observed course-content mechanism, clarifies standalone-versus-baked duplication and future dynamic content requirements. Begin with authored instances and exact executable consumers; do not assume common physics or visible counts.

This is the sole recommendation. No RIGID1, runtime closeout, GEOM2 or PC port is started in this phase.
