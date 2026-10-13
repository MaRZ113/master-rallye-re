# Validation

Public immutable-source build workflow PASS with clean frozen renderer and
current committed HUD baseline. Baseline and PS2-enabled Win32 Release builds
independent, serial --parallel1, canonical .build/.staging only.

- Baseline CTest24/24 PASS.
- PS2-enabled CTest30/30 PASS.
- Focused Python88/88 PASS,0failures/skips.
- Both proxy export/PE32 checks PASS.
- Both interface generators repeated twice, locked outputs PASS.
- Compileall PASS.
- Port diff-check PASS.

Native tests supplied original private grass, shrub, puddle and reflection
inputs. Cover separate textures/asset identities, category swap rejection,
Stock defaults, one-category failure isolation, separate frame consumption,
source count/size, pending-state restoration, device loss/real Reset/echo.
Two-category resource/proof lifecycle remains separate from physics lifetime.
Synthetic shrub tests cover exact category spelling, original same-surface
grid/lift distinction and malformed/unknown resources. Research byte checks
independently verify46R5900words and original ELF mapping.

Baseline DLL SHA256:
011dd9a94155d216d0c0dde28e0af97f5b72226aae5be97016f2d767ebdf7138
PS2-enabled DLL SHA256:
6edc2426e2602545121f16959cdbb2055fb205a907b36173cb85a447b7051deb

Sources/patches/Git/generator fingerprints are in build-report.json, also
dist/current/build-report.json. No dirty-worktree exception was required.
Source renderer and Course SDK unchanged. Original private grass SHA remains
6af6393c444a485b2c648c2a6973a91bd5783db3c0f90269a0d653b2f089cfad.
Original assets are not included in Git/handoff. No automatic deployment/push.

Runtime: first grass/menu/HUD result is USER_RUNTIME_OBSERVATION. Second shrub
layer pending user A/B. Native physics spawn/contact NOT_PERFORMED.

Handoff deterministic ZIP serialization, SHA member manifest and CRC/readback:
PASS. Isolated extracted source/test bundle ran all88Python tests PASS using
only the external verified renderer staging for integration-file checks.
No private game corpus was required by those Python cases. The previous small
grass-port1/source-contract.json fixture is included for identity regression.
