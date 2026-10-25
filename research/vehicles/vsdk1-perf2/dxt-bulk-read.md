# PERF2 — source-qualified cached DXT bulk reads

2026-10-24 · Separate optional performance candidate. Original c-perf and its
nine-stage layout remain immutable. No texture resolution or artwork change.

## Live baseline

The user supplied four manually labelled native QPC capture windows:

| Interval | DXT loads | DXT inclusive | GPU CreateTexture | Texture LRU releases |
| --- | ---: | ---: | ---: | ---: |
| Lancer cold | 1351 | 5883.04 ms | 41.50 ms | 1422 |
| Pajero cold | 77 | 1162.66 ms | 4.59 ms | 0 |
| Lancer warm | 1 | 1.32 ms | 0.05 ms | 0 |
| Lancer re-entry | 81 | 4323.44 ms | 5.61 ms | 611 |

These are inclusive action windows, not automatic CarID attribution or exact
input-to-first-frame latency. The first cold window includes substantial UI
work. Re-entry nevertheless spends over 4.3 seconds in cached DXT loading while
GPU creation, surface conversion and mip generation consume a small fraction.

Texture-manager-clear counters stay zero. Actual LRU releases occur during
Lancer cold/re-entry. Manager destruction on menu exit is therefore not an
established explanation for this run. Native cache pressure/reloading is observed.
`live-capture-baseline-summary.json` records all four capture hashes. There is
post-optimization native timing evidence below.

## Original pixel-reader mechanism

Exact retail SHA256:
`bf8aef32407eb6552c05045b8abef149f32983cedd9503b865069b444c5f96b4`.

1. `0053DF60` calls `00558CB0`, whose call at `00558CBA` invokes `00581120`.
2. `00581120` reads dimensions, constructs the original image with `005FF230`,
   then loops over each pixel. `00581190` calls stream virtual method `+44h`
   once per 32-bit BGRA pixel and copies that word unchanged.
3. Native stream vtable `0069CE44` has `+44h = 0064D900`. That helper calls
   virtual `+24h` with a four-byte request.
4. `+24h = 0064D720`: loose files call **ReadFile** for every request. Archive
   streams follow their original ZIP path instead.

A 1024×512 loose DXT therefore incurs over half a million four-byte file reads
despite its contiguous BGRA representation. Larger imported textures amplify
this inherited path. The exact instructions and live timing breakdown justify
batching reads while retaining every source pixel.

REA/Ghidra evidence: `perf2lower.json`, `perf2read.json`, `perf2seek.json`.
`dxt-bulk-byte-verification.json` independently records original PE bytes,
Capstone decoding, vtables and Win32 IAT mappings. Tiny stream helpers absent
from Ghidra's function map are verified directly from instructions.

## Implemented adapter

`vehicle_dxt_bulk_native.append_dxt_bulk()` changes only call `00558CBA` in the
suspended-process patch plan. It needs no mutable globals, imports or DLL changes.

Fast-path admission requires the exact `0069CE44` vtable, a valid loose-file
handle, archive flag zero, stream position 12, positive dimensions no greater
than 4096 each, and exact file length `20 + width*height*4`.

The helper reads dimensions in one eight-byte call, invokes the original native
image constructor and reads the entire pixel payload into its original BGRA
allocation. Rows, alpha and colour bytes remain untouched. It returns the same
four-byte image wrapper. GPU format choice, materials, upload, mip generation
and cache accounting remain the original engine path.

Archive/unknown streams go directly to the original decoder once. Noncanonical
dimensions/layouts rewind using the native seek method and fall back. A failed
seek returns NULL rather than decoding from the wrong position. Allocation or
short-read failure uses the native deleting image destructor to free partial
ownership and returns NULL. No handles, images or COM objects are retained.

The logic contains no vehicle IDs, model names, materials or texture heuristics.
The 4096 guard is an adapter bound; larger files use the original reader.

## Validation and remaining gate

`validate_vehicle_dxt_bulk_native.py` executes original scalar-reader, stream,
image-constructor and deleting-destructor instructions against the compiled
adapter. Win32 file/seek/size and heap services are typed mocks. Code is RX;
page zero stays unmapped.

Twelve cases pass: byte-equal 1×1, 8×4 and 32×16 images; archive, unknown-vtable,
different-position and trailing-data fallback; short-read FALSE and TRUE with
partial byte count; failure of each of the three allocation operations with
cleanup. Dimensions, full BGRA, final position and stack/callee-saved ABI agree.
Canonical read calls change from `width*height+2` to **2**, excluding the
unchanged outer header-prefix reader.

Three regression tests pass for these controls, deterministic linked output,
preserved payload prefix, exact call-only image diff, wrong-source/preimage
rejection and allocation bounds.

## Measured separate bulk candidate

The user supplied these additional action windows with the same nine stages:

| Interval | Before DXT loads / time | Bulk candidate DXT loads / time | Before / after LRU releases |
| --- | ---: | ---: | ---: |
| Lancer cold | 1351 / 5883.04 ms | 72 / 80.70 ms | 1422 / 0 |
| Lancer re-entry | 81 / 4323.44 ms | 71 / 72.13 ms | 611 / 611 |

The re-entry capture directly verifies installed decoder call `00558CBA` targets
bulk entry `10025DA0`, in addition to all nine timing hooks. The earlier cold
and original baseline captures predate this additional identity field; their
raw data remains unchanged and the comparison marks that limitation explicitly.

Call counts differ, particularly the initial cold window's UI workload. These
measurements demonstrate substantially less synchronous DXT-loading time in the
observed windows, not an exact percentage improvement in input-to-visible-model
latency. Identical 611 LRU evictions in re-entry show this adapter does not remove
cache pressure: it makes required reloads much cheaper. GPU creation is 2.79 ms
in the after re-entry window. No source artwork or resolution changed.

Private `evidence/benchmark-qualified.json` records capture hashes, per-stage
counts, direct decoder identity where recorded and pairwise cautions. Warm and
Pajero follow-up measurements remain pending. CPU mocks alone do not establish
gameplay speedup, and actual race stability remains the user's testing boundary.

The adapter changes no original EXE/DLL file, texture pixels, geometry, physics,
audio, UI, materials, fitment or frozen vehicle baseline.
