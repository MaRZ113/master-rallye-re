# Future leverage

| Tool/branch | Leverage | Difficulty | Runtime risk | Why |
|---|---|---|---|---|
| Debug window/log capture | HIGH | low | low if passive | Loader/cache/build/shader stages become direct runtime evidence |
| Broker Editor | HIGH | medium | medium | Typed broker oracle may expose semantics across systems; edits are live and saving is separate |
| Flow Builder/FL-to-SFL | MEDIUM-HIGH | medium | high for build/convert | Original conversion/generation can make controlled samples; opener has no mapped retail menu item |
| BuildData | MEDIUM-HIGH | medium | high | Reuses original loaders and reports failures, but recursive and overwrite-capable |
| Game/Scene XML serializer | MEDIUM | medium | high | Exact save filters/serialization are known; outputs use CREATE_ALWAYS |
| Egg/Particle/Marker editors | MEDIUM | high | unknown | Could expose authoring semantics; internal operations and writes remain unmapped |
| 0x848 tree/editor object | UNKNOWN | high | unknown | Object and generic dispatch are real; identity is not established |

## Best-supported next branches

1. Isolate Menues/Enabled and DebugWindow/Enabled in a retail copy.
2. Capture passive startup logs and correlate them to loader xrefs.
3. Find a legitimate Flow Builder entry path before testing selection or writes.
4. Inventory Broker Editor read-only behavior before attempting any mutation.
5. Revisit BuildData only after exact start path and legitimate invocation are known.

No follow-up branch has been started.
