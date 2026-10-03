# Embedded authoring paths and guarded bridge

## Current R-COOKER3.1 lifecycle

Current jobs keep authoring mirrors beneath their own job roots and use the
Python Junction manager in `junction_lifecycle.py` and `source_cooker_jobs.py`.
New jobs do not emit setup/removal scripts. Junction creation and cleanup
verify path type, exact target, and job ownership; ambiguous state is blocked.
Schema-2 paths resolve relative to the current job directory. The generated
PowerShell workflow described later on this page is historical V1 behavior,
not a current requirement or release artifact.

## Discovery

`discover_embedded_authoring_paths` parses every supported material-prefix
GXM role and records absolute GXI references as tuples of:

- GXM role and exact embedded path;
- historical root to which the embedded path points;
- matching relative GXI source and SHA256;
- resolution state.

References are grouped by historical root. A required reference must resolve
unambiguously. For these legacy vehicle folders, a root-level file wins over a
nested alternate only when it exists at the package root; conflicting
different-byte duplicates otherwise block the job. The source directory is
read-only.

Mercedes uses 50 role references to 25 unique GXI files. Forester uses 46 role
references to 23 unique GXI files. Forester's fourth inventory GXI is not
referenced by the selected complete/car/wheel GXM set and is not copied into
the authoring mirror.

## Historical V1 mirror and generated scripts

`materialize_authoring_mirror` copies only referenced GXI files and verifies
each copied SHA256. The initial V1 implementation emitted setup and cleanup
PowerShell scripts and a job-owned manifest. That workflow was replaced by the
R-COOKER3.1 Python lifecycle above.

Setup accepts only an absent path or the exact owned Junction target. A real
directory, unknown reparse point, ownership mismatch, or different target
stops execution. Setup also stops if the historical parent directory is
missing; it does not create directories outside the job. Target checks use
`Get-Item -Force` and the `.Target` property. Cleanup rechecks job ownership,
Junction type, and exact target, then removes only the Junction link with
non-recursive `rmdir`; it never deletes the target tree.

The Mercedes T1/T2 historical path was already removed by its prior owned
helper and was observed absent for T2. Older user-owned Mercedes/Forester job
directories retain their original manifests and generated helpers; R-COOKER3.1
does not rewrite those ignored research outputs. The current Python lifecycle
is exercised with isolated temporary Junctions by the synthetic integration
tests, and release jobs created by the current CLI do not generate scripts.

## Fail-closed cases

- unsupported or non-absolute GXI references;
- missing source file;
- ambiguous different-byte basename candidates;
- a single historical path resolving to different copied content;
- copied GXI hash mismatch;
- non-owned, non-Junction, or wrong-target existing link.

The raw embedded absolute paths belong to the original authoring projects;
the bridge redirects only those exact roots to an isolated mirror during a
human cook.
