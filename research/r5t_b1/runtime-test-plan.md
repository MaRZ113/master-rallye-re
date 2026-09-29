# France1 controlled cooker test plan

## Candidate and gate

The staged source candidate changes one float in the first-eight France1
startpoint point box by +1 source unit. This is a controlled byte edit, but
the link from that point to the literal `startpoint` node remains
`HIGH_CONFIDENCE_INFERENCE`, not a proven index binding.

Do not interpret a single baseline/modified comparison. Demo 9.10 has already
produced different validated render prefixes from identical source. Capture at
least three cold-cache cooks for each cohort. Each run must load France1
successfully in the isolated Demo 9.10 runtime clone and be snapshotted before
its DX/DXT caches are reset.

## Staged inputs

- Baseline runtime: `.research-output/r5t_b1/experiments/france1-startpoint/baseline/runtime`
- Modified runtime: `.research-output/r5t_b1/experiments/france1-startpoint/modified/runtime`
- Course target: `DataGx/Course/France1`
- Generated cohort instructions: each cohort directory's `TEST_INSTRUCTIONS.txt`
- Expected one-float patch: root `source-patch.json`

The staging tool uses copies under ignored `.research-output`; source corpus
and original runtime paths are read-only inputs. It does not launch the game
or modify any file outside the isolated experiment directory.

## Human run sequence

For each cohort, launch the `MRallye.exe` inside that cohort's `runtime`
directory with that same directory as working directory. Select France1 and
wait until it loads successfully. From the repository root, run `snapshot`
using the next cohort run ID. Exit the runtime fully, then run `reset` before
the next independent cook. The generated instruction files contain exact
commands for `baseline-01..03` and `modified-01..03`.

After six snapshots, run:

```powershell
python tools\r5t_b1_course_cook.py compare --experiment france1-startpoint
```

This validates cohort inputs and emits `variance-aware-report.json` and
`variance-aware-report.md` in ignored output. It classifies values as
baseline-variable, stable modified, modified-variable, or unchanged. A stable
compiled difference establishes source-to-compiled correlation only; a
separate runtime observation is needed for an in-game effect.

## R5T-B.1 closeout result

The six required cooks were captured and compared. Baseline tag100 is
10,118,248 bytes with SHA-256
`9a3ea51096fc24ab82689ac929951cf8ba3291f3dc9d688fb95365383ef5a7d7` in all
three runs. Modified tag100 has the same size and SHA-256
`c89654dbf502de96df366d05ecdd87051b0051e8308851550c0e0b6d37c23086` in all
three runs. Render prefixes vary naturally. The result confirms a repeatable
source-to-tag100 compiled effect, not a semantic interpretation.

The owner reports that the modified course loaded in Demo 9.10.0 with no
obvious starting-grid or other gameplay difference. This was a one-corner
tracer, not a whole-object translation; it does not establish that the
startpoint volume is irrelevant to spawning, triggers, collision, or race
activation. R5T-C should test a validated whole-volume translation before
making those claims.
