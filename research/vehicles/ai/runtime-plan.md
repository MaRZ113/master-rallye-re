# R5V-H.0 runtime handoff — corrected forced ID26 proof

## Current gate

**WAITING_FOR_CORRECTED_RUNTIME.** The first human run failed: the G.1 locked
thumbnail/commit behavior regressed in the test environment, and Car1 was not
observed as ID26. That run did not carry enough provenance to separate a
resource-root mismatch from a hook guard miss. Preserve it in
[runtime-results.md](runtime-results.md); do not reuse its candidate or handoff.

The static pool map remains `CONFIRMED_BY_EXE`. Natural T1 pool inclusion is
still **NOT STARTED**.

## Exact corrected package

The candidate was deterministically rebuilt from:

* pristine retail SHA256: `bf8aef32407eb6552c05045b8abef149f32983cedd9503b865069b444c5f96b4`
* G.1 intermediate: `722d1a59a9c11cb0c181751c17674e6a04587e2c7b3b8c225c2e93754a438da7`
* G.2 profile-0 intermediate: `636422d0a21b5f75abd3d6233ab0fcbae26cb0dce79c1a8d40d60ad2e8ca488f`
* corrected H candidate SHA256: `dc821c096dea1db00c91ddf41e85cfac1f5369eaf56bd821ed0b904cbe246e13`
* candidate size: 3,121,214 bytes
* patch-manifest SHA256: `68ee11ae153daf4a48974676dd9f1bb31245cb774a4beee53ec165134d537fca`
* mode: `forced-id26-proof`; G.2 `stock_audio_profile_id=0`

Generated paths in this checkout:

* candidate: `.research-output/vehicles/ai/forced-id26-proof/candidate/MRallye.exe`
* complete runtime root: `.research-output/vehicles/ai/forced-id26-proof/runtime-package/`
* prelaunch instructions: `.research-output/vehicles/ai/forced-id26-proof/VERIFY_RUNTIME.txt`

The runtime package was staged from the verified final G.1 package and contains
all profile-pinned retail/G.1 resources, the exact VehicleSelect overlay, and
28 Mercedes runtime asset files. It excludes the source package's generated
PlayerState and backup files. No manual copying from a historical or retired
runtime root is part of this handoff.

Before launch, run this from the `master-rallye-re-vehicles` checkout, using
the project's configured Python:

```powershell
$env:PYTHONPATH = (Resolve-Path 'src').Path
python tools\vehicle_ai_runtime_package.py verify `
  --runtime-root '.research-output\vehicles\ai\forced-id26-proof\runtime-package' `
  --candidate-manifest '.research-output\vehicles\ai\forced-id26-proof\candidate\patch-manifest.json' `
  --retail-exe 'D:\Game\Master Rallye\corpora\retail\MRallye.exe'
if ($LASTEXITCODE -ne 0) { throw 'R5V-H.0 runtime package verification failed' }
```

Proceed only if it prints `EXE PASS`, `ROOT PASS`, `VEHICLESELECT XML PASS`,
`MERCEDES ASSETS PASS`, and `MODE PASS`. The effective paths are the package's
`MRallye.exe`, the package root itself, and
`DataScene/FrontendScreens/VehicleSelect.xml` with SHA256
`6cdf398b892dbe01d2a1258030d2785e568cd993e4cf01d9dc4378ae9207341d`.
Launch `MRallye.exe` with this package directory as the working directory.
The later Observatory raw-dump Root header must equal this exact package root;
the prelaunch verifier cannot assert which directory a running process chose.

## Test sequence

1. Start the verified package with a genuinely fresh profile. Do not copy
   PlayerState files into it.
2. In Vehicle Select, highlight Mercedes ID26. Confirm the locked text, the
   native locked thumbnail, `CarModel=-1`, `UI/Enabled=False`, and that normal
   accept is blocked. **Stop if any check fails; do not enter Quick Race.**
3. Select stock T1 ID0 / Landcruiser.
4. Start an ordinary single-human Quick Race with Opponents=Three, Class=T1,
   and otherwise stock rules.
5. Capture the active race as `h0-forced-id26-ai`. Preserve Observatory source
   metadata with exactly `image_sha256`, `image_path`, and `active_root`.
6. Confirm Broker Car0 remains the human ID0 and Car1 is ID26/T1/Mercedes.
   Human-observe the Mercedes model, wheels/textures, movement under AI,
   progress, collision and damage. One clean race is enough; finishing and
   Results are useful but not required for this proof.

Run the evidence-limited checker against the capture, supplying the exact
absolute paths returned by the verifier:

```powershell
python tools\check_vehicle_ai_runtime.py '<capture.json>' `
  --expected-exe-sha256 dc821c096dea1db00c91ddf41e85cfac1f5369eaf56bd821ed0b904cbe246e13 `
  --expected-image-path '<verified-root>\MRallye.exe' `
  --expected-active-root '<verified-root>'
```

The checker rejects missing or mismatched EXE hash, image path, or active Root
as `RUNTIME_PACKAGE_MISMATCH`. A correct package with a non-ID26 Car1 is
`FORCED_ID26_NOT_OBSERVED`. Broker agreement is at most
`HUMAN_AI_CONFIRMATION_REQUIRED`; it does not establish visible rendering,
AI behavior, physics, collision, damage, or progression by itself.

Expected race state: four total participants, one human; Car0 ID0/T1; Car1
ID26/T1/Mercedes and AI; Car2/Car3 distinct stock T1 AI IDs 1–6. Their exact
DriverIDs are not constrained. The corrected hook does not require Car0 ID0,
but ID0 remains the controlled human test player.

## Stop rule

If the package verifier or fresh-profile locked-state canary fails, stop and
report the package/root evidence. If both pass but Car1 is not ID26, stop at
the publication seam and gather focused runtime diagnostics. Do not modify the
natural AI pool, add ID26 to a roster, or continue to R5V-H.1 until this forced
proof receives a human pass.
