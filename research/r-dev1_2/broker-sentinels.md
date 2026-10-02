# Broker key registry and reserved-looking names

## Finding

Retail Broker Editor opening interns two string-ID objects named `__NO_SAVE` and `__NO_CHANGE` into a shared broker key registry. The insertion routine deduplicates by string-ID equality and, if absent, appends a 12-byte linked-list node that stores the ID. It does **not** add a typed broker value, modify an existing broker value, set a dirty/revision/save flag, or write a file.

That gives a precise machine-level meaning for the Broker Editor path: these are names registered in broker key/index metadata. The executable evidence examined here does not establish that the names suppress serialization or mutation. Their English labels remain **UNKNOWN** as policy descriptions until a consumer of those reserved IDs is recovered.

## Sentinel text and references

Retail static string-ID objects used by the Broker Editor opener are:

| Name | String-ID object | Opener use | Context |
|---|---:|---|---|
| `__NO_SAVE` | `0070AEE8` | passed to `004D54A0` once | shared broker key registry |
| `__NO_CHANGE` | `0070AEEC` | passed to `004D54A0` once | shared broker key registry |
| `__IGNORE` | `0070AEE4` | not passed by Broker Editor opener | only its static initialization use was recovered in retail |

Each text also occurs as two literal records in each build. The primary literal address has no direct xref in the existing R-EXE1 string table; the second literal has one direct xref to a static string-ID initializer. These duplicate/static-construction references are not policy tests. The machine-relevant use is the pooled/string-ID object above and the calls into the key-list insertion function.

| Build | `__NO_SAVE` literal addresses | `__NO_CHANGE` literal addresses | `__IGNORE` literal addresses | Broker opener | key-list insertion |
|---|---|---|---|---:|---:|
| 8.4.1 pristine | `005E4D44`, `005E5B64` | `005E4D50`, `005E5B70` | `005E4D5C`, `005E5B7C` | `00543670` | `00482670` |
| 9.3.1 pristine | `006620C4`, `00663274` | `006620D0`, `00663280` | `006620DC`, `0066328C` | `00619480` | `004AC7B0` |
| 9.10.0 pristine | `00698244`, `00699480` | `00698250`, `0069948C` | `0069825C`, `00699498` | `0064B010` | `004C1370` |
| retail pristine | `006AF364`, `006B063C` | `006AF370`, `006B0648` | `006AF37C`, `006B0654` | `0065E990` | `004D54A0` |

The R-EXE1 catalog records one initializer xref for the second `__NO_SAVE` literal in each build (`0041AE8A` in 8.4.1, `0041AF4A` in 9.3.1, `0041BA8A` in 9.10.0, and `0041BCFA` in retail). The same static-initializer pattern is independently visible in the fresh retail Ghidra project for the second `__NO_CHANGE` and `__IGNORE` literals (`0041BD18` and `0041BD36`). These constructors initialize string-ID objects; they are not calls to a save filter or edit guard.

### Retail direct-reference census

A fresh direct-reference query in the isolated Ghidra 12.1.4 retail program returned:

| Target | Direct references | Reference source / interpretation |
|---|---:|---|
| literal `__NO_SAVE` at `006AF364` | 260 | References are grouped at non-function memory locations (`NO_FUNCTION` in the query output); they do not identify a code consumer. |
| literal `__NO_SAVE` at `006B063C` | 1 | Static string-ID initializer `0041BCFA`. |
| literal `__NO_CHANGE` at `006AF370` | 261 | References are grouped at non-function memory locations (`NO_FUNCTION`); no policy-testing function was identified from them. |
| literal `__NO_CHANGE` at `006B0648` | 1 | Static string-ID initializer `0041BD18`. |
| literal `__IGNORE` at `006AF37C` | 260 | References are grouped at non-function memory locations (`NO_FUNCTION`); no policy-testing function was identified from them. |
| literal `__IGNORE` at `006B0654` | 1 | Static string-ID initializer `0041BD36`. |
| pooled object `__IGNORE` at `0070AEE4` | 1 | Non-function reference only; not passed by the Broker Editor opener. |
| pooled object `__NO_SAVE` at `0070AEE8` | 2 | One non-function reference and the Broker Editor call site in `0065E990`. |
| pooled object `__NO_CHANGE` at `0070AEEC` | 2 | One non-function reference and the Broker Editor call site in `0065E990`. |

The hundreds of references on the first literal copies are not hundreds of function xrefs. The query groups them under a non-function source; their source records were not recovered as policy consumers. The only executable Broker Editor use of the pooled sentinel objects is the two insertion arguments in `0065E990`. The initializer references and pooled-object references must therefore be kept separate from semantic policy tests. A comparable complete raw-xref census was not regenerated for pristine 8.4.1, 9.3.1, and 9.10.0 in this phase; their opener/insertion correspondence is documented from the existing cross-build analysis, and that limit is retained rather than extrapolating retail's raw-reference counts.

## Retail manager and list structure

`004D8EC0` obtains or creates the shared manager candidate at `DAT_006F9410`. Its manager allocation is `0x1c` bytes. The relevant fields are:

| Manager offset | Observed representation | Confidence |
|---:|---|---|
| `+0x04` | typed-entry vector begin | HIGH |
| `+0x08` | typed-entry vector end | HIGH |
| `+0x0c` | typed-entry vector capacity/end | HIGH |
| `+0x14` | circular doubly linked-list head for interned key IDs | HIGH |
| `+0x18` | entry/list count used by this list insertion | HIGH |

`004D54A0` receives a pointer to a string-ID object. It walks the circular list at `manager+0x14`, compares each stored ID using the broker string-ID comparison helper, and returns without mutation if the ID is already present. Otherwise it allocates `0x0c` bytes, links the node at the tail, stores the numeric string ID at node `+0x08`, and increments `manager+0x18`.

```text
BrokerKeyNode (0x0c bytes)
  +0x00  previous node pointer
  +0x04  next node pointer
  +0x08  interned string-ID value
```

The list is a general broker key/index registry, not a list of filenames, save exclusions, or Broker Editor filters. The same insertion helper is called from generic broker/key operations (`00522810`, `00522BD0`, `0065F170`, `00671DF0`, `00673130`) as well as twice from the Broker Editor opener. Its compare is list de-duplication, not a `__NO_SAVE` or `__NO_CHANGE` policy check.

The manager accessor can lazily create an empty vector and list head if the global manager is absent. That is metadata initialization. The typed-entry vector is separate from the string-ID list; `004D54A0` does not modify vector records.

## `__NO_SAVE`

**Confirmed:** Broker Editor registers the string-ID object `0070AEE8` in the manager's key list.

**Not confirmed:** a save exclusion, XML serializer filter, Game/Options/PlayerState save suppression, editor commit rule, or automatic persistence rule. No serializer-side test of this ID was found. `004D54A0` only compares for duplicate IDs and appends the ID if missing.

Classification: `CONFIRMED_BY_EXE` for registry insertion; `UNKNOWN` for the name's intended save policy.

## `__NO_CHANGE`

**Confirmed:** Broker Editor registers the distinct string-ID object `0070AEEC` through the same insertion helper.

**Not confirmed:** read-only behavior, dirty-flag suppression, callback suppression, revision suppression, edit prevention, or persistence effects. The insertion function has none of those effects itself, and no reader that compares this exact ID was recovered.

Classification: `CONFIRMED_BY_EXE` for registry insertion; `UNKNOWN` for the name's intended change policy.

## `__IGNORE`

`__IGNORE` has an adjacent string-ID object at `0070AEE4`, but the Broker Editor opener does not pass it to `004D54A0`. In retail, no additional direct code reference to that object was recovered beyond its initializer. Its relation to the other two names is plausible from layout/naming, but semantics and consumers are **UNKNOWN**.

## Cross-build result

All four builds retain the same pattern: Broker Editor opener → manager accessor → insert `__NO_SAVE` ID → insert `__NO_CHANGE` ID. The command ID changed from `0x26` in 8.4.1 to `0x27` in 9.3.1, then remained `0x27`. `__IGNORE` is present in each string set but is not passed by the Broker Editor open path. No evidence shows that any of these names were removed, converted into boolean broker values, or consumed as serializer directives between the builds.

The authoritative 8.4.1 and 9.3.1 files used here are the pristine corpus hashes; previous patched demo copies are not used for these claims.

## Evidence boundary

- **CONFIRMED_BY_EXE:** retail Ghidra 12.1.4 decompilation and call graph for `004D54A0`, `004D8EC0`, and `0065E990`; list node/link code checked against assembly; direct-reference census for the sentinel literals and pooled objects; exact string-ID objects passed by the opener.
- **CONFIRMED_BY_CORPUS:** the four executable identities match `research/corpus/executable-provenance.md`.
- **STRONG_HYPOTHESIS:** these are reserved key names intended for special broker treatment somewhere in a broader tool/data contract.
- **UNKNOWN:** exact policy meaning of each label, any indirect consumer through a dynamically computed ID, and whether an external editor/tool interprets the names.
- No runtime value was edited, saved, or committed.
