# Exact dependency and bundle rules

The resolver scans car.dx, complete.dx and wheel.dx in the named vehicle folder. Every non-Null ordered draw slot is resolved case-insensitively against a same-folder DXT basename using the existing asset resolver. It reports resource, physical draw ID, slot, exact name, resolved path and count of bindings sharing the name. It never guesses an absent texture. The manifest distinguishes modified files, required unchanged dependencies, unresolved names and optional sidecar metadata.

The bundler accepts only replacements of files already present in that vehicle folder. DX replacements are recomputed against original bytes with the R4E patcher and rejected if any byte differs outside authorized fields. DXT replacements must retain header and size. Collision changes require the separate R4C workflow and are rejected here. The staging tree is independent of the original game.
