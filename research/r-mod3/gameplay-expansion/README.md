# R-MOD3 gameplay expansion feasibility

This is a read-only reverse-engineering and design package for the published
Randomizer & AI Extender beta. It does not change the beta DLL, INI parser,
patch plan, renderer proxy, executable, or release artifact. The source build
was already dirty when work began; its unrelated changes remain untouched.

The public baseline is pinned in [published-baseline.json](published-baseline.json):
tag `v0.1.0-beta.1`, commit `40e96a879d81dbe8fece1af65f8ccec3ec1334fd`,
and the uploaded ZIP SHA256. The pristine retail source is 3,121,214 bytes with
SHA256 `bf8aef32407eb6552c05045b8abef149f32983cedd9503b865069b444c5f96b4`.

## Findings at a glance

| Area | Feasibility | Confidence and boundary |
|---|---|---|
| Seven AI with same-class T1/T2 and repeated CarIDs | Existing native chooser explicitly refills an exhausted physical-ID pool. The reported crash cause remains **UNKNOWN**. | High confidence in static refill and per-slot publication; no matching exception EIP or repeated-ID crash capture was found. |
| Opponent counts outside Quick Race | Separate Cup, Invitation, Master Rallye, and Challenge owners exist. | High confidence in ownership; per-mode count/scoring/save limits remain unqualified. |
| Randomize human vehicle | A prepared, displayed physical ID can feed the existing native player-car read. | High confidence in Quick Race's selected-ID-to-Car0 path; mode-wide preview and class-rule handling need a focused design proof. |
| Force AI roster | Native selection is mode-owned and physical ID, derived class, driver and participant slot are separate values. | High confidence in native publication boundaries; repeated-ID gameplay remains unqualified. |
| Force starting grid | The native grid is derived from `StartArea` and writes a transform per `CarN`; a logical-car to grid-ordinal permutation is the least invasive candidate. | Medium confidence; no arbitrary-coordinate implementation or all-course clearance proof. |
| Force human vehicle | Feasible at a prepared-selection boundary, with explicit per-mode validation and UI synchronization. | Medium confidence; Challenge-authored rules and cross-class campaign semantics remain unknown. |

Evidence labels are kept separate: `CONFIRMED_BY_EXE`, `CONFIRMED_BY_CORPUS`,
`CONFIRMED_BY_RUNTIME`, `HUMAN_RUNTIME_OBSERVATION`, and
`STATICALLY_VERIFIED`. The earlier R-AI2 eight-participant runtime is evidence
for the engine's tested capacity and lifecycle; it does not qualify repeated
CarIDs or every course start.

## Research documents

- [Duplicate CarID and seven-AI crash](duplicate-carid-root-cause.md)
- [Per-mode opponent counts](per-mode-opponent-counts.md)
- [Player vehicle randomization](player-randomization.md)
- [Forced AI roster and starting grid](forced-roster-and-grid.md)
- [Forced player vehicle](forced-player-car.md)
- [Cross-feature interactions](cross-feature-interactions.md)
- [ConfigVersion 3 proposal](config-v3-proposal.ini)
- [Native hook map](native-hook-map.md)
- [Implementation roadmap](implementation-roadmap.md)
- [Evidence and validation](evidence-and-validation.md)
- [Future Vehicle SDK interoperation boundary](vehicle-sdk-interoperation.md)

The compact audit in `audit_evidence.py` checks the exact retail image when
provided and cross-checks the existing mode map, chooser note, grid corpus
summary and selected Ghidra exports. It reads files only. Its tests check the
auditor's fail-closed behavior; they are not game-runtime tests.

Run the offline evidence checks from the repository root:

```powershell
python research/r-mod3/gameplay-expansion/audit_evidence.py `
  --retail-exe 'D:\Game\Master Rallye Pristine\MRallye.exe' `
  --output .research-output/r-mod3/gameplay-expansion/audit-report.json
python -m unittest discover -s research/r-mod3/gameplay-expansion/tests -v
python research/r-mod3/gameplay-expansion/build_review_archive.py
```

The final test summary is `validation-report.json`; the review archive includes
that summary, the audit source, tests and documentation only. It excludes
executable files, game resources, raw captures and Ghidra databases.

No gameplay implementation was performed. The seven-AI crash remains the
first bounded implementation gate because its actual failing instruction has
not been established. Any follow-on work requires owner approval and a new
phase-specific candidate; this package itself does not arm or authorize one.
