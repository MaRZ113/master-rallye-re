# Scoped gameplay Freecam

R-CAM1-A3d adds actual camera control, default OFF, using the common GameFov
owner. One pre-traversal CALL remains at VA `0x006532DD` / RVA `0x002532DD`,
original `0x00509680` / RVA `0x00109680`, two arguments and RET8. Completion
intercepts the existing CALL at VA `0x005B0166` / RVA `0x001B0166`, original
scheduler `0x00653080` / RVA `0x00253080`, one float argument and RET4.
Completion is installed first; failed pre installation rolls it back. Exact bytes,
readback/protection and per-frame patch ownership remain checked.

The new x86 scheduler bridge saves original input state, invokes pre callback,
copies the float argument, calls the original exactly once, preserves its opaque
output state across post callback and returns RET4. PUSHAD/flags and aligned
FXSAVE preserve ECX/EDX, callee-saved registers, EAX/EDX outputs, x87, XMM/MXCSR.
The existing traversal tail bridge preserves RET8. Neither replaces return addresses.
Seven actual scheduler ABI fixture cases supplement 62 existing observer cases.

Only planes `+08..37`, Previous Pose `+38..77` and Current Pose `+88..C7`
are owned: **176 bytes**. Each frame snapshots the latest native stock fields,
writes both pose endpoints to the independent pose and generates effective CPU
side planes. Native interpolation then produces the same effective VIEW.
Particles at `0x0056410E`, finalize at `0x006532E6`, late builder at
`0x0056CE38` and EndFrame remain inside the scope. Present cannot restore while
the scheduler is active. Restoration follows the original scheduler return.
Source, flags, viewport `+78..87` and snap count `+C8` are never restored.

The camera builder `0x005614A0` can skip when its argument equals global
`0x006E9A74`, initially `-1`. Reviewed gameplay/finalize/debug calls pass zero.
Freecam checks that sentinel remains `-1`; it does not force a native cache flag.
The effective pose stays present for direct late reads as well as native VIEW.

Initialization inverts the actual last successfully displayed gameplay VIEW,
with columns Right, Up and -Back, rather than guessing the interpolation factor
from Current Pose. Owner/race/camera identity must still match. Movement uses
world Y for vertical, normalized diagonal translation, yaw/pitch with ±89° pitch,
orthonormal basis and elapsed time clamped to 50 ms. No roll control is added.

GameplayFOV Off/Freecam Off stays stock; FOV alone retains its plane/projection
behavior; Freecam alone uses stock source-angle/aspect; both use configured VFOV.
There is no second overlapping plane or pose restoration stack. Toggling off
lets the next native render consume the stock pose currently produced by the game,
not the pose saved at initial activation.

The local HWND input subclass is installed only for enabled exact-retail Freecam.
It reads physical non-extended keypad scan codes regardless of NumLock and forwards
all messages to the original WndProc. There are no global keyboard/thread-message
hooks. WASD and Custom use supported virtual key bindings. Focus loss clears
held keypad/mouse state, deactivates flight and requires a fresh toggle edge.
Mouse capture starts with zero delta, recenters the client area and hides cursor
through the existing foreground cursor owner. Ordinary game input remains available.
F8 has no conflict in reviewed renderer bindings/MainWndProc evidence; unmapped
DirectInput/debug shortcuts remain a human first-flight check. Toggle is rebindable;
F10 is rejected. The module and passthrough input state stay pinned if a newer
subclass prevents safe unlinking.

Reset restores while current ownership is still valid, then clears flight/input
and revokes the race certificate. Teardown/unknown context deactivates. Identity
loss abandons stale storage without dereferencing it. A successful new lifecycle
and displayed stock VIEW are required to rearm. Wrong thread also abandons writes.
Failure is surfaced, never silently treated as verified restoration.

R-OBS1b message-hook removal, R-ATTR1 guard, display/UI/AF/MSAA/reflection policies
are retained. No EXE file patch, teleport, HUD hide, photo mode, lighting, weather,
Exclusive fix or asset change occurs. Earlier camera-dependent ordering/position
caches and car-centered streaming can limit distant flight: behavior remains UNKNOWN
pending the first local flight. No global culling bypass is used.
