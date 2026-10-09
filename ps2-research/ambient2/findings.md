# PS2-AMBIENT2 — BirdManager

**COMPLETE for the principal static/executable flying-bird chain. Independent runtime validation: NOT_PERFORMED.** Ground-population activation, actual registry contents/cadence and live frame/VU evidence remain open.

The highest-value finding is a small procedural flying-sprite system. `FlightList` contains possible spawn origins; it is neither a spline nor a population of authored birds. A burst shares an origin, then each `gaAnimals_FlyBird` obtains independent random motion. `gaImageBankSwitcher` controls three wing-image keys separately. The ordinary world PSB renderer supplies a Y-locked camera-facing basis and submits a textured quad.

| Finding | Evidence |
|---|---|
| 36 managers; 542 FlightList points, 55 MillList points | All 36 named paired RaceTest resources re-extracted through canonical PackFS; CONFIRMED_BY_BYTES |
| Manager default pool capacity16, optional `Animals/MaxBirds` override | `1ae8b8`, `1af1c0`, `1af460`; CONFIRMED_BY_EXE; effective live value UNKNOWN |
| Original spawn, RNG and flight update recovered | `1afa20`, `1b06d8`, `1b0a40`, `1b0e68`, `1b0f88`, `1d5df0`; CONFIRMED_BY_EXE |
| Actual carrier translation, visual copy and bank selection connected | `1b0e68` → entity+50; `1b0508` → entity+4c; `1b0410`; CONFIRMED_BY_EXE |
| BurdyBrown/White PSB/GXI, four alternative quads per bank | Original banks and loader/consumer chain; CONFIRMED_BY_BOTH |
| Wing keys0/1/2 advance every five owner invocations; ground key3 | `1b0410`, `1b1770`, `1b17e8`, `1b1838`; CONFIRMED_BY_BOTH |
| Ordinary sprite mode8; alpha blending enabled, alpha test disabled, depth writes masked | `3376c0` → `312610`; decoded original GS masks; CONFIRMED_BY_EXE |
| CPU cache → REF/UNPACK/MSCAL0xf → DMA CALL → VIF1 | Fresh PSB producer/cache dispatch plus established shared helpers; CONFIRMED_BY_EXE |

Two significant original-code traps were found. Manager update `1af330` requires **both** resolved list pointers, while 26 canonical course XMLs lack a local MillList declaration. The lookup itself returns NULL for missing registry entries; actual registry retention or other registration must be captured before asserting inactivity in those races. Config `1af0b0` calls Boolean **writer** `1e2b98` for `Bird Brown`, leaving a freshly constructed manager's +94 at1 even when the first authored property says False. Duplicate authored properties remain in the inventory.

No neighboring-bird steering, route interpolation or terrain/obstacle query occurs in the traced FlyBird path. This is a bounded conclusion about that controller, not the whole game's animal systems. Miller's plane-walking code exists, but its normal population producer is not reached from the selected manager update.

Read [source semantics](bird-source-inventory.md), [ownership/spawning](manager-lifecycle.md), [flight equations](flight-motion.md), [sprite/orientation](orientation-and-animation.md), [render contract](draw-pipeline.md), [case/PC comparison](course-case-studies.md), [validation](validation.md) and [closeout report](final-report.md). JSON contracts retain exact hashes, addresses, fields and short original instruction probes; larger original-data artifacts remain ignored.
