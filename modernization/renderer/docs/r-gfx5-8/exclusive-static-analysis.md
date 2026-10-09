# Exclusive restore: native mode owner and ordering evidence

## Exact image and method

`CONFIRMED_BY_EXE`: pristine retail `MRallye.exe`, SHA256 `bf8aef32407eb6552c05045b8abef149f32983cedd9503b865069b444c5f96b4`, ImageBase `0x00400000`. Ghidra 12.1.4 was used through the installed local `ghidra_ai_bridge` exporter and PyGhidra. Its program SHA matched the binary. The existing task-local renderer Ghidra database was opened through `getReadOnlyDomainObject`; missing functions were queried in a rollback-only transaction and the program was never saved. New exports/settings are ignored in `scratch-r-gfx5-8/`. No original Ghidra project was modified.

## Address map

| Stable research name | VA / RVA | Proven interface and role |
|---|---|---|
| WindowDeviceCtor_00558D50 | `0x00558D50` / `0x00158D50` | ECX=this, one stack char argument, RET 4; constructs a 0x1B4 owner, vtable `0x0069228C`, publishes primary owner at `0x006F9D80` |
| RetailWndProc_00558E90 | `0x00558E90` / `0x00158E90` | Win32 four-argument thunk; loads ECX from `0x006F9D80`, calls virtual slot 0; DefWindowProcA if null |
| InitializeWindow_005590C0 | `0x005590C0` / `0x001590C0` | ECX=this, one HWND argument, RET 4; adopts or creates HWND, subclasses WndProc, saves style/outer/client |
| HandleWindowMessage_0055A4D0 | `0x0055A4D0` / `0x0015A4D0` | ECX=this, HWND/message/WPARAM/LPARAM, RET 0x10; real virtual message consumer, last RET at VA `0x0055AA51` |
| CreateNativeDevice_0055AB90 | `0x0055AB90` / `0x0015AB90` | ECX=this; copies selected windowed byte, builds PP, invokes virtual mode transition and IDirect3D8::CreateDevice |
| ResetNativeDevice_0055AE40 | `0x0055AE40` / `0x0015AE40` | ECX=this, no stack arguments, RET at `0x0055AEC6`; pre-resource callback, native Reset, backbuffer description, post-resource callback |
| ApplyNativeWindowMode_0055AED0 | `0x0055AED0` / `0x0015AED0` | ECX=this, width/height stack args, RET 8; virtual +4; restores saved style or selects fullscreen/topmost |
| CheckCooperative_0055AF50 | `0x0055AF50` / `0x0015AF50` | ECX=this, no stack arguments; TestCooperativeLevel, conditional recovery |
| DestroyNativeWindowOwner_00559260 | `0x00559260` / `0x00159260` | ECX=this; device release, saved style/outer restoration, original WndProc restoration |
| RendererSingletonCtor_0053EED0 | `0x0053EED0` / `0x0013EED0` | allocates owner 0x1B4 and stores it at singleton +0x20 |
| RendererRecreate_0053F350 | `0x0053F350` / `0x0013F350` | rebuilds device/window owner and reports actual fullscreen state to Broker |
| FrontendFrame_00653080 | `0x00653080` / `0x00253080` | compares Broker DirectX/Mode/Fullscreen to owner+0x1C==0; disagreement triggers selector/recreate |
| SelectFullscreen_00541E90 | `0x00541E90` / `0x00141E90` | selector owner, not HWND owner; updates +0x78 and rebuilds matching setting lists through 0x005423E0 |

Calling conventions above follow ECX and stack cleanup in the instructions. Ghidra's incomplete automatic prototypes label some zero-stack ECX methods `__fastcall`; that is not evidence for an EDX argument. These functions are not called by R-GFX5-8.

## Object lifetime and mode meaning

`CONFIRMED_BY_EXE`: `0x006F9CF0` is the renderer singleton pointer. Its +0x20 references the same primary owner that the constructor publishes at `0x006F9D80`. The live owner is reconstructed during `RendererRecreate_0053F350`; a cached address alone is insufficient.

| Owner offset | Meaning established by consumers |
|---|---|
| +0x00 | vtable at VA `0x0069228C` / RVA `0x0029228C` |
| +0x05 | native window initialization completed |
| +0x06 | device creation completed |
| +0x1C | zero = native fullscreen, nonzero = native windowed |
| +0x24 | active/non-minimized size state; WM_SIZE sets false for SIZE_MINIMIZED/MAXHIDE |
| +0x25 | device/render-ready flag, cleared during size Reset |
| +0x28 | D3DPRESENT_PARAMETERS, width/height at +0x28/+0x2C |
| +0x44 | PP.Windowed DWORD |
| +0x5C / +0x60 | device HWND / focus HWND |
| +0x68 | game-visible device interface |
| +0x164 | saved normal style |
| +0x168 / +0x178 | saved/current outer/client rectangles |
| +0x1AC | previous WndProc when subclassing an existing HWND |
| +0x1B0 | WM_ENTERSIZEMOVE / WM_EXITSIZEMOVE flag |

`CreateNativeDevice_0055AB90` copies selected device setting byte +0xF9 into +0x1C and into PP.Windowed. Zero uses enumerated fullscreen size/format. Nonzero uses the saved normal client and desktop format. It calls virtual +4 (`ApplyNativeWindowMode`) before native CreateDevice. After a successful native CreateDevice, the nonzero branch also reapplies the saved outer rectangle with HWND_NOTOPMOST at VA `0x0055AD13` / RVA `0x0015AD13` (CALL to SetWindowPos; argument setup precedes it). This is game work after the proxy's wrapped creation has returned.

`ApplyNativeWindowMode_0055AED0`: nonzero restores saved +0x164 style via SetWindowLongA, then SetActiveWindow. Zero sets style `0x90080000`, calls SetWindowPos(HWND_TOPMOST, width, height, flags 0x40), then SetActiveWindow. The vtable entry is `0x00692290` / RVA `0x00292290`. This mode polarity is confirmed statically, rather than inferred from visual geometry.

## Two separate Reset paths

`CONFIRMED_BY_EXE`: `HandleWindowMessage_0055A4D0` handles WM_SIZE and WM_EXITSIZEMOVE. If +0x24 is active, +0x1C is windowed, and interactive resizing is complete, it updates saved outer/client, compares actual dimensions, clears +0x25, writes PP width/height, and calls `ResetNativeDevice_0055AE40` at VA `0x0055A619` / RVA `0x0015A619`. It does **not** call TestCooperativeLevel first. Failure calls the error reporter with `0x8200000C` at VA `0x0055A62B` / RVA `0x0015A62B`. This message branch finishes before forwarding to the prior WndProc/DefWindowProcA. Activation, focus, and WM_ACTIVATEAPP do not perform a pre-Reset readiness recovery in this consumer.

The separate frame/device readiness path `CheckCooperative_0055AF50` calls TestCooperativeLevel at VA `0x0055AFB3` / RVA `0x0015AFB3`. DEVICELOST returns unavailable without Reset. DEVICENOTRESET refreshes desktop format only when +0x1C is windowed, then calls Reset at VA `0x0055B015` / RVA `0x0015B015`. The native fullscreen branch performs restore/show/maximize ShowWindow calls **after** this recovery Reset. A WM_SIZE received during an earlier restore is therefore a different control-flow entry.

Reset itself calls pre-resource virtual +0x14, native device vtable +0x38 at VA `0x0055AE57` / RVA `0x0015AE57`, gets backbuffer/description, and post-resource virtual +0x18. Concrete callbacks `0x0055B410` / RVA `0x0015B410` and `0x0055B450` / RVA `0x0015B450` handle dynamic resources/baseline state. No new resource hook was introduced.

The documented D3D8 contract distinguishes unavailable DEVICELOST from recoverable DEVICENOTRESET and requires cooperative queries on the creating thread. The surviving [Microsoft D3D8 reference](https://learn.microsoft.com/en-us/previous-versions/ms889731(v=msdn.10)) is an archived CE .NET page; its lost/not-reset distinction is also present explicitly in this PC retail code. It does not prove this user's Windows driver/focus timing.

## What the human trace establishes

The user-supplied R-GFX5-7 trace summary reports successful true Exclusive 640×480 startup and initial Reset, then iconic/zero-client DEVICELOST. During restoration it reports style `0x16CF0000`, ex-style `0x108`, outer 640×480, client 624×441 and GetFocus=0; game Reset 624×441 is normalized to native 640×480/Windowed=FALSE and returns DEVICELOST. No independent raw-session audit was possible here.

The 16×39 discrepancy is the observed nonclient geometry, not a hardcoded border constant. R-GFX5-7's Exclusive proxy path performs no post-Reset style/placement write. Static retail paths can restore a saved decorated style during mode application or teardown; the native D3D runtime/Windows can also participate in style restoration. The old trace does not identify the specific writer or its stack.

`STRONG_HYPOTHESIS`: if the game retains +0x1C=windowed while the proxy creates a native Exclusive device, an early restored WM_SIZE can take the immediate windowed Reset path while focus/native readiness is incomplete, bypassing the game's separate cooperative recovery path. This explains the requested client dimensions and fatal failure. The live mismatch and readiness-before-Reset remain `UNKNOWN`; input PP and output Windowed alone do not prove the owner byte at the instant of failure.

## Safe observation and correction boundary

R-GFX5-8 reads mode/flags only on the exact pristine image. Both pointer chains must agree; owner vtable must be image+0x29228C; owner HWND must equal the observed game HWND; boolean fields and PP.Windowed must be in range; all reads use the existing guarded safe_copy. Nothing is written. Recreate is handled by validating fresh pointers on each bounded event. Synthetic memory tests cover mismatched owner/HWND/vtable, unknown build, invalid flags, overflow/unreadable addresses, and immutability.

For modified EXEs, this new owner observation remains unknown. FOV, CPU-culling, vehicle semantics, UI and other existing feature-local checks are unaffected. The generic message/readiness observer still works and captures module/return-RVA stacks. No new whole-EXE SHA profile is required for existing features.

A one-byte write is insufficient to prove coherent ownership: +0x1C is sourced from a selected setting; its virtual transition changes style/placement/focus; PP and resource lifetimes also participate; the Broker frame can recreate an inconsistent owner. A safe synchronization would need these owners and timing verified together. Consequently this pass does not call `0055AED0`, `00541E90`, write +0x1C, suppress WM_SIZE, or hide a genuine native failure.

Next observation: correlate the first style-changing stack, pre-WndProc WM_SIZE, read-only owner mode, native readiness immediately before Reset, and the first activation/focus events. If readiness is DEVICELOST in the nested size path, early Reset is confirmed. If it is DEVICENOTRESET yet Reset still fails, investigate resources/focus and native failure instead. If the game flag is fullscreen, reject the windowed-owner hypothesis and inspect the actual captured call path. [Human tests and failure capture](runtime-handoff.md).
