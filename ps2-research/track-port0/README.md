# TRACK-PORT0 — course delta-port foundation (docs only)

Approved plan: delta-port. PC courses stay the base; only PS2 differences are carried over.
Index of earlier research: [../TRACK_RESEARCH_INDEX.md](../TRACK_RESEARCH_INDEX.md).
This phase changes no code, builds nothing and touches no game data.

## Deliverables
| File | Purpose |
|---|---|
| [registry-schema.json](registry-schema.json) | JSON Schema (draft 2020-12) of the Course Delta Registry v2 |
| [registry-example.json](registry-example.json) | One Turkey3 sample record, validated against the schema |
| [policy.md](policy.md) | Delivery channels A/B/C, `PS2Port.ini` keys, evidence gates, performance budget, pinned inputs |
| [validate_registry.py](validate_registry.py) | Validates a registry file against the schema (stdlib only) |

## Next phase
TRACK-DELTA1 (plan stage T1): fill the registry for Turkey3 first, then all 36 courses.
