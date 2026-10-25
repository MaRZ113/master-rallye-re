# V-SDK SCALE1 work log

Branch: `research/vehicles`. Private evidence and candidates live under
`.research-output/vehicles/scale1/` and are excluded from Git.

Execution order:

1. Verify retail identity and audit native registry, frontend, race, UI and
   persistence consumers; distinguish stock bounds, tested extensions and unknowns.
2. Implement deterministic collection allocation and append-only UI/resource
   composition with explicit qualification levels. Preserve the old profile.
3. Generate and validate a reversible external runtime capacity probe for a
   second T2 slot, then bounded larger layouts only where evidence permits.
4. Continue direct GT4 source parsing and shared conversion; keep unsupported
   source structures explicit, without guessed wheel anchors or geometry.
5. Run regressions, preserve frozen Subaru resources and protected originals,
   package own source/docs/tests and document human runtime gates.

## Iteration notes

- Retail executable SHA256 confirmed by REA/Ghidra 12.1.4:
  `bf8aef32407eb6552c05045b8abef149f32983cedd9503b865069b444c5f96b4`.
- REA recovered 34 direct callers of the registry singleton. Complete caller
  pseudocode is retained privately with evidence IDs. This is a direct-call
  inventory, not proof that indirect or cached-pointer consumers do not exist.
- Original registry has 26 records, stride 0x34, followed by 39 RaceTest rows
  of stride 0x2C. Current SDK supports two audited added slots; ID28 rejection
  belongs to its profile and is not an observed universal engine ID check.
- Original frontend capacities are 7/7/11. Navigation reads the capacity for
  the selected class; position publication iterates 12 keys. These are separate
  constraints from global record allocation and UI texture-bank frame counts.

## Result and evidence boundary

**Two offline capacity candidates are ready for human testing. A combined
Subaru + GT4 Lancer candidate is not yet available.** No new capacity is
runtime-qualified. Original EXE/DLL, frozen Subaru geometry/wheels/livery and
physics values are preserved. No game launch, commit, publication or push.

Implemented persistent CarID/class-slot reservations (including removal
tombstones), explicit conflict rejection, case-insensitive resource ownership,
append-only UI composition and generated native roster extensions. An optional
64-KiB private process allocation removes the code-cave storage bottleneck.
Default retail capabilities retain their previous qualified IDs26/27. The
experimental canary harness extends one exact pinned base; the old general
`runtime-prepare` command remains reference-bounded, not an arbitrary roster
installer. Actual converted resources remain a separate author-build input.

| Evidence | Global records | T1 / T2 / T3 | Meaning |
| --- | ---: | --- | --- |
| Retail | 26 | 7 / 7 / 11 frontend | Registry also contains ID25 Trooper, exposed by a prior extension |
| Previous qualified baseline | 28 | 8 / 8 / 12 | Prior human evidence; gameplay not repeated here |
| Packaged candidate A | 29 | 8 / 9 / 12 | One new T2 slot; offline only |
| Packaged candidate B | 30 | 8 / 10 / 12 | Two new slots and private code allocation; offline only |
| Largest constructed/emulated profile | 32 | 8 / 12 / 12 | Resources derived, helpers emulated; not gameplay |
| Rejected next profile | 33 | 8 / 13 / 12 | Twelve-position publisher admission bound, not engine maximum |

No universal maximum or unlimited count is demonstrated. Details and coverage
gaps: [capacity.md](capacity.md). GT4 progress: [gt4.md](gt4.md).
Regressions and human gates: [validation.md](validation.md).

## Candidates and test order

Private outputs under `.research-output/vehicles/scale1/`:

1. `final-29/` and `final-29-private-candidate.zip`: unchanged Subaru/Mercedes
   plus one independently registered **SDK T2 CAPACITY PROBE**.
2. After A passes, `final-30/` and `final-30-private-candidate.zip`: two canaries.

The canaries use genuine stock Navara geometry under separate families and
explicit SDK PROBE names. They are not substitutes named Lancer. They have
independent UI frames and byte-exact cloned physics values. Only five shared
XML/bank composition outputs change; previous frames remain byte-identical.
Each candidate has `HANDOFF.md`, `validation.json`, sealed runtime and matched
launcher. Do not exchange launchers or player state between candidates.

PowerShell from the repo:

```powershell
$candidate = (Resolve-Path '.research-output/vehicles/scale1/final-29').Path
& "$candidate/launcher/mr-runtime-launcher.exe" --integrated 'D:/Game/Master Rallye/MRallye.exe' "$candidate/runtime"
```

Check Vehicle Select, all classes, Subaru and every probe, both player actors,
a new Quick Race, AI, Results and return/re-entry; reflections on/off. Use each
bundle's disposable state, not a transplanted campaign save. Quit before trying
another bundle. Campaign progression, persisted competitions and multiplayer
remain unqualified. This human lifecycle gate prevents claiming new safe counts
from static/emulator results alone.

## Reproduction

```powershell
$env:PYTHONPATH = 'src;tools;.'
python tools/run_scale1_qualification.py --base .research-output/vehicles/vmesh413/v413-exp-004/runtime --output .research-output/vehicles/scale1/reproduced-29 --records 29
python tools/run_scale1_qualification.py --base .research-output/vehicles/vmesh413/v413-exp-004/runtime --output .research-output/vehicles/scale1/reproduced-30 --records 30
```

New output required. These commands build/preflight/package; never start the
game. Optional `--emulate` uses caller-installed Unicorn/Capstone, not SDK runtime
dependencies. `mrtool addon collection-plan` supports repeated manifests,
explicit capabilities and optional `--reservations` for stable assignment.
Experimental29/30 capability profiles here do not upgrade runtime qualification.

`scale1-source-review.zip` contains current own source snapshots/tests/docs and
compact validation summaries, no extracted models/textures/CORE/ELF or raw native
dumps. The private candidate archives contain local game assets and must not be
distributed. The working tree had substantial pre-existing changes; source
snapshots are not a claim that all file contents originated in this task.
