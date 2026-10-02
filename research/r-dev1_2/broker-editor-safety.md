# Broker Editor open-only safety decision

## Decision

**LOW_RISK_BUT_METADATA_MUTATION — controlled open-only observation is acceptable with a separate stronger confirmation.**

The retail command `0x27` reaches `0065E990`. Before display, it registers `__NO_SAVE` and `__NO_CHANGE` through `004D54A0`. That function de-duplicates or appends two 12-byte nodes containing interned string IDs in the shared broker manager's key registry. It does not write a typed broker value, revision, dirty flag, or file. The list is key/index metadata, not a dedicated save-exclusion list.

Broker row population reads existing broker records and posts UI messages. The mapped open-only call graph contains no `CreateFile` write access, `CREATE_ALWAYS`, XML writer, Game/Options/PlayerState save handler, delete/remove operation, or generic broker setter before first user interaction.

The classification remains below `SAFE_OPEN_CANDIDATE` because the two registered names look policy-bearing and their downstream meaning is unresolved. This metadata can persist in process-global memory after the Broker Editor window closes; no remover was found on close.

## Allowed observation boundary

The proposed human test may observe, scroll, expand, select, move/resize, and close the window. Do not edit a cell/value, remove an entry, use Update or Commit Changes, or invoke any save operation. Safety of editing/commit is **not** inferred from this open-only audit.

The external helper requires the exact retail hash, one visible main window with the recovered native menu signature, `--confirm`, and the distinct phrase:

```text
OPEN BROKER EDITOR WITH METADATA REGISTRATION
```

The helper sends only allowlisted command `0x27`; it accepts no arbitrary command ID. Dry-run remains the default. The helper has not been run against a game process.

## Confidence

- **HIGH — CONFIRMED_BY_EXE:** command-to-opener route, two key registry insertions, duplicate-detection/list mutation behavior, broker entry enumeration, and absence of value setters/writers on the mapped open-only chain.
- **MEDIUM — CONFIRMED_BY_EXE:** no direct disk write or XML serializer is called from this mapped path; this is a call-graph absence result, not a runtime file-monitor result.
- **UNKNOWN:** exact intended effect of `__NO_SAVE`/`__NO_CHANGE` elsewhere and whether an indirect/dynamic consumer later consults the metadata.
- **CONFIRMED_BY_RUNTIME:** no Broker Editor test in this phase.
