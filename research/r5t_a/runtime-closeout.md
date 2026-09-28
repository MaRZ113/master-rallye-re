# R5T-A closeout: Blender and the 9.10 course-cooker bridge

This note separates the automated local checks from the project owner's runtime
observations. Original and cooked game resources remain in ignored `inputs/`.

## Blender course import — HEADLESS SMOKE PASS

The `tests/blender/r5t_a_course_smoke.py` test passed headless in Blender 5.2.2
for retail Italy1 and France1. It checked geometry counts, source identity
attributes, course collection placement, read-only metadata, vehicle-exporter
rejection, and loaded DXT images. Italy1 produced 54,612 vertices, 41,722
polygons, 837 draws, two UV sets, and 75 material slots with loaded images.
France1 produced 65,206 vertices, 64,577 polygons, 995 draws, two UV sets, and
97 material slots with loaded images. No manual viewport review or comparison
with the original game's D3D8 appearance was performed.

## 8.4.1 source → Demo 9.10.0 runtime cooker → Demo 9.10.0

`CONFIRMED_BY_RUNTIME` (project owner): Demo 9.10.0's original runtime cooker
processes old 8.4.1 course source when stale compiled DX/DXT outputs are removed.
The resulting courses load and run in Demo 9.10.0; AI opponents work, old
8.4.1 start/grid behavior can persist, and visual issues remain on some legacy
conversions. This is separate from retail-course package compatibility in the
older demo runtimes.

The local `inputs/vesions_cooker-info.txt` says there is no course GXM/GXI
cooker in 9.3.1, 8.4.1 has a course cooker but not a car cooker, and 9.10.0 can
cook GXM/GXI and courses. The cooker entry point is identified by the owner as
the Demo 9.10.0 MRallye runtime. The precise launch action/arguments, file
watching trigger, stdout, and debug log are not present in the supplied input
snapshots. Therefore this note verifies the supplied output structure, but it
does not claim an independent local cooker invocation or reproducibility test.

## Supplied recooked DX — CONFIRMED_BY_CORPUS

The course DX reader accepted both files as revision 135, validated complete
render-index coverage, and structurally reached trailing tag100. The tag100
payload itself remains undecoded.

| Course | Bytes | SHA-256 | Vertices | Triangles | Physical draws | Course root records | Batches |
|---|---:|---|---:|---:|---:|---:|---:|
| France1 | 14,769,564 | `0d6ae4c4ea87ee0c9ac41592714b710d3ac8eb1e9a437bb43be11471e21bcd58` | 84,250 | 74,812 | 4,620 | 665 | 105 |
| Italy1 | 10,384,538 | `315a1a265dc4fbb025c031aaefc107bf9ad4d8c306f417eaefb6f3d99ce4cc6b` | 56,010 | 43,262 | 1,565 | 2 | 131 |

This confirms revision 135 contains substantially different logical course
record layouts: France1 has 665 parsed root records, while Italy1 has two.
Revision number alone does not identify one course graph.

## Snapshot comparison and limits

Case-insensitive relative-path and SHA-256 comparisons give:

- France1 source → `fresh-cooked`: the old `france1.dx` is absent; the other
  172 files are byte-identical. `fresh-cooked` → `cooked-in-9.10.0`: a new
  `france1.dx` is added; the other 172 files remain byte-identical.
- Italy1 source → `fresh-cooked`: `track01.dx` and
  `i2a_field2-tga.dxt` are absent; the other 110 files are byte-identical.
  `fresh-cooked` → `cooked-in-9.10.0`: a new `track01.dx` is added; the other
  110 files remain byte-identical.
- The France1 DXT set is unchanged byte-for-byte in these snapshots. Italy1's
  one missing DXT is already absent in `fresh-cooked`; none of the remaining
  DXT files changed bytes. These snapshots do not establish whether the cooker
  regenerated identical DXT files or reused them.
- The source GXM and TXT are byte-identical across source, `fresh-cooked`, and
  `cooked-in-9.10.0` snapshots.

The folder names and file deltas are corpus evidence, not proof of the cooker
deletion policy, process arguments, or deterministic output. No generated game
asset is copied into repository research outputs or committed.
