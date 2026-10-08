# J0 validation and evidence

The SDK test suite covers strict manifest semantics, duplicate/reserved IDs,
deterministic automatic allocation, sparse class mapping in both directions,
registry arithmetic, family/resource collision rejection, unlock/audio/AI/
Results policy validation, RGBA initializer byte encoding, evidence-aware
frontend state reporting, deterministic multi-addon output, build-manifest
hash verification, and refusal of incompatible target capabilities.

The I.1 runtime evidence ledger
[`../multislot/i1-runtime-evidence.json`](../multislot/i1-runtime-evidence.json)
records six capture pairs. All raw sidecars were SHA256-checked against the
JSON metadata; every capture identifies the exact candidate SHA above. The
AI capture proves a natural ID27 T2 AI participant because the same candidate
manifest lists ID27 in the dynamic T2 pool and contains no forced participant
override. It does not prove the AI's completed race or finishing position.

## J0 verification record — 2026-10-08

* Complete `tests/synthetic` suite: **382 passed, 0 failed, 0 skipped**.
* Focused addon SDK tests: **14 passed**.
* `python -m compileall -q src tools tests`: **PASS**.
* Draft 2020-12 schema self-check and both example manifests: **PASS**.
* Two-addon `mrtool addon build`: **PASS**, offline-only plan SHA256
  `357d3cf10f32b63af27d28c23a858197d7eedbd0d7ef79e4deb2a63a6b170989`.
* `mrtool addon verify` on that build: **PASS**; `runtime_installable=false`.
* Six I.1 JSON/raw capture pairs: **6/6 SHA256 verified** against their JSON
  metadata; all six identify the same exact candidate EXE.
* Frontend-state checker: A reports stored physical ID27 retained while the
  scene shows Navara/local0; B reports ID27/T2/local7 consistently. It does
  not infer actor loss or automatic commit.
* `git diff --check`: **PASS**.

These automated checks do not promote any new human runtime behavior. The
reference build is a semantic plan and reference metadata, not a game-ready
package.

## Archived derived evidence

The deterministic archive
[`archive/r5v-j0-derived-evidence-2026-10-08.zip`](archive/r5v-j0-derived-evidence-2026-10-08.zip)
contains the I.1 capture ledger, the A/B frontend re-entry fixture, and the
two-addon offline reference plan with its verification manifests. It contains
derived metadata only: no raw Broker dumps, executable, game assets, saves, or
screenshots. `archive-index.json` inside the ZIP lists SHA256 and size for every
payload member; the index itself is excluded to avoid a self-referential hash.
