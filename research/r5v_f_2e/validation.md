# R5V-F.2e static validation

## Candidate and package

- Clean retail executable SHA-256: `bf8aef32407eb6552c05045b8abef149f32983cedd9503b865069b444c5f96b4`.
- Final isolated candidate SHA-256: `1fb0a1f1ba02cd05fa25f0c94558cf1b281fd12affcdc37bb3c1ca538e6c65af`.
- Deterministic rebuild and stored patch manifest/diff: PASS; 72 operations; 617-byte code-cave payload.
- Candidate `Data.sma` SHA-256: `b14a6e7e4cc93758114fa88afdf3221778c507b61abbb6b6de37e62e4c3b755ca`.
- Source archive SHA-256: `03c2b52d451b378c7ec634132ebfab706616e33c57fea2985b83db66d3fd4b2f`.
- Archive member comparison: 7,595 source file members retained; 28 Mercedes asset members added; no removals; only VehicleSelect scene changed.
- Scene overlay SHA-256: `83006b28f88ea513c5aca768b68bf16468c834f8f9242dff18b19442eab7a756`.
- Mercedes payload: 28 files, 3 revision-135 DX and 25 DXT; no GXM/GXI/TXT.
- Modern inspection: all three DX roles parsed, 69 bindings resolved, zero unresolved.
- Cook A/B determinism: PASS for these exact Mercedes sources and retail build; not generalized to arbitrary GXM or builds.
- Retail Mercedes physics schema: PASS / COMPATIBLE; 144 values, 120/120 fixed paths, 6 gears, 6 torque entries, 13 Player1 overlay fields. Runtime physics remains untested for the final candidate.

## Registry and profile checks

- Physical registry capacity 27; record stride `0x34`; record26 begins at registry offset `0x54C`.
- T1=8, T2=7, T3=12; local7 ↔ ID26.
- ID26 has Mercedes internal/runtime, model, wheel, and physics-family values; stats 4/3/6/5; SmallCarSheet fallback9; red custom marker; test-only unlock.
- ID0 is not modified by a profile write; ID25 is explicitly initialized and retains Trooper identity.
- Vehicle Select adds T1_Car8 image-bank index3 (historic frame4); T3_Car12 remains present.
- Direct display wrappers preserve stock group lookups for IDs other than 26 and retain physical ID26.

## Tests

`PYTHONPATH=src python -m unittest discover -s tests\synthetic -v`: **PASS, 240 tests**.

The final-profile regression tests cover the sparse map, class counts, stats field order, display strings, art index, fallback fields, family metadata, no-donor identity, and both wrapper branches/resume addresses. These tests and static parsers do not substitute for game runtime.

## Later owner runtime report

- Vehicle Select, Mercedes preview/textures, stats and short-race core gameplay: **OWNER-REPORTED PASS** for the F.2e hash above.
- Three paired Broker snapshots confirm the separate Race Options `0x33` manufacturer and `0x34` vehicle-name failures, plus the unchanged physical ID26 in active race.
- Full stage/results/return: **NOT CLAIMED** for this exact candidate.
- Race Options identity handoff: **SUPERSEDED** by R5V-F.2f; see `../r5v_f_2f/validation.md` and `runtime-handoff.md`.
