# Gamma/brightness archaeology — DEFERRED

Static reviewed import inventory reports no gamma import; reviewed D3D8 receiver map has no confirmed SetGammaRamp/GetGammaRamp site. [R-GFX1 evidence](../../../renderer-recon/d3d8-entry.md) is coverage-limited, not proof about all unreviewed indirect/GetProcAddress paths. Current research searches establish no stock gamma/brightness config owner.

Exact-pristine existing session session-20261007-003728-5952.jsonl has1263 sampled frame summaries, zero SetGammaRamp/GetGammaRamp counters, four successful resize Reset transitions640x480 <->1920x1027. Historical R-GFX4/windowed evidence, not this DLL or an exclusive gamma experiment; summary/capture coverage does not rule out non-D3D Win32 use. Conclusion: **not observed in reviewed paths**, not universal absence.

Mapped families use textures and copied vertex diffuse with LIGHTING0. [Lighting research](../../../renderer-recon/lighting.md) and R-GFX4 input archaeology prevent confusing stock prelighting with output gamma. Changing texture RGB/vertex diffuse is not transfer correction.

R-GFX5 forwards native Set/GetGammaRamp unchanged, adds no SetDeviceGammaRamp, Gamma checkbox, texture conversion/sRGB claim or desktop-global ramp. Stock/Borderless/Exclusive retain native/original behavior. Independent borderless correction, exclusive gamma capability/OS behavior and any stock option effect remain UNKNOWN. A future local-output stage needs justified compositor/transfer ownership outside this phase.

Optional human exclusive comparison holds track/assets/settings fixed, notes brightness difference and actual gamma events. No desktop gamma edits. Missing new correction is deliberate **DEFERRED**, not a fake Gamma1.0 feature.
