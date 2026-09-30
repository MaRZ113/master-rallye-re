# Trooper ID25 runtime test plan

## Owner-reported P0/P1 result

The supplied R5V-E0.1 master prompt records P0 = FULL PASS and P1 = FULL PASS
for the Trooper ID25 candidate. The owner reports selection in T3, Trooper
preview/race/wheel resources, physics, collision and damage, full-stage
completion, Race Results, return to menu, and no replacement of IDs 0–24.
The exact tested executable hash, raw debug log, and screenshots were not
supplied. This is an owner-reported result, not an independently repeated
runtime test by this research run.

The report also records the independent frontend observations: display label
`STEEL MONKEYS FORKLIFT`, Astero-derived stats, missing Vehicle Select icon,
and Astero race 1P/progress/Race Results icons. These identity layers are
investigated separately in R5V-E0.1.

## P1 candidate

Candidate directory: `.research-output/r5v_e0/runtime-test/`.

- Executable: `MRallye_slot25_trooper_test.exe`
- Executable SHA-256: `3022bdc6eb07d1e388f9c8ef693b83ce1c20c12c2c1a62719aad1cc59a1b1f13`
- Overlay: `DataGx/Vehicles/Trooper/` (car, complete, wheel, and 24 DXT files)
- Retail source executable SHA-256: `bf8aef32407eb6552c05045b8abef149f32983cedd9503b865069b444c5f96b4`
- Physics: retail `Vehicles/Trooper`; collision: authentic Trooper tag101
- Automated gates: DX conversion, dependency resolution, physics schema, and
  collision structural checks all pass.

The active installation root was read-only checked on 2026-09-30; it had no
loose `DataGx/Vehicles/Trooper` directory at that time. Its local `Data.sma`
hash is `b181590a1c4fc31ad117d677728c632a6c684e1d28b2e242841e7aa5653d6cc2`,
different from the clean corpus archive used to build the candidate
(`03c2b52d451b378c7ec634132ebfab706616e33c57fea2985b83db66d3fd4b2f`). The
two archives contain byte-identical `vehicles.xml` and `Modifications.xml`
members, including Trooper physics. The local archive has extra `Trooper1`
model members; the new overlay uses the separate `Trooper` runtime folder.
The candidate bundle does not modify either archive or the original
executable.

## P1 test procedure retained for reproducibility

1. Close the game. Keep `MRallye.exe` and `Data.sma` unchanged. Copy the
   candidate executable to the installation root under the distinct name
   `MRallye_slot25_trooper_test.exe` and launch that copy from the installation
   root.
2. Copy the bundle's `DataGx/Vehicles/Trooper` folder to the matching loose
   path beside the retail `Data.sma`. If a Trooper folder now exists, preserve
   it first and compare it with this bundle before changing any files.
3. Select ID25/T3 slot 12 and start a simple Practice or Quick Race. Preserve
   debug output around `Vehicles/Trooper/car.dx`, `wheel.dx`, DXT, and physics
   configuration loads.
4. Check the body and all four wheels, textures, acceleration, braking,
   steering, suspension, wheel placement, collision, camera, and damage.
   Drive a meaningful portion of the stage; if stable, finish the stage,
   reach Race Results, return to the frontend, and confirm original vehicles
   remain usable.
5. Close the game before cleanup. Remove only the distinct candidate
   executable and the newly added Trooper loose folder. Restore any folder
   preserved in step 2.

The owner reports `P1 FULL PASS` for the listed behaviors. Automated
validation did not launch the game, and the exact runtime candidate hash was
not provided. Keep that provenance distinction when reusing this procedure.
