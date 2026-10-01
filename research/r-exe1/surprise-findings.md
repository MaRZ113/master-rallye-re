# Surprise findings

## Retail-only BuildData cache builder

Retail contains a substantial development-oriented builder not found in the three earlier executable string catalogs. The recursive walker at `005B2DA0` enumerates a selected root and dispatches MODEL, TEXTURE, and IMAGE BANK file types to callbacks that enter the same ordinary GXM/GXI/image-bank loaders used by runtime resource code. The unrecognized wrapper at `005B2F80` normalizes the selected path, resets per-type counters, invokes the walker, and logs completion totals. Raw disassembly verifies the wrapper even though Ghidra did not initially create a function for it.

A data table near `00692F8C` contains a cluster of method-pointer-like values including the wrapper address. That establishes callback-like registration evidence. The table's owner, dispatch function, and user-visible reachability are still unresolved. R-EXE1 does not patch or invoke it.

**Why it matters:** it may expose the original runtime cache cooker through dormant retail editor infrastructure, and its callbacks link resource loading to derived DX/DXT-style caches.

## The shared broker is an executable data model

Retail broker diagnostics expose entry count/capacity, categories, type tags, revision, path identifiers, and save flags. Typed getter/setter families use the same 0x1c stride and grow the vector as indexed entries are created. This offers a reusable executable anchor across vehicles, race state, progress, frontend, and scene configuration, rather than a vehicle-only parameter reader.

## Networking code is real and stable late in the lineage

The four builds contain an enable/disable UDP listener that binds port 22,222. It is paired with network car address keys and race synchronization state. The 9.3.1, 9.10.0, and retail listener instruction sequences are identical under the reported mnemonic-only comparison. Protocol and playable-mode support remain unknown, but this is more than generic Winsock imports.

## Retail archive lookup reuses the normal resource open path

The retail reader checks loose files before archive fallback, then opens Data.sma members through a ZIP central-directory reader. Models/textures continue through shared GXM/GXI loaders and cache diagnostics. This means archive behavior, loose overrides, and cache generation can be investigated through one resource-manager path.

## Six MasterRallye summary rows are not a race capacity

Retail `MasterRallye.xml` and its read/write functions clearly use Car0..Car5 for campaign summary fields. Separately, the vehicle/race system has its own `Race/NumCars` route. This is an important guard against misreading a convenient fixed array as a global six-car cap.
