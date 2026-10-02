# R5V-F.2c determinism status

Cook A is frozen as three immutable DX files under research-output/r5v_f_2b/cook-a/cache_snapshot/DataGx/Vehicles/Mercedes, with hashes and source evidence in cook-a/hashes.json. The set combines the earlier complete cook and the later car/wheel cook. The later session loaded complete.dx from cache, so it was not a three-role recook.

The current runtime-cook DX files are being cleared after snapshot verification so the next human run starts without complete.dx, car.dx or wheel.dx. GXM, GXI, DXT, TXT source, Data.sma and the candidate runtime remain in place. Cook B instructions are in research-output/r5v_f_2b/COOK_B_INSTRUCTIONS.txt.

Cook B is WAITING_FOR_HUMAN. After a fresh log proves all three GXM reads, model builds, saves and reloads, compare SHA-256 for each role against hashes.json. If any differ, run a structural and field-level diff before classifying determinism.

Cook A's render outputs and texture closure pass. The authentic car tag101 has a bounded auxiliary secondary-descriptor difference from legacy rev127. This remains a semantic collision limitation and prevents final package acceptance; Cook B is still useful to test whether the retail build reproduces the current output deterministically.
