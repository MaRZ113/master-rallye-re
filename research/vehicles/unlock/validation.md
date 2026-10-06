# R5V-G.1 validation

## Final runtime gate passed

The final candidate is the deterministic 78-operation patch of pristine
retail. It preserves the physical ID26 record and adds bounded frontend
presentation and stock-like availability behavior. Final runtime captures
report candidate SHA256
`722d1a59a9c11cb0c181751c17674e6a04587e2c7b3b8c225c2e93754a438da7`, size
3,121,214 bytes, and the staged `runtime-package` Root.

* Locked ID26: fresh progress with cheats false; `CarModel=-1`; native
  `CAR LOCKED` / `UNLOCK BY WINNING 2 T1 CUPS`; locked thumbnail; `UI/Enabled=False`;
  normal accept blocked.
* Naturally unlocked ID26: `T1CupCar1=True`; `CarModel=26`; `MERCEDES` /
  `ML-320`; normal thumbnail and `UI/Enabled=True`.
* Race Details: final Master Rallye and Rallye Cup snapshots both contain
  `MERCEDES ML-320` and preserve `RaceData/Competitor0/CarID=26`,
  `Race/Car0/CarID=26`, and class 0. Their raw sidecars hash-match their JSON
  metadata. Human observation confirms both strings were visibly rendered.
* Stock ID0 Race Details regression: PASS by owner-reported human runtime.
* Full stage and Results on the final candidate: PASS by owner-reported human
  runtime. The available report does not separately claim frontend return.
* No human split-screen Race Details test is claimed; the two split-screen
  hook sites are statically covered. Challenge and Trophy localization remain
  unmodified and unqualified for ID26.

## Candidate and package verification

* Source retail SHA256:
  `bf8aef32407eb6552c05045b8abef149f32983cedd9503b865069b444c5f96b4`.
* Candidate SHA256:
  `722d1a59a9c11cb0c181751c17674e6a04587e2c7b3b8c225c2e93754a438da7`;
  3,121,214 bytes; 78 patch operations.
* Vehicle Select overlay SHA256:
  `6cdf398b892dbe01d2a1258030d2785e568cd993e4cf01d9dc4378ae9207341d`.
* Race Details sites: `0x0047C0F5`, `0x0047C181`, `0x0047C200`.
* The final Root and overlay are pinned by the ignored runtime package manifest.
  The post-capture verifier reported PASS.

## Automated validation

Final closeout verification on 2026-10-06:

* Synthetic suite: **279 passed, 0 failed, 0 skipped**.
* Bounded Race Details wrapper tests: **14 passed** (included in the suite).
* Runtime package tests: **9 passed** (included in the suite).
* `python -m compileall src tools tests`: passed.
* Final candidate deterministic `--verify-existing`: passed.
* Vehicle Select overlay deterministic `--verify-existing`: passed.
* Runtime package verify with `--allow-runtime-state`: passed.
* JSON capture parsing and raw sidecar verification: passed for both final
  captures.
* `git diff --check`: passed at final review.

Historical test logs with earlier fixture errors remain historical; the
current synthetic retail fixture includes the Race Details sites and the
final run above is clean.
