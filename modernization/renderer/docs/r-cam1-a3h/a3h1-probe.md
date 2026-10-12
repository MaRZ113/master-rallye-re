# R-CAM1-A3h.1 — bounded UI ownership probe

Status: **READ_ONLY_PROBE_READY_FOR_RUNTIME**. This delivers observation only. It does not implement HUD or pause-overlay hiding.

The prior [`reconnaissance.md`](reconnaissance.md) remains unchanged as the historical blocker report. Its main conclusion still holds: the final UI consumer identifies individual packets but no native Egg/sibling owner was proven. This note adds a safe draw correlation probe without upgrading that conclusion.

## Exact-build and observation boundary

The probe is enabled only when the runtime executable matches the existing pristine-retail SHA256 `bf8aef32407eb6552c05045b8abef149f32983cedd9503b865069b444c5f96b4`, Trace is enabled, and the already verified UI consumer hook is installed. On unknown builds, semantic UI observation stays disabled.

It reuses the existing `DrawTextPacket` consumer hook at VA `0x0056D110` / RVA `0x0016D110`; it adds no EXE patch site. At the final `DrawPrimitive` wrapper it records only the verified caller VA `0x0056D7C4` / RVA `0x0016D7C4`. The known UI draw signature is FVF `0x142`; mismatches remain visible in the record rather than being promoted to UI ownership.

The capture-local record correlates frame and draw sequence with the active native consumer scope, raw entity and packet pointers, derived point storage (`packet+0x54`), content-storage pointer (`packet+8`), packet mode, UI epoch, cached race lifecycle generation when available, callsite, primitive type/count, FVF, stage texture pointers and generations, and stage color/alpha/texcoord state where known. The consumer tuple is reread at draw time; mutation inside a scope is recorded as a mismatch. Unknown modes are retained as observations. Unreadable, null, replaced, or missing identity fields receive explicit statuses and do not receive a valid capture-local identity ID.

The per-F10 budget is 1,024 draw rows and 512 unique capture-local identities. Storage is bounded and allocated before drawing; the callback only fills records. Each F10 capture rearms IDs and counters. Metadata reports `complete`, `overflow`, and `unmapped` independently: complete coverage does not imply semantic ownership. A frame-file truncation also downgrades offline analyzer completeness.

When `[Trace] Enabled=1`, the same session's race snapshot optionally reads `Race/PauseMenu/Enabled` through the existing typed race Broker memory reader. It resolves the exact interned key and accepts only a type-tag-0 bool payload of 0 or 1. This is a bounded, read-only memory read; it does not invoke a Broker getter, create an absent entry, or write any value. The result is diagnostic corroboration only. Missing, malformed, unsupported-build, or wrong-thread results remain unavailable/unknown. The probe never uses this bool to classify draw owners.

## What remains unproven

`owner_mapping_status` is intentionally `unmapped`, and `owner_name` is null for every emitted draw. The current probe proves only:

```text
active native UI entity/packet consumer scope -> one observed D3D draw
```

It does not prove:

```text
entity -> Scene/Egg parent -> Hud0 Egg name -> HUD or pause semantics
```

The separate data/resource fact that `PauseMenuTiles` and `PauseMenuChooser` are distinct Eggs does not map their instances to these packets. A paused-only tuple remains a paused-only observation, not proven pause ownership.

The previous exact-build Ghidra research in `research/r-gfx5/ui-group-ownership.md` found no parent/root link at the final consumer. `research/r-gfx5/widescreen-integration.md` explicitly excluded a static `entity+0x50` fallback. That offset is the next narrow static candidate to inspect read-only in Ghidra, together with the entity's submission/list node at `Submit` VA `0x00509680` / RVA `0x00109680` and `SortPerCamera` VA `0x00509970` / RVA `0x00109970`. These are leads only: no owner field offset or type is asserted, and the probe does not read `entity+0x50`.

No D3D method is skipped and no render state, packet, camera, FOV, pause value, or UI entity is written. Existing margin, carousel, camera, and Freecam behavior remains independent of the probe.

## Artifacts

- [runtime-handoff.md](runtime-handoff.md) contains the two-F10 operator capture procedure and pass/fail checks.
- [`../../tools/analyze_ui_ownership.py`](../../tools/analyze_ui_ownership.py) compares normal and manually labeled paused captures without making semantic claims from screen position or pointer equality alone.
- [`../../data/a3h1-ownership-readiness.json`](../../data/a3h1-ownership-readiness.json) is the current machine-readable readiness summary. It deliberately keeps owner mapping unresolved.
- [`build-manifest.json`](build-manifest.json) records the local diagnostic DLL identity. The DLL itself stays in the ignored `.build-msvc` output directory and is not archived or committed.
