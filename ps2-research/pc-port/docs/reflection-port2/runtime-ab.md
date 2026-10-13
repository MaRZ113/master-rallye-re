# One manual visual A/B sequence

Use the separately built PS2-enabled DLL from `dist/current/ps2-enabled` in your
isolated PC test setup, by manual installation only. Keep the previous working
DLL/config as fallback. The task never installs or edits game files.

Use one course, one car/paint, the same Free Camera bookmark, lighting and
resolution. First use Tata, then Kia Sportage. Restart the game after config
changes; keep vehicle reflections policy in the baseline renderer at Stock.
Use non-MSAA for the first test; an MSAA capture is explicitly unsupported and
must leave that body draw Stock, with a bounded diagnostic reason.
Kia's target is the complete opaque painted **record14**, not an isolated hood:
its local bounds span X[-1.0444,1.0456], Y[0.0590,1.6333], Z[-2.3285,2.1591].
The `kiabon2`/`KIA_RECORD_14_BONNET` names are source/diagnostic identifiers;
they do not narrow the verified206-face group. Inspect it from above and a
quarter-side view, rather than judging only a small front-hood patch.

```ini
[PS2Port]
FoliageMode=0
PixelProbe=0
ReflectionMode=0
ReflectionCoverage=0
ReflectionTargetPrecision=0
ReflectionSourceGXI=PS2EnvSource64x64.gxi
ReflectionDiagnostics=1
```

1. Stock: save screenshot and one F10 for Tata.
2. Working fallback: set ReflectionMode=4, retain Coverage=0/Precision=0.
3. Refined destination-format control: retain Mode4 and set Precision=1.
   Logs must show target format25 (A1R5G5B5) or explicit precision_fallback=true
   with format21 (A8R8G8B8). This changes destination quantization only.
4. Kia: repeat Stock vs Mode4 with Coverage=1, first Precision=0, then1 if
   useful. Require vehicle=KiaSportage and exact bonnet digest in the accepted
   event. No matching event means Stock; do not broaden the identity predicate.
5. Rotate camera around the same stationary car; then race restart, menu return
   and one window-mode toggle. Check glass/wheels/HUD and neighbouring draws.
   Repeat with MSAA enabled: expect no mixed override, no stale private target
   or persistent alpha/texture state, and normal gameplay after real Reset.

Save one screenshot/F10 per condition and the bounded ps2_reflection_material
record: vehicle, geometry_sha256, texture generation, source/target formats,
fallback, copy/capture/draw/restore HRESULTs. Current input/image is copied once
per frame before the first accepted body draw. Both vehicles share that image
within the same frame; no per-car environment camera or second native body draw
was added. Record comparable original PS2 camera/lighting evidence before
claiming pixel parity. The captured PC +0.5 normal-Y texture mapping and PS2
-0.5 expression have an unresolved basis relationship; no guessed sign flip
was applied.

For vegetation next, preserve the reflection result and test `grass-port3/runtime-ab.md`.
