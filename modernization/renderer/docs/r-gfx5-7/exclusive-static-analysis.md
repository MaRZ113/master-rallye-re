# Exclusive fullscreen: static owner and runtime unknowns

## Exact-build basis

Static analysis used the pristine retail `MRallye.exe`, SHA-256 `bf8aef32407eb6552c05045b8abef149f32983cedd9503b865069b444c5f96b4`, in Ghidra 12.1.4 through the local GhidraBridge. The database and exports are task-local ignored scratch data; no executable bytes or Ghidra project outside the renderer scratch directory were changed.

## Native window-mode owner

`FUN_0055AB90` at VA `0x0055AB90` / RVA `0x0015AB90` copies a selected display-setting byte into the renderer/window object at offset `+0x1C`. It branches on that byte when choosing the dimensions and format used for device setup: zero selects the enumerated display mode; nonzero derives dimensions from the stored normal-window rectangle and uses the associated windowed format. The function then reaches the game's indirect D3D8 device-creation call (the existing renderer map places the call at VA `0x0055ACD7` / RVA `0x0015ACD7`).

`FUN_0055AED0` at VA `0x0055AED0` / RVA `0x0015AED0` is a `__thiscall` transition method using the same object layout and HWND at `+0x5C`. If byte `+0x1C` is nonzero, it restores the saved window style at `+0x164` and activates the window. If zero, it sets the visible-popup style `0x90080000`, applies the supplied fullscreen dimensions with `SetWindowPos`, and activates the window.

Together these exact-build instructions confirm that `object+0x1C` distinguishes the game's normal-window branch from its fullscreen-window branch. The evidence supports interpreting it as the game's windowed/fullscreen mode byte (`CONFIRMED_BY_EXE`). The static analysis did not establish a direct caller for `FUN_0055AED0`; its transition is likely reached through an indirect dispatch. Nor did it prove which live object instance is associated with a particular wrapped device at the time of the reported loss.

## Why this is not yet a causal fix

The user-reported failure chain is: true Exclusive CreateDevice succeeds, the first normalized Reset succeeds, then after frames `TestCooperativeLevel` returns `D3DERR_DEVICELOST` (`0x88760868`), the game's subsequent Reset also fails with DEVICELOST, and the game reports Error 2010. Earlier human traces also reported a 1920×1080 target followed by a 1904×1041 game Reset request, and a 640×480 target followed by 624×441. Both differences are 16×39; this is historical runtime evidence consistent with decorated outer/client dimensions, but it is not a captured causal transition for the current candidate.

The mismatch between proxy-selected `Windowed=FALSE` and a game object still holding the windowed branch is a `STRONG_HYPOTHESIS`. The static owner makes that hypothesis testable, but there is no new trace showing a style/activation transition or the `+0x1C` value immediately before the first DEVICELOST. A proxy-only COM wrapper does not receive the owning game object pointer as a supported argument. Writing a guessed pointer or forcing the byte would risk altering unrelated window ownership and reintroducing Reset reentrancy.

No game-side byte write, hook, style change, fake HRESULT, fallback to Borderless, or internal retry was added. `game_windowed_flag_0x1c` is explicitly reported as null with reason `no_validated_runtime_pointer_owner`. This preserves a concrete, fail-closed diagnostic checkpoint while leaving the actual Exclusive correction open.

## Next evidence needed

Run E1 from [`runtime-handoff.md`](runtime-handoff.md) with the new candidate. If loss recurs, preserve the complete session JSONL and identify the first `display_cooperative_transition` with HRESULT `0x88760868`, then the next `display_native_attempt` Reset. Compare their device ID/reset epoch and HWND context: style/ex-style, client and outer rectangles, maximize/minimize, foreground/active/focus handles, and renderer commit state. This will distinguish spontaneous game-window transition from ordinary focus loss and establish whether a narrow object-owner tap is needed.
