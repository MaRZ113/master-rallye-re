# EXTRA-SET1 native candidate

The implementation now lives in `src/native/rmod1/extra_options_runtime.cpp`.
It extends the G1 source line, retains the `dinput8.dll` product name and adds a
versioned SDK roster provider. Vehicle visual mappings are in `vehicles.json`;
SDK registration and per-mode eligibility come from the accepted SDK plan.
The existing graphics proxy is staged privately and consumes the small interface
in `extra_options_graphics.hpp`; the general/renderer checkout is read-only.

Build from the owner-local inputs with MSVC and the existing renderer toolchain:

```powershell
python tools/build_extra_options_candidate.py --name owner-next --package
python tools/validate_extra_options_candidate.py --build .research-output/extra-set1/owner-next --delivery "D:/Game/Master Rallye/master-rallye-re-vehicles/.research-output/vehicles/extra-set1/owner-next"
```

The builder's installed-G1 hashes are identification evidence, not a runtime or
build allowlist. It compiles the investigated G1 source plus the SDK provider.
The private runtime checks the API/hook layout it actually calls. It must not
write to the original EXE, SMA, input/graphics wrappers or accepted SDK bundle.
`pefile` is used for owner-local PE inspection; dependencies are not vendored.

The delivered private candidate is `extra-set1/integrated-11` in the vehicles
checkout. Run `Launch-Extra-Options.cmd`; use single-player Quick Race's native
Vehicle Setup → Gearbox page. Paint/Tire drafts are committed with APPLY and
persist in the adjacent `MRallyeExtraOptions.state.ini`. Legacy Randomizer INI
behavior remains separate. New toggles are Enabled/Liveries/Tires in
`MRallyeExtraOptions.ini`. No installer or F6 popup is involved.

Five original native tire families plus Stock are routed through the existing
pre-initialization front/rear writers. Texture-only sponsor transfer preserves
alpha and is explicitly partial; compatible PC visual bundles are available
where it cannot reproduce the full variant. No CarID or gameplay profile is
created for a livery. The current customization scope is player 0, single-player
Quick Race. Other-mode customization is not certified.

Evidence and owner checklist:
`master-rallye-re-vehicles/docs/sdk/EXTRA_OPTIONS_NATIVE_RESULTS.md`.
The native scene fixture proves actual rendering/initialization, not normal
interactive navigation or race/solver behavior. Those remain owner tests.
Source-only archives contain no donor assets, compiled DLLs or extracted shaders.
No push, release or installation was performed.
