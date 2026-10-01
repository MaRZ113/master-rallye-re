# Hypothesis ledger

The JSON file is the authoritative machine-readable ledger. These are deliberately unresolved statements, not new facts.

| ID | Statement | Confidence | Cheapest falsification |
|---|---|---|---|
| H-RESOURCE-001 | Retail requests try a loose path before archive fallback; exact precedence among ambiguous roots/archive names still needs tracing. | HIGH for loose-first, MEDIUM for root ordering | Break at `0064D530` with a duplicate loose/packed resource in a disposable install. |
| H-BROKER-001 | XML `Value` records populate the shared 0x1c broker-entry form and use `Type`/save flags for access and persistence. | MEDIUM-HIGH | Trace one XML record through the generic parser into a broker entry. |
| H-SAVE-001 | `SavePlayerState` and `SaveOptions` select different broker serialization passes. | MEDIUM | Find all readers of the flag bits and follow an actual writer. |
| H-BUILDDATA-001 | Retail's BuildData callback may be exposed through an editor/development menu. | LOW-MEDIUM | Resolve the callback table owner and menu/command dispatch. |
| H-GHOST-001 | RecordReplay/RecordSpline are producer-side counterparts to GhostPlayback/GhostCar. | LOW | Trace recording xrefs into file APIs and compare the playback record layout. |
| H-ROUTE-001 | LastMarker, SplitPoint, WrongWay, and pace-note keys participate in distributed per-car route state. | LOW-MEDIUM | Find active-race broker reads/writes and watch one car's values across route events. |
| H-NETWORK-001 | Port 22222 serves race synchronization/discovery and might use up to eight indexed car records. | MEDIUM for sync relation; LOW for capacity | Trace socket send/receive and indexed loop bounds. |
| H-MATERIAL-001 | New alpha-test shader families distinguish cutout from blended alpha; environment variants add separate stage state. | MEDIUM | Trace representative material values through selector and D3D8 render-state calls. |

Each entry records evidence for/against, builds examined, static follow-up, runtime follow-up, and status in [`hypotheses.json`](hypotheses.json). No hypothesis was silently upgraded to a confirmed fact during documentation.
