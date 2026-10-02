# Central manager

Retail, `CONFIRMED_BY_EXE` unless qualified.

| Location | Meaning | Independent evidence |
|---|---|---|
| `006F9410` | lazy shared manager pointer | `004D8EC0` allocates 0x1C shell; editor and game use accessor |
| manager `+04/+08/+0C` | entry begin/end/capacity pointers | setters calculate indexed address; serializers iterate begin→end |
| manager `+14` | circular SaveFile-list sentinel | `004D54A0` insertion, `005B16C0` traversal |
| manager `+18` | SaveFile-list count | insertion increments; destroy clears nodes |
| manager `+00/+10` | not assigned a general semantic name | partial structure only |

Allocated-slot count is `(end-begin)/0x1C`; capacity is `(capacity-begin)/0x1C`.
Neither equals the number of nonempty values. A key's interned ID selects
`begin + id*0x1C`; access grows to at least `id+1`, constructing intervening
empty slots. Getter families can therefore mutate allocation/key bookkeeping.
An entry pointer must not survive vector reallocation; the ID is the stable
lookup handle while the path pool lives.

## SaveFile container correction

`004D54A0` compares each node's string through `004D0570` and `005D1660`
(`_stricmp`), returns on a duplicate and otherwise allocates a **0x0C node**:
`+00 next`, `+04 previous`, `+08 interned SaveFile ID`. Head/tail links are
circular; no payload ownership is stored in these nodes. `004D5350` enumerates
live entry `+18` fields into this list. `004D5400` retags entries from an old
logical file to another. `005B16C0` consumes the registry to save Game groups.

This corrects the R-DEV1.2 description “interned broker key-ID list”: the node
representation was useful, but its **semantic role is SaveFile registration**.
Broker open registers `__NO_SAVE`/`__NO_CHANGE` names; it does not create those
as ordinary typed entries. The open-only metadata-mutation classification stands.

## Ownership, copies, removal

- `004DD980` constructs an empty entry; `004DDC20` releases payload and resets
  it. `004DE7B0` performs tag-specific destruction, including XmlData virtual
  deletion and StringList ownership. String-ID wrappers do not own pooled text.
- `004D8D40` resets a valid positive ID's slot; it does not shift later IDs.
- `004D7690` merges nonempty source entries by ID; `004DEAA0` copies payload
  and metadata, cloning XmlData through virtual `+08`.
- `004D78C0` replaces/reset-copies the source manager. `004D7830` clears the
  shared vector; `004D8F70` destroys manager-owned entries/storage/list nodes.
- `004D7A60(scope)` resets matching live slots but no validated direct caller
  was recovered. An available primitive is not proof of normal scene policy.

There is one slot per exact path ID per manager; changing scope does not create
a second same-path record. The Observatory preserves duplicate Dump rows as
evidence defensively; it does not assert duplicate live singleton slots exist.
