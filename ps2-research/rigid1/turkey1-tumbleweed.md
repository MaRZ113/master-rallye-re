# Turkey1 primary tumbleweed case

Canonical `\TNG\DATASCENE\RACETEST\TURKEY1.XML` contains7 `gaAiRigidBody` records in `IContManager`. Representative properties are Mass5, MOI(2,2,2), Trigger Distance15, Casts ShadowTrue. Its model spelling is `misc\objects\tumbleweed\tumblweed`.

The model has96 visual vertices/48 emitted triangles, `bigshrub $shader(treeblend)` and authored convex A8/12, B26/48. The physical representation is not assumed spherical. Both models use the same owner/body/integrator path; direct mass and inertia change acceleration response to contact forces/torques. Gravity acceleration itself is mass independent for isolated m>0.

The selected force callback proves gravity, not wind. Owner update has no random or wind vector operation. Contact can wake a paused body. Additional world-force writers were not exhausted, so the broader question of autonomous environmental tumbleweed motion remains UNKNOWN, rather than being guessed from the name.

A bounded PC scan found no tumbleweed/tumblweed/gaAiRigidBody filename or XML/TXT token counterpart. The absence grade is **NOT_FOUND_IN_SCANNED_PC_CORPUS**. Unnamed or differently named embedded geometry and live PC behavior remain outside that negative result.
