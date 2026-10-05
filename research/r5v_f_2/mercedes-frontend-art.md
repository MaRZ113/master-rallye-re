# Mercedes frontend art and presentation audit

## Vehicle Select icon

The registered demo Mercedes is ID2, class0 / T1 local2. In the active Vehicle Select scene, `T1_Car3` is the local2 widget and uses carsheet image-bank index4. This exact slot-to-widget/frame mapping appears in both demo builds. Demo-8.4.1's `carsheet_004_000.dxt` is 128×128, SHA-256 `c1b9e1c7db098b83256d40dea60f7f131b00265b5448637294f8feb172c40872`. Demo-9.3.1's frame4 is SHA-256 `c3f5d7ac2e388a6412ef21cf3722e2ccfae80029abd5c51d8e40343681006c23`; it is byte-identical to the retail frame4 file.

This is stronger than assigning a name by visual resemblance: the frame is attached by scene structure to the historic ID2/local2 slot. It does not prove the graphic is Mercedes-exclusive: the same frame remains in retail, where the current ID2 is Tata. The final ID26 overlay now binds T1_Car8 to zero-based image-bank index3 (frame4). It is staged in the ignored F.2e output and is statically verified; P0 must confirm runtime rendering. Report it as historic Mercedes-slot art, not exclusive restoration art.

## SmallCarSheet — separate channel

Demo-8.4.1 has no RaceResults SmallCarSheet asset. Demo-9.3.1 has 20 frames, and its ID2 constructor's final raw integer is 0; however, the demo-specific link from that integer to the SmallCarSheet frame was not independently traced. Retail's proven `VehicleRecord +0x1C` SmallCarSheet consumer is a separate build/layout evidence source; it does not by itself prove demo-9.3.1 semantics or identify the content of its frame0 as Mercedes. No retail unused frame (12, 18, 23, or 29) is assigned to Mercedes by this audit.

The final profile retains the established donor SmallCarSheet frame9 until the historical field/frame link is proven. That fallback does not change the internal name or Vehicle Select icon choice. Do not merge the Vehicle Select frame4 and SmallCarSheet selector into one icon system.

## Frontend stats and race colour

Both demo ID2 initializer call sites provide four raw presentation integers `[4,3,6,5]`; in the existing Vehicle Select bar order these correspond to Speed/Acceleration/Handling/Endurance. The final profile uses these values. The old `0x24` record layout has no four-float RGBA tail corresponding to retail `+0x24..+0x30`, so the demo cannot supply an equivalent per-record race-marker colour. Final ID26 keeps an explicit custom red marker; do not call it Mercedes-authentic.

The staged final mappings and P0 checklist are summarized in [R5V-F.2e frontend](../r5v_f_2e/frontend.md).
