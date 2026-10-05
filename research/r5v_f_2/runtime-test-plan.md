# Mercedes runtime plan — final P0/P1 handoff

The final `mercedes-final` profile and isolated retail package are prepared. **P0 is waiting for a human run; P1 is gated on P0 PASS.**

Use only `research-output/r5v_f_2e/runtime/MRallye.exe` with that directory as the working directory. Its exact SHA-256 and the complete P0/P1 checklist are in [R5V-F.2e runtime-test plan](../r5v_f_2e/runtime-test-plan.md). Start DebugView first and store logs under `research-output/r5v_f_2e/logs/`.

Prior cache-only portability and collision/damage runtime success are reported by the supplied R5V-F.2e prompt. The local tracked R5V-F.2d cache manifest still records a waiting human gate and no corresponding log was available; these earlier results are recorded as owner-reported, not re-verified here. The exact final candidate has not yet passed P0 or P1.

P0 checks T1/T2/T3 capacities, ID26 identity/name, model/textures, frame4 art, stats, navigation, ID0/ID25 regression, and Quick Race pre-race text. Stop before entering a race. Only after P0 PASS run offline P1 for cache loads, normal driving/physics, collision/damage, camera/HUD/marker, stage completion/results, and return to menu. Glass breakage is not required for this old model.
