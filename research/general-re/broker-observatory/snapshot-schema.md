# Snapshot schema and CLI

Schema: [broker-snapshot.schema.json](broker-snapshot.schema.json), version 1.

New captures include optional `tool_version` and microsecond UTC creation times
for reliable same-second history ordering. Older snapshots without tool_version
remain valid schema v1; no existing capture is rewritten.

The JSON is a parsed view of the game's emitted text, paired with a raw
`.dump.bin` sidecar during live capture. Important `source` fields include the
process/build identity, full-buffer hash and length, selected-block byte
offset/length/hash, capture method, and output sidecar name. `dump` includes
the printed size/capacity, scope totals, SaveFile list, and parsed-row count.

Each `entries` element preserves row order and duplicates. It contains:

- `ordinal` in the selected Dump block;
- `occurrence` among equal `(broker_id, path)` rows;
- `revision`, exact displayed `broker_id`, coarse `scope_label`, path, and type text;
- conservative typed `value`, displayed `value_raw`, raw formatting remainder,
  plus all continuation lines;
- `save_flags` with S/O/PS names, matching `save_game`, `save_options`, and
  `save_player_state` fields, and the row's SaveFile label;
- the complete original first line.

`ID=` is retained as `broker_id` because it is the exact printed token; a
separate `scope_label` maps the two named scope cases and the remaining branch
to USER. The diagnostic does not expose the interned path/key ID as a numeric
field. `dump.special_labels_observed` records reserved labels only when they
appear in an entry's SaveFile or the printed registry. `UNKNOWN:<type>` rows
cause a fail-closed parse so parser coverage can be extended deliberately. The
raw source remains intact. Labels such as `frontend` or `italy1-t2` are
metadata only and do not infer game state.

Bool, Int, Float, `nuVector2/3/4`, Matrix, simple quoted strings, and
StringList rows receive a typed `value` when the displayed representation is
unambiguous. Matrix values remain a flat output-order list; no row/column
semantics are inferred. Quoted string contents are unwrapped but not unescaped;
`value_raw`, `value_raw_remainder`, and `raw_first_line` retain the exact
display form. XmlData remains an opaque emitted value plus continuation text.

## Commands

```text
broker_observatory.py capture --pid PID --label LABEL --output SNAPSHOT.json
broker_observatory.py parse RAW.dump.bin --label LABEL --output SNAPSHOT.json
broker_observatory.py summarize SNAPSHOT.json [--prefix PREFIX] [--json]
broker_observatory.py diff BEFORE.json AFTER.json [--prefix PREFIX] [--float-tolerance N] [--format text|json|csv]
```

Prefixes are case-sensitive because resource paths are preserved exactly.
Diff matching retains duplicates; see [diff-semantics.md](diff-semantics.md).

Example offline parse of a previously captured raw buffer:

```powershell
python tools\runtime\broker_observatory.py parse .\baseline.dump.bin --output .\baseline.json
python tools\runtime\broker_observatory.py summarize .\baseline.json --prefix Vehicles/ --json
python tools\runtime\broker_observatory.py diff .\baseline.json .\race.json --prefix Race/ --format json --output .\race-diff.json
```

Offline parsing does not read or modify the game process. Live capture requires
the verified retail build and explicit PID.
