# R5T-B.1 variance-aware cook method

## Why 3 + 3 cooks are required

Two earlier identical-source France1 cooks produced different valid render
prefixes: 85,212 vs 84,738 vertices, 75,456 vs 75,246 triangles, and 4,621
vs 4,638 draws. The raw tag100 region and 172 non-DX resource hashes were
identical. One baseline and one edited cook would therefore confound source
effects with known natural variation.

## Cohorts

- `baseline`: three independent cold-cache cooks of the unchanged 8.4.1
  France1 GXM/TXT/GXI resources.
- `modified`: three independent cold-cache cooks of the same files, with only
  one recorded GXM float changed by +1.0 source X.

Each runtime clone was made from the same isolated Demo 9.10.0 runtime tree.
The France1 DX and all 66 DXT cache files were removed before its first cook.
After each successful load, the `snapshot` command copies the entire course
folder to a unique immutable run directory and hashes both source inputs and
all resulting resources. The runtime must be fully closed before `reset`
removes generated DX/DXT files for the next run.

## Reproducible commands

The two generated `TEST_INSTRUCTIONS.txt` files contain the cohort-specific
commands and run IDs. From the repository root, a baseline example is:

```powershell
python tools\r5t_b1_course_cook.py snapshot `
  --experiment france1-startpoint `
  --cohort baseline `
  --run-id baseline-01 `
  --course-target DataGx/Course/France1

python tools\r5t_b1_course_cook.py reset `
  --experiment france1-startpoint `
  --cohort baseline `
  --course-target DataGx/Course/France1
```

Repeat with run IDs `baseline-02` and `baseline-03`; use `modified` and
`modified-01` through `modified-03` for the edited cohort. Snapshot before
reset. Add `--log path\to\readable.log` to `snapshot` only when a readable
plain-text log exists.

After all six successful loads and snapshots:

```powershell
python tools\r5t_b1_course_cook.py compare --experiment france1-startpoint
```

The comparison refuses fewer than three runs per cohort, duplicate run IDs,
non-identical input manifests within a cohort, or a cross-cohort difference
that is not exactly the patched GXM. It reports hashes, sizes, DX render and
tag100 parser fields, other resource hashes, and optional log summaries. A
stable compiled field is not by itself proof of a physical or gameplay effect.

## Completed result

All six snapshots were captured and the variance-aware report passed input
validation. Baseline and modified cohorts each contain three cold-cache cooks
with identical inputs within the cohort. The only cross-cohort input change is
the recorded point-0 X float in `France1.gxm` (+1.0 source unit).

All six revision-135 DX files pass course render validation. The tag100 region
is 10,118,248 bytes in every run; baseline hash is
`9a3ea51096fc24ab82689ac929951cf8ba3291f3dc9d688fb95365383ef5a7d7` and modified
hash is `c89654dbf502de96df366d05ecdd87051b0051e8308851550c0e0b6d37c23086`.
The raw region is byte-identical within each cohort, while render prefixes
vary naturally. This confirms a deterministic compiled tag100 response to the
isolated source edit; it does not assign runtime semantics. See
[`startpoint.md`](startpoint.md) and the R5T-C differential report.
