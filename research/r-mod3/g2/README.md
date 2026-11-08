# R-MOD3-G2 — Quick Race player vehicle override

**Status: `READY FOR HUMAN GAMEPLAY TESTING`; no G2 gameplay runtime result is claimed.**

G2 adds an experimental player-vehicle setting to the preserved G1 duplicate-capable runtime. Scope is limited to Quick Race player 0 and stock physical IDs 0–24. `Stock` preserves the game's choice, `Forced` selects one configured stock physical ID, and `Random` selects once when the Quick Race Vehicle Select constructor is entered. AI policy and player policy are independent.

The generated package is `first-integrated-candidate-g2.zip` under the ignored `.research-output/r-mod3/g2/first-integrated-candidate-g2/` directory. It is separate from the published beta and the G1 reference. It contains the x86 `dinput8.dll` proxy, the G2 runtime DLL, INI examples, and a reproducible native patch plan. It contains no retail EXE, `Data.sma`, game assets, or graphical `d3d8.dll`; Vehicle SDK and Observatory are not dependencies. See [runtime-handoff.md](runtime-handoff.md) before testing.

The owner confirmed G1's full eight-participant T2 duplicate race; [the G1 closeout](../g1/README.md) records that evidence boundary. The G1-generated manifest remains historically unchanged. G2 preserves its 17 native image operations and adds only two Quick Race player-car call-site operations.

ConfigVersion 2 retains its prior meanings. ConfigVersion 3 adds a required `[Player]` section; see [configuration-v3.md](configuration-v3.md). Exact native ownership and the currently unresolved manual-navigation behavior are documented in [native-ownership.md](native-ownership.md).

The release gate remains human confirmation that the Vehicle Select display and the race participant use the same selected physical ID, including after navigation, plus the forced/random re-entry checks. Synthetic tests and a valid DLL/package do not establish that gameplay result.
