# R-GRID8 static validation

## Candidate and Observatory

- Source EXE: pristine retail SHA256
  `bf8aef32407eb6552c05045b8abef149f32983cedd9503b865069b444c5f96b4`, size
  3,121,214.
- Candidate SHA256:
  `75942c0b65147b96b8b2254ee536f6aefc7f3a501c23d12be640f85a562680ac`, size
  3,121,214.
- The exact build verifier passed inverse restoration and byte-equal
  deterministic reproduction.
- R-OBS2 family audit passed the `retail-broker-v1` structural anchors and
  created `profile_origin=locally_audited` in ignored
  `.research-output/observatory/build-profiles/`. The candidate SHA was not
  added to the exact-source profile list. Its registry profile remains
  `unknown`; generic Broker capture is enabled, but registry-semantic checking
  is not inferred from that profile.
- Only `loading_legacy_failure` matches the explicitly enumerated exact
  false-Attract variant. All Broker, Debug and native Dump anchors match stock.
- Active-race native Dump is usable. Post-Results native Dump remains unsafe.

## Course-derived data

The protected retail corpus is read-only. Rebuilding produced 36 distinct
canonical RaceTest resources, 39 registered scene IDs, 288 predicted
transforms, and 36 `NOT_TESTED` audit rows. Every resource hash was checked
against both R-AI2.1's capacity map and R5T SDK corpus validation. No course
asset was edited.

## Commands

Run from the repository root:

```powershell
$env:PYTHONPATH = (Resolve-Path 'src').Path
python -m unittest discover -s tests/synthetic -v
python -m compileall src tools tests
python tools/r_grid8_candidate.py verify .research-output\general-re\grid8\MRallye.exe
python tools/research_build_profiles.py audit-build .research-output\general-re\grid8\MRallye.exe
python tools/grid8_audit.py summary
git diff --check
```

The full R-AI2.1 regression suite remains part of synthetic discovery. The
active-race `check-capture` tool binds the candidate, Observatory local profile,
JSON/raw Dump pair, scene ID, eight IDs/classes/drivers and subsystem paths. Its
maximum verdict is `GRID8_BROKER_STATE_MATCH_ONLY`; human visual observation is
still necessary.

No Results, finish, replay, or gameplay lifecycle is required in this phase.
