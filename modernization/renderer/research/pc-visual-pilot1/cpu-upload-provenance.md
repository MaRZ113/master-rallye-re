# CPU upload provenance follow-up

Date: 2026-10-09
Scope: code-only continuation of PC-VISUAL-PILOT1; no new game capture and no draw-state override.

## Audit input and interpretation

The two supplied audit records cover complete frames 306081 and 329935. Each reports 128 attempted probes, zero readable probes, and `buffer_not_safe_for_readonly_probe` for every candidate. All sampled vertex and index buffers had `D3DUSAGE_WRITEONLY` (`Usage=8`) in `D3DPOOL_MANAGED` (`Pool=1`). The audit hashes are `949e5f748db1c283acb4c5a0367a6ff1d22ea86a96a5fb72dcd5544a239458f4` and `97ac9e3d8682179fb77b40545a014b362aab39ffecf56c7e5587fcbfadb68d85`.

These captures contain no geometry fingerprint. `TARGET_IDENTITY_NOT_FOUND` means **no content evidence because every probe was blocked**. It does not show that bush01 was absent, nor does the externally supplied course label establish course identity inside the renderer. No fallback READONLY lock or material override was attempted.

## Implemented observation path

When the existing foliage diagnostic is explicitly enabled, the D3D8 device wrapper now wraps vertex and index buffer interfaces returned by `CreateVertexBuffer`, `CreateIndexBuffer`, `GetStreamSource`, and `GetIndices`. The generated interface source is updated through `tools/generate_interfaces.py`, so regeneration preserves the custom forwarding contract. The wrapper records the resource generation and the device-call return address that created it. Existing buffer `Lock` and `Unlock` calls remain the only source of mirrored bytes.

For a successful writable lock, the proxy records the byte interval and flags. At `Unlock`, it copies the still-locked CPU pointer into a bounded mirror before forwarding the native unlock. The mirror tracks initialized intervals, a monotonic revision, resource generation, and invalidation reason. `D3DLOCK_DISCARD` clears prior interval coverage; partial writes cover only their written intervals. A probe may read the mirror only when its entire draw range is covered and its kind/generation still match. The original probe may continue to use a bounded READONLY lock for buffers already proven safe as managed/system-memory, non-dynamic and non-WRITEONLY.

The implementation never adds a READONLY lock to WRITEONLY or dynamic buffers, never reads GPU memory, and never changes submitted draw state. It preserves the native Lock/Unlock HRESULTs and forwards the original call once.

## Fail-closed lifecycle

Mirror coverage is revoked or rejected on failed `Unlock`, unknown or contradictory lock flags, untracked unlock, nested successful lock, unavailable/out-of-range data, excessive interval fragmentation, successful `ProcessVertices` writes, successful device `Reset`, successful unknown buffer QI/raw-interface escape, proxy registration/allocation failure, proxy-count exhaustion, and resource-generation mismatch. If a CPU copy or per-frame budget fails, coverage for that write interval is removed so a later probe cannot hash stale bytes; other independently covered intervals remain usable. An unknown successful device/root QI disables foliage provenance for the affected device set/session so later raw-device traffic cannot silently enter the evidence stream.

The wrapper registration is atomic across raw/proxy lookup maps. If registration cannot complete, the API's raw resource reference is returned with correct reference balance, and any existing mirror for that identity is invalidated. A stale proxy cannot donate bytes to a new resource generation.

Bounds are explicit: 8 MiB per buffer mirror, 32 MiB per device, 16 MiB of copied upload bytes per D3D frame, at most 4096 initialized intervals per buffer, 8192 tracked proxy/resource entries, and the existing 128-draw / 1 MiB F10 probe budget. Bound buffers retain their CPU mirror after the application's proxy reference is released; unbinding plus proxy release discards unowned mirror storage. Native COM resources are not retained solely to keep diagnostic bytes alive.

## Provenance boundary

The recorded creator address and buffer generation can connect a future geometry fingerprint to its D3D resource lifetime and creation callsite. They do **not** by themselves prove which course file or named material owns the resource. The course name in the prior audit remains `USER_RUNTIME_OBSERVATION`; no engine-derived course/resource owner, persistent draw partition, or live negative control has been established yet.

Next runtime evidence, if requested in a later step, must come from this rebuilt diagnostic proxy. It should first establish complete CPU-write coverage and compare candidate draw fingerprints against the frozen France1 bush01 source signature. If that does not establish course ownership and a stable native-call partition, retain `BLOCKED_ON_DRAW_IDENTITY`; do not broaden the classifier or enable an override.

## Validation boundary

The synthetic native tests cover partial/discard writes, range coverage, failed unlock, unknown QI, proxy-registration collision, binding retention, unbinding, Reset, `ProcessVertices`, resource-generation mismatch, and the original stock probe path. These establish the local mirror contract only. They are not a PC gameplay capture and do not change the two supplied audits.
