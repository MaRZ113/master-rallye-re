# TRACK-PORT0 — course delta-port foundation (docs only)

Approved plan: delta-port. PC courses stay the base; only PS2 differences are carried over.
Index of earlier research: [../TRACK_RESEARCH_INDEX.md](../TRACK_RESEARCH_INDEX.md).
This phase changes no code, builds nothing and touches no game data.

## Deliverables
| File | Purpose |
|---|---|
| [registry-schema.json](registry-schema.json) | JSON Schema (draft 2020-12) of the Course Delta Registry v2 |
| [registry-example.json](registry-example.json) | One Turkey3 sample record, validated against the schema |
| [policy.md](policy.md) | Per-aspect channels, coverage rules, evidence gates (G-COLL, PCSX2), trigger criteria, ini keys, budget, pinned inputs |
| [validate_registry.py](validate_registry.py) | Validates a registry file against the schema (stdlib only) |

## Next phase
TRACK-DELTA1: Turkey3 census (T1a/T1b, done). Then the Turkey3 vertical-slice prototype. The full 36-course census (T1-full)
follows the prototype.
