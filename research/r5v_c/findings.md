# R5V-C: duplicate-Astero retail slot25 candidate

**Automated candidate READY for human P0; runtime validation WAITING FOR HUMAN.** The experimental copy is under ignored .research-output/r5v_c/runtime-test/. Original retail MRallye.exe, Data.sma, XML, DX/DXT, localization, and IDs 0–24 initializer instructions were not replaced. This is not a gameplay success claim.

The supported source is SHA-256 bf8aef32407eb6552c05045b8abef149f32983cedd9503b865069b444c5f96b4; candidate SHA-256 is 672d1945681900f3de5921e7a9032ea6d6e57d5e3fe1b49270e04994520222c2. The patcher is tools/patch_vehicle_slot25.py, with exact operations in patch-plan.json.

Record25 is initialized via retail 0x45A0B0, using class 2, ID25, Astero's four stats 6/6/8/8, unknown/meta 0, owned name Astero and float bits 3D8B1C04/3F092D67/3EF74E40/3F800000. Its temporary string is constructed by retail 0x4D11D0; the initializer deep-copies it and frees the temporary. No record memcpy occurs. Original Astero ID16 remains in its own record.

The class-2 navigation capacity changes 11→12. ID25's unlock case alone is forced true for this experimental copy because index15 maps to Progress/UnlockedCars/Bonus2, which is false in the currently inspected game-local DataGame/PlayerState.xml. No save or progress file was edited. No localization was changed: on the unlocked branch 0x4819B0 requests localization groups 0x33/0x34 with absolute ID25; the resulting displayed text is not statically established. Internal resource name remains Astero regardless of display text.

The R5V-B.2 race actor chooses Race/CarN/CarType only on the Frontend/Active branch; a different branch can use a scene Car Name. That uncertainty is deliberately left for P1 after a P0 pass. A wrong/fallback visual with working ID25 physics would be a partial result, not full slot confirmation. The twelfth scene marker is absent, so P0 may pass with a misplaced/invisible selector marker if ID25, stats and Astero preview are demonstrably reachable and navigation is stable.

**Next gate:** owner tests P0 only and reports FULL PASS, UI-PARTIAL PASS or FAIL. P1 must not begin on an automated result alone. Forklift and tracks remain out of scope.