# R-CAM1-A3j.4a — live RaceLine preview

Runtime update: the accepted A3j.4a.1 session `session-20261011-113911-34600.jsonl` and frame `frame-34600-d1-00004729.jsonl` confirm the 448-record native snapshot, ordinal-1 Freecam selection, and scene invalidation. The remaining compile/static-only wording below describes the original handoff. Physical placement remains unverified; see [physics-commit-probe.md](physics-commit-probe.md) for the current commit gate.

**Status:** `ROAD_TARGET_PREVIEW_READY_FOR_RUNTIME` (build/static evidence; the new runtime path still needs one human session). This is a read-only destination-selection component. It does not expose or perform teleport.

## Live collection seam

The exact pristine retail image is `MRallye.exe`, 3,121,214 bytes, SHA-256 `bf8aef32407eb6552c05045b8abef149f32983cedd9503b865069b444c5f96b4`, PE32/I386, ImageBase `0x00400000`. VA and RVA below are therefore separated by `0x00400000`.

`ResetManager_Recovery_004CCC90` (VA `0x004CCC90`, RVA `0x000CCC90`) resolves its `RaceLine` object through the native typed registry. At VA `0x004CCCA6` / RVA `0x000CCCA6` it forms the reference at `[ESI+0x54]`, passes it to `0x004E51C0`, then calls `0x004E4D20` at VA `0x004CCCB1` / RVA `0x000CCCB1`. The getter uses that bound reference to return the active list object. Its begin/end fields are at object offsets `+0x04/+0x08`; the stock recovery path consumes contiguous `0x48`-byte records and reads packed float32 XYZ at `+0x38`. The exact 16-byte call context and call target were checked against retail `.text`.

The optional wrapper calls the real getter first, preserves the getter's register and flag results around the observer, then copies only the bounded list. It rejects unreadable or misaligned bounds, any extent other than 448 records, non-finite positions, an extent overflow, and begin/end changes during the copy. It retains no native list or record pointer. `RaceLine` order is the marker ordinal; the copied index is reported as `0..447`. The source object is available at this native recovery seam, not through an arbitrary D3D callback.

The existing current-race certificate binds the snapshot to race generation and owner lifetime. The renderer invalidates the snapshot when that identity changes or the camera lifecycle is cancelled. A getter copy is accepted only while the same certified race owner remains current before publication. The route hook is installed only with `RoadTargetPreviewEnabled=1`; the three physics observer hooks and three clear-writer hooks are controlled by `Enabled=1`.

## Selector and F10 output

`road_target::nearest_marker` is a pure, deterministic function over a renderer-owned fixed-size snapshot. It ranks by horizontal XZ distance, reports Y difference and full XYZ distance separately, applies `RoadTargetPreviewRadius` as a horizontal diagnostic search bound, and picks the lowest ordinal for exact/effectively equal-distance ties. A tie whose candidate elevations differ is rejected as `height_separated_horizontal_overlap`. Snapshot generation, owner lifetime, course gate, count, stride, position offset, native source and finite coordinates are checked before selection.

`GameFov::camera_json()` includes a `road_target_preview` object in the existing F10 frame diagnostic. It reports native source, scene identity, route count/layout, generation/owner, sequence, position fingerprint, Freecam position, selected ordinal/XYZ/distances, radius and an explicit `physical_placement_verified:false`. A route candidate means only that a nearby live route sample was selected; it says nothing about pavement footprint, ground contact, foliage collision or chassis clearance. No static XML fallback exists. Until the normal stock recovery getter has run in the current race, the preview reports unavailable with its concrete reason.

## Evidence boundary

`CONFIRMED_BY_EXE`: exact getter callsite, target, registry lookup sequence, route object begin/end layout, record stride, and position offset. The complete call and clear contexts are also covered by a PE `.text` regression test when the pristine executable is available.

`CONFIRMED_BY_EXISTING_RESEARCH`: France1 has 448 ordered RaceLine positions; the existing A3j.3a observer captured one successful ordinary stock recovery. The source/runtime position comparison and ordinal 2 remain static inference; this component does not claim that ordinal was selected by the game.

`UNPROVEN`: live snapshot contents/fingerprint and F10 selection have not yet been observed in a runtime session; the native list's allocation lifetime outside the bounded getter-time copy is not inferred from a static pointer; physical destination safety is not established.
