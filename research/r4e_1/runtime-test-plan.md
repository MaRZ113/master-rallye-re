# R4E.1 human runtime test plan

Use one candidate at a time. Both files are named `car.dx` and belong to `DataGx/Vehicles/Astero/`. The ignored package is `.research-output/r4e_1/runtime-tests/`. The installed/unpacked Astero source currently contains the old E2 probe; these candidates were built from the protected original backup matching R4E provenance. Compare against that original baseline and restore your test tree after each run. No Data.sma is included.

## N1: all-normal +90-degree rotation

Package only `N1_normal_rotation/car.dx` using the runtime-confirmed full-tree Python SMA workflow. Keep Reflections ON; load Astero in a race. Inspect chromebar/bullbar and chrome while changing the camera angle. Record: game and car load, chrome geometry intact, reflection/shading clearly altered, change follows edited surface, unexpected artifacts.

A clear localized difference confirms normal writing. No clear difference remains **INCONCLUSIVE** and calls for a separate all-constant-normal probe; that fallback has not been generated. Crash or corruption is a failure requiring investigation.

## M1: environment feature bit off

Package only `M1_env_disable/car.dx`. Keep Reflections ON; compare body draw 7 against original. The `acamo64b-tga` primary/livery texture should remain while this draw's whitepaint environment contribution disappears or changes. Compare chrome and other untouched reflective draws. Record: game and car load, primary texture intact, targeted reflection removed, unrelated reflections unaffected, artifacts.

Only a targeted reflection change confirms the feature-bit writer. No change calls for a narrow field trace; unrelated changes call for scope investigation.

If both N1 and M1 pass, freeze the same-topology vehicle SDK v1 baseline and recommend R4F. If N1 remains inconclusive, prepare the constant-normal fallback. If M1 fails, investigate only the environment field. Neither probe is runtime-confirmed at package generation.
