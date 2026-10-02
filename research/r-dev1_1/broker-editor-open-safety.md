# Broker Editor open-only safety

## Decision

**DO_NOT_RUNTIME_TEST in this phase.** Opening does not show a direct disk writer or explicit broker value commit on the mapped path, but it does perform unresolved shared broker registry operations before first display. The phase's bar is stronger than “no `WriteFile` call seen.”

## Open chain (retail)

```text
main dispatcher 005B0990, ID 0x27
  → opener 0065E990
  → duplicate HWND check
  → CreateApplicationWindow
  → create/initialize controls
  → ensure two broker entries
  → local menu/title and size
  → populate broker list
  → show
```

Constructor `0065E650` allocates internal UI/record objects, references `DataEditors/BrokerEditorHelpInfo.txt`, and reads it through generic resource reader `0064D9B0`. Population functions `0065F9A0/0065FA20` iterate broker data. The referenced help file was not found in supplied corpus views.

Before menu/population, opener calls `004D8EC0` and then `004D54A0` for two globals (`0070AEE8`, `0070AEEC`). `004D8EC0` resolves the broker singleton. `004D54A0` searches a linked list and appends a 12-byte node/increments a count if the key is absent. The two keys' semantic names and whether node creation is merely indexing or changes shared behavior are not proven.

No disk serialization, XML save, reset, remove, commit, or delete was found on the open-only chain. However, an in-memory structural write occurs or may occur, so this does not satisfy the user's safe-open criterion. Do not test edits or open this window until the registry calls are resolved. Its Commit Changes action is a separate local command and persistence remains a separate Game/Scene XML save path.
