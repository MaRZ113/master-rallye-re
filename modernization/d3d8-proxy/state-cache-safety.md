# Engine cache constraint and observational state

**Master Rallye has its own D3D state cache.** Future graphics code must not change
native state behind that cache and assume the game will repair it on the next
draw. The game can suppress a Set* because its cached value appears current.

R-GFX1 [state-cache.md](../renderer-recon/state-cache.md) confirms manager VA
0x00570900 / RVA 0x00170900 and caches for RS, TSS, transforms, textures and
stream/FVF/indices/viewport. RS forwarding seam VA 0x0053F8B0 / RVA 0x0013F8B0
and restoration VA 0x00570BB0 / RVA 0x00170BB0 are read-only input evidence.

R-GFX2 issues only the game's requested native call. It adds no getters to find
defaults and copies no engine memory. State starts unknown; JSON null always
means unobserved/invalidated, not zero. A successful setter records observed state;
a game-issued getter records its output. A failed call preserves the prior state.
An unreadable successful getter's output invalidates that field rather than
silently preserving an unreliable value.

Tracked storage includes RS0..255, TSS8×64, matrices0..511, 16 streams, 8 textures,
indices/base index, shader/FVF raw values, viewport and render/depth targets.
Draw snapshots serialize the 24 documented RS keys, TSS types1..32 on 8 stages,
WORLD256, VIEW2, PROJECTION3, TEXTURE0/1 transforms16/17, viewport and bindings.
Other indexed matrix writes are still recorded as events, with exact float bits.

Successful Reset invalidates everything; resource metadata associations are
cleared. Failed Reset retains prior observed state but aborts a pending frame.
BeginStateBlock/EndStateBlock/ApplyStateBlock conservatively invalidate, and
recorded setters are not presented as live state. The proxy does not emulate
partial state-block masks. MultiplyTransform and deletion of a bound shader mark
the affected value unknown. SetRenderTarget invalidates viewport because it can
change implicitly. Successful UP draws clear the implicit stream0 binding (and
indices for indexed UP), according to D3D8 semantics; no native cleanup call is
inserted. Known-null binding remains distinguishable from unknown.

Each draw snapshot is the observed state immediately before that native draw;
the native result is attached afterward. Reset restoration and inherited state
still depend on all relevant calls reaching this wrapper. A raw-device escape
could make observational state stale without changing rendering, so human call
coverage checks are part of acceptance. Unknowns cannot be promoted using an
FVF, texture filename or a previous frame from another device.
