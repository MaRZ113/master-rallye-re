# Evidence and validation record

## Baselines

The pinned public Randomizer beta is GitHub tag `v0.1.0-beta.1`, commit
`40e96a879d81dbe8fece1af65f8ccec3ec1334fd`, release asset
`MasterRallye-Randomizer-v0.1.0-beta.1.zip`, size 170,004 bytes, SHA256
`11f40dd716998539ed0885b7c4ade4d4601597727ced02a26cd1753b9ce84892`.
It was published at `2026-10-11T01:00:51Z` and is a prerelease beta. The tag
and asset were checked against GitHub during this phase. See
[`published-baseline.json`](published-baseline.json) and the [release
page](https://github.com/MaRZ113/master-rallye-re/releases/tag/v0.1.0-beta.1).

The exact supported retail source image remains `MRallye.exe`, 3,121,214
bytes, SHA256
`bf8aef32407eb6552c05045b8abef149f32983cedd9503b865069b444c5f96b4`.
The local pristine file was hashed during this work. No executable bytes were
written.

The research worktree was `research/r-mod1`, HEAD
`ea3012a1481cf1d2f8ed3401eedc995c96dbcfb9`, already dirty before R-MOD3.
All R-MOD3 files are confined to `research/r-mod3/gameplay-expansion/`;
release/product source, Observatory, Vehicle SDK and retail files were not
changed by this phase.

## Source evidence used

- `research/r-ai1-2/mode-map.json`: exact-retail mode owners, generation
  lifetimes and prior runtime boundaries.
- `research/r-mod1/native-chooser-count-evidence.md` and
  `research/r-mod1/participant-capacity.md`: R-MOD chooser/count ownership,
  seven-AI owner observation and evidence limits.
- `research/r-mod1/native-patch-plan-f3.json`: 17-operation static template,
  existing hook seams and source identity. It explicitly says
  `runtime_qualified=false` and is not treated as a capture of the public DLL.
- `research/r-ai2-1/`: prior six/eight participant runtime lifecycle results
  for their separate fixed-roster candidates; not repeated-CarID evidence.
- `research/general-re/grid8/grid8-audit.json`, `native-grid-formula.md`,
  `findings.md`: 39 registrations, 36 course resources and native grid
  structure. Every course runtime clearance remains `NOT_TESTED`; the
  historical Italy_S4/Track10 start was unsafe/near geometry.
- Ghidra 12.1.4 exports in ignored `scratch_rmod1/ghidra/` for the exact
  retail program: chooser, length, shuffle, driver, Quick Race, Cup, Master,
  Challenge and grid functions. No `ghidra-bridge` callable tool was exposed
  in this session; the existing exact-build exports were inspected directly.
- Vehicle SDK frontend lifecycle documentation was read from the separate
  worktree only. It informed physical-ID/local-ordinal restoration; no SDK
  files were edited.

## Evidence labels

| Claim | Evidence label | Limit |
|---|---|---|
| Public beta tag, release asset identity | `CONFIRMED_BY_CORPUS` / direct release metadata | No package or DLL was changed during R-MOD3. |
| Physical chooser/refill and per-slot native writes | `CONFIRMED_BY_EXE` / `STATICALLY_VERIFIED` | Does not establish safe duplicate-ID gameplay. |
| Separate Cup, Master Rallye, Invitation and Challenge owners | `CONFIRMED_BY_EXE` | Does not establish new configurable counts. |
| Cup stage and Master save/Resume roster persistence | `CONFIRMED_BY_RUNTIME` in historical qualified candidates | Not re-tested on the published beta in this research-only phase. |
| Six/eight participant lifecycle | `CONFIRMED_BY_RUNTIME` in historical R-AI2.1 candidate | Mixed non-repeating roster; no all-course clearance. |
| Seven-AI T1/T2 same-class crash | `HUMAN_RUNTIME_OBSERVATION`; cause `UNKNOWN` | No exception EIP/register/stack linked to these scenarios. |
| Grid formula and course templates | `CONFIRMED_BY_EXE` / corpus structural audit | All course physical clearances `NOT_TESTED`. |
| Forced/player-randomized/forced-roster/grid behavior proposed here | `STATICALLY_INFERRED` | No R-MOD3 gameplay implementation or new runtime test. |

## Automated checks

`audit_evidence.py` re-checks exact retail file identity when given a path,
checks source hashes and native addresses in the mode map, parses selected
Ghidra assembly invariants, verifies the F3 plan is pinned to the retail SHA,
checks its operations for range overlap and exact retail file-offset
preimages, and requires all 36 course clearance labels to remain explicit.
`tests/test_audit_evidence.py` contains isolated
positive and negative fixtures. These checks validate document inputs; they
do not launch the game, inspect DLL runtime state or prove gameplay.

The authoritative research check command and output are recorded in
`validation-report.json` after the final run. This phase does not claim a full
R-MOD C++ product suite because no product source was changed and the
pre-existing worktree contained unrelated dirty changes.
