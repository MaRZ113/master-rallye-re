# R5V-H runtime evidence ledger

## First H attempt — failed, preserved

Classification:

* G.1 locked-state behavior in the H test environment: **REGRESSED**.
* Forced Car1=ID26: **FAIL / NOT OBSERVED**.
* H runtime package provenance: **SUSPECT / UNVERIFIED**.
* Static stock AI-pool mapping: remains **CONFIRMED_BY_EXE**.

Owner-reported observations on the fresh profile:

* ID26 displayed `CAR LOCKED` and `UNLOCK BY WINNING 2 T1 CUPS`.
* The locked thumbnail was blank, ID26 remained committable, and a race could
  be started with the Mercedes player model.
* The Mercedes player model still loaded.
* No forced Mercedes was observed in Car1; opponents looked like normal stock
  compositions.

The tested candidate was SHA256
`688653245b916ae7aae2a8e22fd47e76963f3afb1c23936b47b57bb40c76f0c5`, size
3,121,214 bytes. It was deterministically reproducible from retail -> G.1 ->
G.2 profile 0 -> H. However, the handoff asked the tester to manually replace
the executable in a pre-existing runtime root. It did not provide a coherent
H resource package or runtime-root verifier, so the effective
`VehicleSelect.xml` used by that process is **UNKNOWN**.

The old hook also required Car0 physical ID0. The human report does not include
the actual Car0 ID, so the guard may have silently fallen through if another
T1 vehicle was selected. This is a documented handoff fragility, not a claim
that the human caused the failure. The first attempt does not establish that
the hook itself executed or failed at runtime.

This record is historical and is not a partial pass. The old candidate/handoff
is superseded by H.0.

## Corrected H.0 package — prepared, not runtime tested

The deterministic H.0 candidate is SHA256
`dc821c096dea1db00c91ddf41e85cfac1f5369eaf56bd821ed0b904cbe246e13`, size
3,121,214 bytes. Its patch manifest SHA256 is
`68ee11ae153daf4a48974676dd9f1bb31245cb774a4beee53ec165134d537fca`.

The exact runtime package is under the ignored
`.research-output/vehicles/ai/forced-id26-proof/runtime-package/`. It was
staged from the verified final G.1 runtime package, contains the pinned
VehicleSelect overlay SHA256
`6cdf398b892dbe01d2a1258030d2785e568cd993e4cf01d9dc4378ae9207341d` and 28
profile-verified Mercedes asset files, and excludes copied PlayerState files.
The package verifier returned PASS for EXE, root layout, VehicleSelect XML,
Mercedes assets, mode, and G.2 audio profile 0. This proves on-disk package
composition only; the game has not yet been launched from this corrected root.

The new forced hook guard is Car1/ESI==1, exclusive end slot/EBP==4, and
requested class/T1==0. It does not read player identity, caller return address,
or overwritten exclusion arguments. The selected CarID local is changed after
driver bookkeeping; retail code still publishes CarID 26 and derives CarClass
from the registry. `Race/NumCars`, DriverID, Car0, Car2, and Car3 are not
written by the H hook.

Current status: **WAITING_FOR_CORRECTED_HUMAN_RUNTIME**. Required first check
is the fresh-profile locked-state canary in the exact H package. If it passes,
test a normal T1 ID0 player and capture the active race with source metadata
`image_sha256`, `image_path`, and `active_root`. The checker can establish only
package provenance and Broker-state agreement; visible actor, AI behavior,
physics, collisions, and damage still require human observation.
