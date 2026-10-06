# Engine state cache and reset consequences

**CONFIRMED_BY_EXE:** `StateManager_00570900` creates the following caches.
The singleton+0x24 holder dereferences to this manager; +0 enables caching and
+4 selects its recording/restoration mode. Normal mode commonly equals 2.

| Manager offset | Cache / constructor VA | Device field inside cache |
|---|---|---|
| +0x10 | render states, `0x0058E2D0`, 0xB28 bytes | +0xB24 |
| +0x14 | texture-stage states, `0x0058D7D0`, 0xEE8 | +0xEE4 |
| +0x18 | transforms, `0x0058D070`, 0x4D28 | +0x4D24 |
| +0x1C | textures, `0x0058C100`, 0xC8 | +0xC4 |
| +0x20 | stream/FVF/indices/viewport, `0x0058CBF0`, 0x5C | +0x58 |

Render-state wrapper VA `0x0053F8B0` compares state values in 12-byte records,
records mode/generation metadata and calls slot50/+0xC8 at `0x0053F921` only
when needed. TSS wrapper `0x0053F930` uses 12-byte records and 0x1D0 stage stride;
texture `0x00564EE0` similarly caches bindings. Transform `0x0053F9E0` compares
16 floats inside 72-byte records. Stream `0x00564F60`, FVF `0x00564FB0` and
indices `0x00577090` cache stream0/stride, FVF value, IB/base vertex. Inline copies
of these checks appear in draw and material paths; wrappers alone are not all
state-changing sites.

Initial stream/IB are null, FVF is XYZ (2), viewport is 640x480, z range 0..1.
Transform cache initializes view/projection/texture/world matrices to identity.
Render-state defaults span tables VA `0x006EA8B0`, `0x006EA9E8`, `0x006EAAF8`
(38/33/5 records). CRT initializers `0x0058E6E0` / `0x0058E870` fill runtime
entries omitted by the disk seeds. [defaults JSON](data/state-defaults.json)
preserves the two forms, writer VAs and symbolic memory sources. Notably LIGHTING
defaults to 1, while the traced material methods explicitly set it to 0.

`0x00570BB0` reapplies defaults after device reconstruction; `0x00570C00` restores
working state; `0x0058EA90` applies RS defaults and `0x0058D550` restores transform
defaults. Manager callback `0x0055B450` calls `0x00570BB0` and `0x0053F590` after
successful create/reset. The latter sets a boot projection and unlit baseline.

**STATIC_INFERENCE:** a future proxy's temporary sun/fog/postFX state must restore
the real device state before returning, or maintain a consistent emulated state
model. The game may suppress a restoring Set call because its own cache believes
the old value is still active. Readback must reflect game-visible D3D8 state.
