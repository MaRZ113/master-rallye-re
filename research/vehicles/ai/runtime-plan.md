# R5V-H human runtime plan — Stage 1

## Candidate

Use only the forced proof candidate for this first test. It was rebuilt from
the exact pristine retail executable through the closed G.1 and G.2 profile-0
builders:

* Retail source SHA256: `bf8aef32407eb6552c05045b8abef149f32983cedd9503b865069b444c5f96b4`
* G.1 intermediate SHA256: `722d1a59a9c11cb0c181751c17674e6a04587e2c7b3b8c225c2e93754a438da7`
* G.2 profile-0 intermediate SHA256: `636422d0a21b5f75abd3d6233ab0fcbae26cb0dce79c1a8d40d60ad2e8ca488f`
* H candidate: `688653245b916ae7aae2a8e22fd47e76963f3afb1c23936b47b57bb40c76f0c5`
* Size: 3,121,214 bytes
* Candidate: `.research-output/vehicles/ai/forced-id26-proof/MRallye.exe`

Before staging, run from the `master-rallye-re-vehicles` checkout:

```powershell
python tools/build_vehicle_ai_candidate.py `
  '..\corpora\retail\MRallye.exe' `
  '.research-output\vehicles\ai\forced-id26-proof\MRallye.exe' `
  --mode forced-id26-proof --verify-existing
if ($LASTEXITCODE -ne 0) { throw 'R5V-H candidate verification failed' }
```

Use the same isolated runtime install and qualified G.1 Mercedes resource Root
used for the G.2 test. Stage this exact executable into that isolated install;
keep the qualified `DataGx/Vehicles/Mercedes` resources and all other game
data unchanged. Do not launch the candidate from a folder that is not already
a complete working runtime root. Immediately before launch, hash the effective
installed `MRallye.exe` and require the exact H candidate SHA above. Do not use
a general mixed-class randomizer or a participant-count patch.

In PowerShell, replace the example root with the known isolated G.1/G.2 game
install, then verify the staged executable before launch:

```powershell
$runtimeExe = Join-Path '<isolated-runtime-root>' 'MRallye.exe'
$expected = '688653245b916ae7aae2a8e22fd47e76963f3afb1c23936b47b57bb40c76f0c5'
$actual = (Get-FileHash -LiteralPath $runtimeExe -Algorithm SHA256).Hash.ToLowerInvariant()
if ($actual -ne $expected) { throw "Wrong R5V-H candidate: $actual" }
"PASS $actual"
```

Only proceed when the command prints `PASS` and the G.1/G.2 vehicle resource
Root is the already-qualified one. The research EXE itself is at
`.research-output/vehicles/ai/forced-id26-proof/MRallye.exe`; its generated
manifest is beside it. Neither the EXE nor game assets belong in Git.

The research candidate changes no participant count and should work with
either fresh or already-progressed PlayerState because the proof guard bypasses
only AI pool membership; it does not ask the player to select or unlock ID26.
For the cleanest read, choose normal player ID0.

## Test setup

1. Launch the verified H executable in the isolated G.1/G.2 runtime root.
2. Start a normal, single-human Quick Race.
3. Select stock player T1 ID0 / Landcruiser.
4. Keep the stock opponent count at Three, so the normal race has one human and
   three AI. Select any ordinary course and difficulty; do not change race
   rules.
5. Capture the active race as `forced-id26-ai-race`.
6. Confirm one visible Mercedes opponent occupies Car1; it has correct wheels
   and textures, is AI-controlled, drives through normal progress, and behaves
   sensibly in steering, acceleration, braking, collisions, and damage.
7. If practical, finish the race and capture `forced-id26-ai-results`.

## Broker oracle

Run the read-only checker on the active-race JSON:

```powershell
python tools/check_vehicle_ai_runtime.py '<capture.json>' `
  --expected-exe-sha256 688653245b916ae7aae2a8e22fd47e76963f3afb1c23936b47b57bb40c76f0c5
```

Expected state:

* `Race/NumCars=4`, `Race/NumPlayers=1`.
* Car0: ID0, class0/T1, player.
* Car1: ID26, class0/T1, AI, `CarType=Mercedes`, `WheelType=Mercedes`.
* Car2 and Car3: different valid stock T1 IDs 1–6, AI.
* Car1–Car3 use the same observed `PlayerType`, distinct from Car0. The
  checker compares these values rather than assuming a numeric enum.
* Car1 DriverID remains a native selected ID; no specific driver is required.
* The G.2 audio path should select profile0 because the physical CarID is 26;
  this is a supporting hypothesis, not a separate blocking audio gate.

The checker returns only `BROKER_STATE_MATCH_ONLY`. Human observation is still
required for model visibility, AI movement, physics, collisions, damage,
progress, finish, and cleanup.

## Gate

After a human pass, close the forced materialization proof and only then design
the natural T1 pool candidate. A passing forced test does not prove natural
selection. If the AI Mercedes fails to materialize or drive, stop and diagnose
that downstream issue before touching the pool.
