# R-DEV1.2 known unknowns

1. **Foreground callback dispatch.** Retail `005AFAF0` calls `005AF9F0` and then USER32 `SetForegroundWindow`, but its virtual/event-table dispatch source was not identified. The exact Windows message/interface is unknown.
2. **Restore guarantee.** Open Game, Reset Game, Open Scene, and Reset Scene call `005AF970` before state operations; none directly calls `005AF9F0` as a normal epilogue. Runtime evidence is needed to establish when and whether the foreground callback restores windows after each operation.
3. **Editor-local state preservation.** The four flags encode only whether an HWND was open. Selection, scroll, tree expansion, selected broker key, geometry, and dirty/edited object state are not encoded. Owner objects may retain or rebuild some of these details; that remains unknown.
4. **8.4.1 editor lifecycle.** The pristine 8.4.1 build has `Editing/EditorsOpen` helpers, but the 9.3.1+ `+0x44..+0x47` snapshot/restore pattern was not matched. Do not assign the later application layout to 8.4.1.
5. **`__NO_SAVE` policy.** The Broker Editor opener interns this string-ID in the broker key registry. No serializer-side consumer testing that ID was recovered. Exact save suppression behavior is unknown.
6. **`__NO_CHANGE` policy.** The opener interns the distinct ID in the same registry. No mutation guard/read-only consumer was recovered. Exact change suppression behavior is unknown.
7. **`__IGNORE` policy.** The retail string-ID object exists but is not registered by Broker Editor and has no additional direct retail code consumer in the recovered references. Its actual role remains unknown.
8. **Dynamic sentinel consumers.** The static pass did not prove that no dynamically constructed key or external development tool consults the three IDs. No runtime edits or saves were attempted.
9. **Registry lifetime/removal.** `004D54A0` adds an interned key node when missing. No node removal on Broker Editor close was found. Whether the manager is reset or destroyed at other boundaries is only partially mapped.
10. **Lazy global manager initialization.** `004D8EC0` can allocate an empty manager/list if needed. The normal runtime timing of that lazy branch and whether a first-ever editor open reaches it were not tested.
11. **Broker Editor editing and commit.** This phase covers open-only enumeration. Commit Changes, Remove, Update, XML/Game/Options/PlayerState save behavior, and dirty-state ownership remain unsafe/unmapped for runtime use.
12. **Help resource availability.** Owner construction references `DataEditors/BrokerEditorHelpInfo.txt`; whether each supplied retail install copy contains the file and how a missing file is presented was not tested.
13. **Open-path file system proof.** Absence of writes is based on the mapped static call graph and import/callee evidence. No runtime file monitor was used.
14. **No human runtime tests.** Flow Builder and Broker Editor plans are prepared, not performed. No runtime result is claimed.
