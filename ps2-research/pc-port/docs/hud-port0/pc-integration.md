# PC native packet ownership, state and safety

The supported pristine PE is `MRallye.exe`, SHA256
`bf8aef32407eb6552c05045b8abef149f32983cedd9503b865069b444c5f96b4`,
3121214bytes, ImageBase0x00400000. Existing REA/Ghidra exact-retail dossier in
`modernization/renderer/docs/global-hud-hide/implementation.md` identifies UI
consumer0x0056D110..0x0056DB0F. This pass reused that evidence and source; it did
not run another PC executable decompilation session or install hooks.

## Exact available native boundary

```text
original PC en2d entity
 -> entity+0x4C packet
 -> packet+0x08 content allocation; +0x54 point; +0x68 mode
 -> existing current consumer scope/identity validation
 -> DrawPrimitive return RVA0x0016D7C4, triangle list, FVF0x142
 -> original native draw or existing user-requested HUD suppression
```

FVF0x142 means XYZ + diffuse color + one UV pair, not XYZRHW. Native WORLD,
VIEW and UI projection participate. The same consumer renders frontend and
race HUD. Its callsite alone is not a widget or race admission certificate.

`MarginIdentity` and captured ownership validate entity,packet,point,storage,
mode, UIepoch, racegeneration and resource generations. Current implementation
does not expose an independently proven stable widget name, authored bank/key,
ownerType or a shared cross-packet widget root. The new HUD design must close
that semantic relation without guessing unknown native fields.

## Live captures: actual forwarding versus suppression

| Capture | Proxy SHA256 | Current packet stream |
|---|---|---|
| `frame-10916-d1-00002579.jsonl` |`0bd68583e87378931c57a530c5673201bcf8017f593075bd1fe7029e5628c72f`|268verified UI draws,268forwarded, all returned0;32packet identities, complete/no drops|
| `frame-42216-d1-00026331.jsonl` |`6edc2426e2602545121f16959cdbb2055fb205a907b36173cb85a447b7051deb`|268verified UI attempts,0forwarded; all268suppressed by H;32packet identities, complete/no drops|

Both captures report `gameplay_running`, exact retail and certified active race.
Each ownership row has `owner_mapping_status=unmapped`, `owner_name=null`.
Their0HRESULT values in the hidden frame are proxy suppression returns, **not**
268successful native submissions. The visible frame supports a real native UI
path but still does not attribute a draw to the speedometer/minimap by name.
Exact hashes and summary records are in `source-evidence.json`; raw captures
remain external. No screenshot is promoted to a semantic packet classifier.

The visible frame's tracked original UI state is:

| State | Observed values |
|---|---|
| ZENABLE |0on248draws;1on20draws — do not assume all HUD lacks Ztest|
| ZWRITEENABLE |0on268draws|
| ALPHATESTENABLE |0on268draws|
| ALPHABLENDENABLE |1on268draws|
| SRCBLEND / DESTBLEND |5/6 = SRCALPHA / INVSRCALPHA|
| CULLMODE |3 = CCW|
| Stage0 COLOROP/ALPHAOP |4/4 = MODULATE; ARG1diffuse(0),ARG2texture(2)|
| Stage1 COLOROP/ALPHAOP |DISABLE in ownership sample; bound texture presence alone is not an active pass|

These are `LIVE_PC_PROXY_OBSERVATION` of original/effective tracked states,
not a separate GPU debugger read of every register. The captured effective
state includes existing filtering/PreserveMargins policies; the immutable
renderer already distinguishes logical and effective state. A future private
sprite texture must preserve/restore exact effective native bindings and not
write game-facing logical state.

## Protected retail source comparison

Read-only `Data.sma_unpacked/DataScene/Hud/Hud0.xml` is124360bytes, SHA256
`91616caa529fb4762e8e263f58bfe0f35ee5aebf127e8ba2fc3014a677ea4dbf`.
It authors the named dial/counter/GPS/progress/damage elements described in the
feature matrix. These names are an intended mapping oracle; they are not a
proved runtime pointer association in the current captures.

`DataGx/Hud/hud-template.dxb`,1732bytes,SHA256
`63d0f959a342a6c8b6f5ed5e7327de00ce73e5c7449bc844a9a4329859e865c0`,
has the same F001/125 header as PS2 PSB but **different record grammar**.
Existing PS2 parser fails closed with `Invalid or truncated resource-name length`.
No guessed PC DXB decoder was introduced. The future narrow plate pilot must
verify the native PC sprite geometry/UVs rather than pretending this parser
already reads both formats.

Existing read-only Course SDK DXT reader validates the original PC dial
`hud-template_000_000.dxt` as128x128BGRA, alpha0..255/255distinctvalues;
SHA256 `73592ae3d27d7f5592d0e7a3d6cadc0f0f23c456904c4b95a86fcf17673820ee`.
PC needle16x64 and original rank/damage texture facts are separately recorded.
Stored alpha and filenames cannot authorize a draw override.

## Performance and lifecycle invariants to preserve

The committed HUD fix in `visual_wrappers.cpp` calls
`live_race_hud_context()` at most once per Trace/D3D frame. That routine reads
typed native/Broker race,scene,pause,player context, not a complete telemetry
feed of speed/RPM/gear/damage/progress. `RaceHudContext` has no such value fields.

Per-draw identity/callsite/renderthread/device/scene/context checks and strict
Clean View/Freecam admission remain required. Re-reading Broker for every UI
glyph would recreate the prior lag defect. First plate pilot needs no new
per-draw game-data sampling because it retains the original PC counter draws.

On Reset, raw escape, consumer ownership loss or missing/ambiguous semantic
identity, Stock must remain effective. Private textures must have explicit COM
ownership, reset/device-loss handling and bounded allocation; never retain a
raw entity/packet beyond its current epoch/lifetime. Native draw HRESULT must
survive restoration. A failed binding restoration must block further mutations
and report the real failure, following existing extension transaction safety.

