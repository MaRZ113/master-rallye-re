# R5V-G.1 finalization validation

## Human runtime evidence recorded

The corrected-root Vehicle Select test is complete. The capture pair
`20261006-150942_merc-locked` and `20261006-151258_merc-unlocked` reports the
active package Root and exact preceding G.1 executable SHA. Their raw dump
SHA256 values match the Observatory metadata.

* Locked state: `T1CupCar1=False`; cheats false; `CarModel=-1`; manufacturer
  `CAR LOCKED`; model/reason `UNLOCK BY WINNING 2 T1 CUPS`; `UI/Enabled=False`.
  The human saw locked slot art and confirmed normal accept could not commit
  ID26 or leave Vehicle Select.
* Natural unlock: `T1CupCar1=True`; cheats false; `CarModel=26`; manufacturer
  `MERCEDES`; model `ML-320`; `UI/Enabled=True`. The human confirms ID26 became
  selectable after meeting the T1 Cup condition.
* The effective Root in both captures is
  `.research-output/vehicles/unlock/runtime-package/`. The exact correction
  overlay was installed there and its prelaunch SHA was verified. This closes
  the earlier wrong-Root deployment failure; no deeper AI/commit-handler RE was
  needed.

The older pre-fix Race Details captures remain evidence of the original defect:
both Master Rallye and Rallye Cup showed `GALOCAL UNKNOWN` while the absolute
participant ID was 26. The shared producer is now traced to `FUN_0047C080` and
group `0x35`, with the selector read from `RaceData/CompetitorN/CarID`.

## Static candidate and package verification

* Deterministic build verification passed from pristine retail source
  `bf8aef32407eb6552c05045b8abef149f32983cedd9503b865069b444c5f96b4`.
* Final candidate SHA256: `722d1a59a9c11cb0c181751c17674e6a04587e2c7b3b8c225c2e93754a438da7`,
  size 3,121,214 bytes, 78 operations. The three new Race Details hooks are
  `0x0047C0F5`, `0x0047C181`, and `0x0047C200`; expected original bytes at each
  site are `506a358bceff570c`.
* The final hook returns `MERCEDES ML-320` only for ID26 and preserves the
  original group-`0x35` lookup for all other IDs. The physical vehicle record,
  CarID, class, class mapping, assets, and race family are unchanged.
* Overlay deterministic rebuild verification passed; output SHA256 remains
  `6cdf398b892dbe01d2a1258030d2785e568cd993e4cf01d9dc4378ae9207341d`.
* The package updater installed the final EXE and updated only the package
  manifest. It preserves runtime-generated PlayerState/options files. The
  package contains 145 pinned payload files plus the candidate, scene, and
  package manifest; post-install verification passes with explicit
  `--allow-runtime-state`.

## Automated checks

* Synthetic suite (`PYTHONPATH=src python -m unittest discover -s tests/synthetic -v`):
  **279 passed, 0 failed, 0 skipped**.
* Race Details patcher/control-flow tests: **14 passed**.
* Runtime-package tests: **9 passed**.
* `python -m compileall src tools tests`: passed.
* Candidate `--verify-existing`: passed; exact retail source, generated EXE,
  manifest, and binary diff match the deterministic rebuild.
* Vehicle Select overlay `--verify-existing`: passed.
* Final runtime package verification: passed; exact candidate and scene hashes
  match the pinned manifest.
* JSON evidence files parse; `git diff --check`: passed.

## Remaining runtime gate

The final candidate has not yet been human-tested on Race Details. Required
checks are the visible Mercedes identity in Master Rallye and Rallye Cup, one
unchanged stock ID0 display, and a short ID26 race regression. Broker values
can confirm state but cannot prove visible rendering. No full stage/results/
frontend-return lifecycle is claimed. G.1 remains open; catalog/ordering has
not started.
