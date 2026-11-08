# R-MOD1 — Randomizer & AI Extender

R-MOD1 is a standalone stock-vehicle mod with two independent controls: the
Randomizer selects AI vehicle policy, and the Opponent Extender exposes the
native Quick Race selector from one through seven AI. It does not require the
Vehicle SDK, addon manifests, addon resources or Observatory. The original
retail executable stays byte-identical on disk; launch uses the external
suspended-process launcher. A graphical `d3d8.dll` is left untouched.

## Current research checkpoints

R-MOD1-F has three separately reviewable candidates. Each later candidate
contains the earlier checkpoint's behavior, but each is a distinct package and
must be human-tested on its own before its added mode scope is called a runtime
pass:

| Checkpoint | Candidate | Scope | Native operations | Evidence status |
|---|---|---|---:|---|
| F1 | `first-integrated-candidate-v14-f1-r3` | ConfigVersion=2; strict live policy reload at fresh Quick Race roster generation | 7 | Static and package verification passed; human test pending |
| F2 | `first-integrated-candidate-v15-f2` | F1 plus new Rallye Cup, Invitation and Master Rallye roster generation owners | 13 | Static and package verification passed; human test pending |
| F3 | `first-integrated-candidate-v16-f3` | F2 plus synchronized Challenge preview/race opponent identity | 17 | Static and package verification passed; human test pending |

They are not merged into one release candidate. See [status](status.md),
[runtime handoff](runtime-handoff.md), [architecture](architecture.md), and
[validation report](validation-report.md). Exact manifests and operation plans
are recorded as `candidate-v14-f1-manifest.json`,
`candidate-v15-f2-manifest.json`, `candidate-v16-f3-manifest.json` and their
corresponding `native-patch-plan-*-f*.json` files.

The exact supported retail build is PE32/I386, 3,121,214 bytes,
SHA256 `bf8aef32407eb6552c05045b8abef149f32983cedd9503b865069b444c5f96b4`.
Unknown builds fail closed. All three checkpoint plans are generated from
retail preimages, have no overlapping image operations, and passed package
verification plus Windows suspended-process preflight before native writes.
The retail EXE is not included in any candidate.

## Feature and evidence boundaries

F1 policy reload applies only when a new Quick Race roster is generated. A
validated policy and duplicate setting are snapshotted for the whole roster;
invalid or changing INI content keeps the last valid snapshot. The Quick Race
participant-count subsystem is startup-scoped and remains separate from class
randomization.

F2 adds selectors only at the audited new-roster owners. Existing Cup and
Invitation stage rosters and saved Master Rallye rosters are reused; no stage,
resume or load reroll hook is added. F3 chooses one absolute Challenge
opponent identity for both preview and race construction, holds it while the
preview is visible, and clears it on Back/reentry. Stock remains the authored
Challenge matchup.

The original chooser retains physical CarID, DriverID, controller and
participant ownership. Extended five-to-eight total participant behavior is
not newly qualified by F1/F2/F3. Historical v11 four-AI runtime confirmation
remains limited to its exact candidate. Historical R-AI mode tests are not
runtime proof for these new packages. Course clearance and repeated-ID race
lifecycle remain separate human qualification gates.

## Build and verify

With the full checkout, MSVC x86/x64 Build Tools and the exact retail EXE
available outside the repository:

```powershell
$env:PYTHONPATH = 'src;tools'
$env:TEMP = 'D:\CodexScratch'
$env:TMP = 'D:\CodexScratch'
python tools/build_r_mod1_candidate.py --checkpoint f1 `
  --retail-exe 'D:\path\to\MRallye.exe' `
  --output '.research-output\r-mod1\first-integrated-candidate-v14-f1-r3'
python tools/test_r_mod1_candidate.py `
  '.research-output\r-mod1\first-integrated-candidate-v14-f1-r3' `
  --retail-exe 'D:\path\to\MRallye.exe'
```

Use `--checkpoint f2` with output `first-integrated-candidate-v15-f2`, or
`--checkpoint f3` with output `first-integrated-candidate-v16-f3`, to build
the other checkpoints. The builder refuses to overwrite an existing candidate.
The F1/F2/F3 INI examples live in the generated package and correspond to
ConfigVersion=2. Read the matching README and use the matching test sequence;
do not enable modes that are outside that candidate's scope.

The separate DInput proxy is not implemented or supported. Renderer proxy
interoperability remains unqualified. No GitHub beta or arbitrary-N runtime
claim is qualified.

## Review archive

After validation, create a compact source/documentation archive:

```powershell
python tools/build_r_mod1_review.py `
  --date 2026-10-10 `
  --output '.research-output\r-mod1\r-mod1-f-review-2026-10-10.zip'
```

It records included-file SHA256 values, branch, HEAD and Git status. It excludes
game binaries, game assets, raw captures and generated runtime packages.
