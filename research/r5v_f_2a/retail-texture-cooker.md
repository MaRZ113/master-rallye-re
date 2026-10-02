# Retail texture cache cooker — static evidence

## Functions and source/output roles

| Address | Observed role | Evidence / limit |
|---|---|---|
| `0x0053D2F0` | Texture-table traversal | Calls `0x0053DCC0` for source-backed texture work and `0x0053DF60` for cached DXT loading. |
| `0x0053DCC0` | GXI cache miss / cook | Constructs `.gxi` and `.dxt` path strings, checks the two cache metrics, calls `0x005FF900` to read GXI, `0x00558A90` to create the in-memory texture, then `0x00558B30` to serialize the DXT cache. |
| `0x005FF900` | GXI stream reader | Directly called by `0x0053DCC0`; format support for these exact source files was not runtime-tested. |
| `0x00558A90` | GXI-to-runtime texture conversion | Called after GXI parsing; exact pixel policy is outside this static path closure. |
| `0x00558B30` | DXT cache serialization helper | Called on the miss path before the `Saved cached texture` log. No native DXT output was produced in this phase. |
| `0x0053DF60` | Cached DXT read | Opens `.dxt`, parses the cache representation via `0x00558C20` / `0x00558CB0`, then logs `Loaded cached DX texture`. |
| `0x0064D530` | File access | Direct `CreateFileA` attempt precedes optional Data.sma fallback. The exact path-context type is not inferred from Ghidra's provisional parameter names alone. |

## Cache selection

For `0x0053DCC0`, the retail code compares source GXI and cached DXT metrics
using the same observed `0x14` tolerance and the cache-enabled byte at the
texture object. When the cached DXT is accepted it returns without GXI
conversion. Otherwise it logs `Reading GXI`, parses the source, converts the
image, opens the DXT path, invokes the writer, and logs `Saved cached texture`
if file creation succeeds. `0x0053DF60` is a separate cached-DXT read path.
The metric meaning remains opaque; no claim is made that the comparison is a
timestamp test.

## Path and archive behavior

The file helper tries `CreateFileA(path, ...)` first. If that open fails, it
can search a loaded Data.sma for recognized roots such as `DataGx/`, depending
on its extra path/context argument. At the texture writer call site
`0x0053DE8E–0x0053DE97`, raw ASM pushes `0`, `1`, and the DXT path before the
call. The call setup supplies a null/zero optional context on this output
branch; the decompiler's inferred pointer type is not treated as authoritative.
This means a successful archive read fallback does not establish a matching
archive write path for newly cooked DXT.

The chosen source GXM stores GXI names as absolute strings such as
`D:/projects/MRallyeTNG/DataGx/Vehicles/Mercedes/Black-tga.gxi`. The retail
loader also builds `.gxi`/`.dxt` names by appending extensions to a resource
stem. Static evidence does not fully prove the transformation from the
serialized GXI string to the texture-manager stem, nor how the absolute
developer prefix is mapped in this supplied corpus. That mapping must be
closed before staging a runtime cook.

## Current result

Retail has a GXI→runtime texture→DXT cache path, but **no Mercedes DXT was
retail-cooked** here. The 25 source GXI files and existing 25 DXT companions
are hash-locked in `mercedes-source-manifest.json`. All referenced names are
present in the source folder and the existing DXT files parse with project
tools. This does not establish retail-native output compatibility, cache
invalidation behavior for these exact files, or runtime texture appearance.

Raw Bridge evidence is retained under
`research-output/r5v_f_2a/ghidra-exports-12.1.4/0053d2f0.json`,
`0053dcc0.json`, `0053df60.json`, `005ff900.json`, `00558b30.json`, and
`0064d530.json`, plus `research-output/r5v_f_2a/raw/retail-0053dcc0.asm.txt`.
