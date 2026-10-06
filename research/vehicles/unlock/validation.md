# R5V-G.1 runtime correction #2 validation

## Runtime evidence audit

The four supplied JSON captures were parsed, and their raw sidecar SHA256
values were recomputed and matched the JSON metadata. The locked-state checker
classifies the captures as:

* ID3: `LOCK_TEXT_OK`, `BUTTON_LOCKED`, highlighted ID `3`.
* ID26: `LOCK_TEXT_OK`, `BUTTON_NOT_LOCKED`, highlighted ID `26`.
* Master Rallye and Rallye Cup: Race Details name state
  `RACE_DETAILS_NAME_UNKNOWN` with `Race/Car0/CarID=26`.

The human report confirms ID26 was accepted into a race. `selectedCar` is not
used as a commit assertion. The captures' candidate EXE SHA matches the G.1
candidate, while the captured Root had no loose VehicleSelect XML. The prior
thumbnail/button outcome is therefore not a valid runtime evaluation of the
corrected XML.

## Candidate and package

* EXE deterministic rebuild and manifest verification: passed; source SHA256
  `bf8aef32407eb6552c05045b8abef149f32983cedd9503b865069b444c5f96b4`, output
  SHA256 `3346eb00442b88cca3f76f7a65606ca56006c5b981acdbf0ee4ad16412e5b055`,
  3,121,214 bytes, 75 operations.
* VehicleSelect overlay deterministic rebuild and source-restoration audit:
  passed; source SHA256
  `ec7fd6372fe5008b1039eb8e09890ef3b37396dad1581568af439cbb611b58e1`, output
  SHA256 `6cdf398b892dbe01d2a1258030d2785e568cd993e4cf01d9dc4378ae9207341d`.
* Runtime root profile pins the captured `Data.sma`, DataAudio, options,
  qualified Mercedes DX/DXT, and DataVideo file inventories. Staging omits
  `PlayerState.xml` and backup state for a fresh profile.
* Runtime package staging and exact-tree verification: `PASS`; 145 files under
  `.research-output/vehicles/unlock/runtime-package/`. The verifier confirms
  the on-disk candidate and loose scene hashes; a postlaunch Root capture is
  still required to prove the process selected that root.

## Tests

* Synthetic suite: **271 passed, 0 failed, 0 skipped** (`PYTHONPATH=src`).
* Focused runtime-package tests: **6 passed**.
* G.1 unlock/capture checker tests: **16 passed**.
* `python -m compileall src tools tests`: passed.
* Candidate EXE verifier: passed.
* Vehicle Select overlay verifier: passed.
* Runtime package verifier: passed.
* JSON evidence/profile parsing: passed.
* `git diff --check`: passed for the working tree and staged index.

## Runtime boundary

No runtime pass is claimed for the corrected overlay or package. The immediate
human gate is to run the verifier, launch from the printed package root, and
confirm the new capture header reports that same Root before comparing ID3 and
ID26. Do not investigate appended AI/control instantiation or patch Race
Details until that deployment gate is satisfied.
