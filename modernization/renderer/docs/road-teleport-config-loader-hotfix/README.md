# Road Teleport INI Config Loader Hotfix

The teleport settings already existed in `parse_free_camera_config()`, but `read_visual_config()` only retained values from its explicit FreeCamera key table. The five teleport keys were absent there, so the parser consistently received safe defaults while the independent PhysicsObserver section still enabled road-target preview.

The loader now collects the four FreeCamera teleport values and `FreeCameraKeys.ArmRoadTeleport`. A Win32 integration test exercises the actual profile APIs, `read_visual_config()`, the production FreeCamera parser, PhysicsObserver loading, and the production forwarding helper. It covers enabled values, safe defaults when the request is missing, and rejection of non-road mode.

Setup telemetry now separates the teleport request, RoadOnly policy, effective configuration, and installed-hook state. `native_selection_argument_override` is true only when installation/lease verification succeeded and the effective road feature is enabled. Exact-build, quiescence, and patch ownership guards are unchanged.

Validation on 2026-10-12: Win32 x86 Release build; 21/21 CTest; renderer Python suite 189/189; root synthetic suite 630/630; `compileall`; proxy verifier; `git diff --check`.

`source-files.zip` contains the five source/test files touched for this hotfix. It contains no game executable, DLL, PDB, object, library, or runtime capture.

Runtime remains to be checked in one ordinary stock-Reset session using the exact pristine retail executable. Expected setup evidence is `road_teleport_requested=true`, `road_teleport_enabled=true`, `installed=true`, and `native_selection_argument_override=true`, with reason `exact_callsites_installed_with_road_selection_override_disabled_until_armed`. This verifies setup only; it does not arm or perform a teleport.
