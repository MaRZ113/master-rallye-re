# Compact DLL + external-resource deployment — integration boundary

Status: design/audit boundary; no new DLL deployment prototype or production claim in the first editor slice.

Existing `runtime_launcher/src/main.cpp::Launch` pins and hashes the original executable, checks adjacent wrappers, creates the game suspended, verifies the child image, optionally installs a native extension and validated patch plan, then resumes. Integrated mode passes `bundle/resource-root` as working directory; bootstrap-only uses the original executable directory. These established paths remain unchanged.

That launcher is a qualified bootstrap precedent, not evidence that an arbitrary DLL is discovered by the installed game or that a partial overlay can resolve every missing resource from the retail installation. The separate bootstrap decision, exact loader interception/fallback, dependencies/conflicts and reversible uninstall still need a bounded launch proof. No replacement of installed d3d8.dll, MRallye.exe, clean Data.sma or Randomizer is permitted.

Next implementation after the editing pilot: pin one existing retail build, expose a small explicit bootstrap/extension interface, route one private changed vehicle resource through an isolated overlay with base fallback and a compact manifest, exercise fail/rollback/conflict paths, then prove a real original-game resource load. Keep it isolated until owner/runtime qualification. A valid fixture DX/DXT and an editor cache hit do not fulfill this deployment gate. Editor Qt package size is unrelated to the desired in-game mod footprint.
