> **R-DEV1.2 resolution note:** the editor-state producer and Game/Scene lifecycle callers are now mapped; `Editing/EditorsOpen` is mapped to Marker/Egg contexts. See `research/r-dev1_2/editor-lifecycle.md`. Unresolved callback dispatch and editor-local state details remain listed below.

# Known unknowns after R-DEV1.1

1. **Original developer sender.** No in-binary native menu, dialog, accelerator, keyboard, toolbar, context-menu, or generated WM_COMMAND sender for hidden global editor IDs was found. Whether an external Steel Monkeys harness sent them remains unknown.
2. **Early runtime menu behavior.** The current 8.4.1/9.3.1 corpus EXEs have whole-file SHA mismatches. Human inventory using exact expected builds is still needed; static main builders show only Reset/Exit.
3. **Menues runtime identity.** Owner confirms the flag-isolation outcome, but tested EXE version/hash, capture, and full config diff were not supplied.
4. **DebugWindow/Enabled.** Key/default exists without consumer xref and had no observed effect in the tested setup. Whether it is redundant, stale, or consumed indirectly remains unknown.
5. **Capability class provenance.** Used virtual slots return true in all four builds. The exact factory/class identity and whether another capability object participates elsewhere are unresolved.
6. **Pending editor opens.** Four app bytes for Marker/Particle/Broker/Egg are consumed and cleared, but no setter/producer was recovered.
7. **`Editing/EditorsOpen` membership.** Integer increment/decrement and editor camera/view bookkeeping are mapped; exact window membership and abnormal-close cleanup are not.
8. **Broker Editor open side effects.** Two unknown broker keys may cause 12-byte registry-node insertion; their semantics and runtime consequence need static resolution before any open test.
9. **Other editor open side effects.** Egg/Marker/Particle do not show an obvious writer in reviewed paths, but all live object/broker/list side effects were not enumerated.
10. **Generic editor ownership.** Ten-slot limit is explicit; indexed IDs' full add/remove ownership and teardown are incomplete.
11. **BuildData earlier history.** No equivalent `0x58` switch handler was matched in three earlier programs; equivalent behavior may be reachable by another path or use a different implementation.
12. **Tool destruction.** Duplicate detection and close commands are mapped, but full destructor order and owner release paths were not reconstructed.
13. **Egg Edit Method labels.** Two retail data pointers remain unresolved; not relevant to global sender reachability.
14. **Prior early-binary provenance.** Existing demo decompilation derives from Ghidra projects opened on `RESEARCH_PATCHED_COPY` inputs. The fresh 8.4.1/9.3.1 corpus binaries are now authoritative for new analysis. Exhaustive comparison to the missing old files remains unavailable.
