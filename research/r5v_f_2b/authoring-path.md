# R5V-F.2b authoring-path mapping

## Embedded path evidence

The three selected root GXM files contain GXI references under
`D:/projects/MRallyeTNG/DataGx/Vehicles/Mercedes/`. The adjacent `lpha`
GXM files use `D:/Projects/MRallyeTNG/DataGx/Vehicles/MercedesAlpha/` instead.
Only the root Mercedes source is staged. Its GXI files are copied byte-for-byte
to `research-output/r5v_f_2b/authoring-root/Mercedes/`; no GXM path string is
rewritten.

## Preflight and planned Junction

The exact destination checked was:

```text
D:\projects\MRallyeTNG\DataGx\Vehicles\Mercedes
```

At preflight, the path and its parent components did not exist. The read-only
check helper reported:

```text
SAFE STATE: exact authoring path is absent; setup helper may create the junction.
```

The intended target is:

```text
D:\Game\Master Rallye\research-output\r5v_f_2b\authoring-root\Mercedes
```

The Junction has not been created yet. `CHECK_AUTHORING_PATH.ps1` and
`SETUP_MERCEDES_JUNCTION.ps1` are under the ignored output `scripts/` folder.
Setup validates the 25 GXI hashes, refuses an existing unmarked path, checks
the parent components are ordinary directories, and records a phase marker.
`REMOVE_MERCEDES_JUNCTION.ps1` requires that completed marker, Junction type,
and exact resolved target; it unlinks only that one junction node and verifies
the isolated target remains hash-identical. No recursive removal is used.

## Current status

`GXM rewrite/rebase not required if the Junction authoring-root method
succeeds.` That remains conditional until retail logs prove that GXM parsing
can resolve the source texture path through this Junction and complete the
cache write. The historical demo source and canonical retail folders remain
untouched.
