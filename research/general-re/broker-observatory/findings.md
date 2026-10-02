# Broker Observatory — findings

## Status

**Tooling implemented; offline synthetic validation passes; live process capture is awaiting the human runtime check.** The tool is based on the verified retail executable and the existing R-DEV1.2 static analysis. It reads the existing Debug window buffer only. It does not invoke Debug→Dump, send a command, suspend the process, edit a broker, save game state, or patch an executable.

The persistent research checkout is `master-rallye-re-general`, branch
`research/general-re`. It continues from the completed R-DEV1.2 baseline. No
other course/R-DEV worktree was changed.

## Corpus and analysis

- **CONFIRMED_BY_CORPUS:** retail `MRallye.exe` is 3,121,214 bytes with SHA256 `bf8aef32407eb6552c05045b8abef149f32983cedd9503b865069b444c5f96b4`.
- **CONFIRMED_BY_EXE:** the retail Dump menu route and typed entry formatting are in `0065EC40` and `00601D00`; the path was checked against the R-DEV1.2 Ghidra analysis on Ghidra 12.1.4.
- **CONFIRMED_BY_RUNTIME (prior owner observation):** the Broker Editor's Debug→Dump command previously produced a large text dump. One observed state reported GLOBAL 6929, SCENE 914, USER 0, TOTAL 7843. These are one-state observations, not fixed capacities or parser constants.
- **CONFIRMED_BY_RUNTIME (prior owner observation):** root `CarN` and `Drivers/DriverN` XmlData rows appeared as leaves in the Broker Editor, with displayed class names such as `gaVehicleOutputData` and `gaIContDriverParams`; they did not expand as normal broker subtrees.
- **CONFIRMED_BY_RUNTIME (prior owner observation):** `__NO_SAVE` appeared on transient rows; `__NO_CHANGE` appeared as a selectable pseudo-value in an editor combo. The latter's implementation meaning remains unknown, and the observation does not establish `__IGNORE` as a runtime SaveFile registry entry.
- **NOT YET CONFIRMED_BY_RUNTIME:** the new external reader has not yet captured a live process buffer. Synthetic fixtures validate parser and diff behavior, not Windows process access or the actual runtime buffer layout.

See [dump-call-path.md](dump-call-path.md),
[capture-architecture.md](capture-architecture.md), and
[known-unknowns.md](known-unknowns.md) for evidence and limits.

## What the original dump contains

The text dump emits rows with a revision, a displayed scope label, the three
save flags, a SaveFile label, a broker path, a displayed type, and a formatted
value. It also emits scope totals and a SaveFile-name list. The schema retains
the exact text following `ID=` as `broker_id` and maps the coarse dump branch
to `scope_label` (`GLOBAL`, `SCENE`, or `USER`). The printed value is not the
underlying interned string-table ID for the path; that ID is not separately
emitted by this diagnostic.

The dump enumerator skips type tag `0x0C`, and formats Float/vector/Matrix
values to two decimal places. The retained `.dump.bin` is byte-exact relative
to the captured Debug buffer, and the JSON preserves each emitted row and its
continuations. It is not a byte-exact serialization of the broker manager or
full-precision value storage.

The snapshot also preserves the exact printed SaveFile filename list and
records `__NO_SAVE`, `__NO_CHANGE`, or `__IGNORE` in
`dump.special_labels_observed` only if that text actually occurs in a row's
SaveFile field or the printed list. It does not treat the three labels as
equivalent or assert that all belong to the registry.

XmlData is preserved as one broker row with its original path, type, printed
value, and continuation lines. The Observatory never creates child paths such
as `Car0/Class` or `Drivers/Driver0/Skill` from an XmlData object.

## Tool operations

```powershell
python tools\runtime\broker_observatory.py parse <debug-buffer.dump.bin> --output <snapshot.json>
python tools\runtime\broker_observatory.py summarize <snapshot.json> --prefix Race/ --json
python tools\runtime\broker_observatory.py diff <before.json> <after.json> --prefix Race/ --format json
python tools\runtime\broker_observatory.py capture --pid <retail-pid> --label frontend --output research-output\general-re\broker-observatory\captures\baseline.json
```

`capture` requires an explicit PID and accepts an optional `--label` metadata
tag. It verifies the on-disk retail hash and size,
checks the loaded `MRallye.exe` module, and reads the existing Debug sink with
`PROCESS_QUERY_INFORMATION | PROCESS_VM_READ`. It emits a JSON snapshot and a
same-basename `.dump.bin` raw sidecar. It fails closed if the active sink is
not the known Debug sink or if the data changes during its consistency reads.

For the exact human procedure and safety boundary, see
[runtime-validation-plan.md](runtime-validation-plan.md). Captures belong in
ignored `research-output/`; never add them to Git.

## Related evidence

- R-DEV1.2 already classifies Broker Editor open-only as
  `LOW_RISK_BUT_METADATA_MUTATION`: its opener registers two interned names in
  shared in-memory key metadata. This tool does not invoke that opener.
- The existing `tools/runtime/dev_command_trigger.py` allowlists Flow Builder
  and Broker Editor with separate confirmation phrases. It was reviewed but
  did not need changes for passive capture.
- No game files, authoritative data, EXEs, or Ghidra project databases were
  modified or added to this branch's tracked output.
- The JSON reports parsed-entry count, non-entry lines outside complete Dump
  blocks, malformed entry-like lines, and rejection reasons for incomplete
  candidates. Unknown typed rows fail closed instead of disappearing.
