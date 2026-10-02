# Snapshot diff semantics

## Matching

Entries are first paired by exact `(broker_id, path, occurrence)` identity.
For an unmatched entry whose broker ID changed, the diff pairs only a unique
remaining `(path, occurrence)` on each side. If duplicate cross-scope records
make that fallback ambiguous, they remain explicit REMOVED and ADDED rows;
the tool does not guess which one moved. Equal paths are never collapsed.

The game's `ID=` token is retained exactly as `broker_id`, but it is not the
interned string-table ID for the broker path. `BROKER_ID_CHANGED` reports a
change to that printed token; `SCOPE_CHANGED` reports a change to the coarse
GLOBAL/SCENE/USER branch. Both can appear for one transition.

## Change categories

- `ADDED` / `REMOVED`
- `VALUE_CHANGED` for same-type displayed values
- `TYPE_CHANGED`
- `REVISION_CHANGED`
- `BROKER_ID_CHANGED`
- `SCOPE_CHANGED`
- `SAVE_MASK_CHANGED`
- `SAVE_FILE_CHANGED`

One paired entry can contain several changes. Type changes are reported as a
type change; the new representation is present in the event's before/after
entry only for JSON snapshots, while text/CSV focus on category and value
metadata.

## Numeric behavior

Integers and booleans compare exactly. Float/vector/matrix display values are
parsed as numbers and compared using an optional absolute tolerance (default `0`).
Because the original dump formats these values to two decimal places, a
tolerance cannot reconstruct unprinted precision. Simple quoted strings and
StringList values have conservative typed views; raw text and continuation
lines remain in every entry. Strings and other multiline types compare the
typed value and emitted continuation lines exactly. The raw snapshot and
sidecar preserve original text for manual review.

Prefix filters use case-sensitive `startswith` against the displayed path.
This allows focused comparisons such as `Race/`, `Vehicles/`, or
`Editing/` without changing path normalization or case.
