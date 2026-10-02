# Reachability classification

| Feature | Class | Reason |
|---|---|---|
| Main Reset / Exit | **A — ORIGINAL_VISIBLE_ROUTE_RECOVERED** | Both have native main-menu items in all builds. |
| Debug window | **A — ORIGINAL_VISIBLE_ROUTE_RECOVERED** | Startup path is driven by Menues config; owner runtime confirms true opens it. It is a development window, not an editor command sender. |
| Broker Editor opener | **D — HANDLER_PRESENT_BUT_ORIGINAL_SENDER_UNKNOWN** | Main switch/open function exist; no in-binary sender recovered. |
| Egg Editor opener | **D** | Same. |
| Flow Builder opener | **D** | Same; local Flow menu is post-open. A separate helper is supplied for a controlled retail open-only test. |
| Marker Editor opener | **D** | Same; pending-open flags have no recovered producer. |
| Particle Editor opener | **D** | Same; pending-open flags have no recovered producer. |
| Generic tree/object editor | **D** | Global `0x3F` and indexed family exist; no sender recovered. |
| BuildData | **D** | Retail `0x58` constructs/executes a command object; no original sender recovered. Earlier-build match absent in current evidence. |
| Game XML open/save | **D** | Subdispatcher handlers exist; no UI sender recovered. Save is write-capable. |
| Scene XML open/save | **D** | Subdispatcher handlers exist; no UI sender recovered. Save is write-capable. |
| Local actions inside an opened tool | **A for the local item→local WndProc route** | Their own dynamic menus route actions after a window exists; this does not alter class D for global openers. |

No feature is assigned **B** because no early-only opener UI was recovered. No feature is assigned **C** because the pending editor-open helper has no recovered flag producer. No handler is assigned **E** because the global dispatch switch still references it.

The D classification means “no sender found in the analyzed executable,” not “Steel Monkeys never had one.” An external dev harness or a component omitted from these four binaries remains possible but unproven.
