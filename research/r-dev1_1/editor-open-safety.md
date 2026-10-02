# Editor open-only safety matrix

| Tool | Retail global opener | Open-only evidence | Classification | Runtime action |
|---|---:|---|---|---|
| Flow Builder | `0x30` → `00662D90` | Window/layout/menu setup only on the mapped open path; no automatic file or broker write found | **SAFE_OPEN_CANDIDATE**, medium-high | May open and inspect; do not use local actions 0–2 or 8–10 |
| Broker Editor | `0x27` → `0065E990` | Ensures two unresolved shared broker entries before display | **DO_NOT_RUNTIME_TEST** | Excluded pending registry meaning |
| Egg Editor | `0x2E` → `00657FD0` | Creates/populates live list/model state; disk writer not found, but shared side effects not fully bounded | **UNKNOWN** | Excluded |
| Marker Editor | `0x3B` → `0065B870` | Populates live marker/editor state; disk writer not found, but state/camera/broker side effects not fully bounded | **UNKNOWN** | Excluded |
| Particle Editor | `0x4A` → `006557C0` | Populates live particle records and calls configuration/broker helpers; no disk writer found, semantics incomplete | **UNKNOWN** | Excluded |
| Generic tree/object editor | `0x3F`, indexed `0x40–0x49` | Opens live parameter editor; collection/UI and broker stateful; maximum 10 | **DO_NOT_RUNTIME_TEST** | Excluded |
| BuildData | `0x58` → command object `005B2960` | Immediately runs recursive resource walker/loaders; cache writes possible | **WRITE_CAPABLE** | Never include in open-only tests |

“No disk writer found” is not equivalent to “safe”: shared in-memory changes must also be bounded. Game and Scene XML Save commands are excluded because their serializers reach create-always file writers. No Broker Editor runtime candidate is proposed.
