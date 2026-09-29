# R5V-C owner runtime result

**Status: P0 FULL PASS; P1 FULL PASS, as reported by the project owner.** The result was supplied in the R5V-E0 master prompt received on 2026-09-30. The prompt states that the retail debug output showed Astero resources loading for ID25. Raw debug output, screenshots, and a separately dated test log were not included in the repository, so this record preserves the owner's report and does not represent an independent observation by the tooling.

## Reported checks

- P0: ID25 was selected in the frontend and its Astero `complete.dx` preview loaded.
- P1: Quick Race loaded Astero `car.dx` and `wheel.dx`; physics, steering, suspension, collision, damage, breakable glass, and camera behavior were exercised.
- The stage was completed, Race Results was reached, and the game returned to the menu.
- The original Astero remained usable after the test.

The reported runtime candidate is the ignored `.research-output/r5v_c/runtime-test/MRallye_slot25_test.exe`, SHA-256 `672d1945681900f3de5921e7a9032ea6d6e57d5e3fe1b49270e04994520222c2`. The supported retail source hash remains `bf8aef32407eb6552c05045b8abef149f32983cedd9503b865069b444c5f96b4`.

## Scope

This closes the R5V-C duplicate-Astero slot proof as owner-reported runtime evidence. It does not establish that ID25 can load another vehicle family, does not confirm Trooper assets or physics, and does not expand capacity beyond ID25.
