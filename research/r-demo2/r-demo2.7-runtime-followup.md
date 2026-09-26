# R-DEMO2.7 — one bounded endpoint/tolerance capture

## Why this remains

The supplied candidate screenshots are enough to identify face 37 and anchor its plane to the first source-replay divergence. They do not show the compared edge endpoint payloads or the effective runtime `ConvexHull_PlaneThickness`. One additional capture can close those exact remaining facts. This is a single candidate run with one ordinary breakpoint; no baseline run, hot-loop condition, source mutation, stepping trace, or executable patch is requested.

## Pinned run

- Build: `demo-8.4.1`
- `MRallye.exe` SHA256: `bbdfdb709ed41b10461b233b2f5c55403f1b6640f57d9e440476211e51ce75be`
- Baseline Trooper GXM SHA256: `fd08bc10c440fce261ef126e40445002fb56359d4011c1dcbf9c2f71b0e91047`
- Candidate GXM SHA256: `0425e1636bc83844da241d48e30fedae2d48aff024cb4f1e329506ac64b1e699`
- One breakpoint: `005C447B`, stop before `XOR EDI,EDI`.

Use a separate scratch game copy and verify all three hashes. Do not modify the original installation, executable, or GXM. Keep the raw text dump under ignored `.research-output/r-demo2/`.

## Capture at the stop

Record `EIP, ESI, EBX, EDI, ESP`. From the frame layout already visible in the prior screenshot, read:

```text
[ESP+0x34]  local-list sentinel pointer
[ESP+0x38]  local-list count
[ESP+0x40]  saved caller EDI (hull-state pointer, verify it is readable)
[ESP+0x44]  saved caller ESI (face-vector byte offset; expected 0x940)
```

Read the exact 8-byte double at module VA `005F8C68` (`ConvexHull_PlaneThickness`). Then use the captured hull-state pointer to read these vector ranges as begin/end dwords:

```text
hull state +0x24 / +0x28  face vector, stride 0x40
hull state +0x34 / +0x38  edge vector, stride 0x80
hull state +0x44 / +0x48  vertex vector, stride 0x20
```

Capture the face object `ESI` for `0x40` bytes, including its `+0x28` list sentinel and `+0x2c` count. Walk that circular list and record every node's address and `+0/+4/+8` dwords. Capture the local list from `[ESP+0x34]` the same way, checking the node count against `[ESP+0x38]`. The expected state is face index 37, one remaining face edge, and three local edges; preserve any mismatch instead of adjusting it.

For the current edge in `EBX` and the last-tested remaining face edge in `EDI`:

1. Read `edge+0x64` sentinel pointer and `edge+0x68` endpoint count.
2. Walk both endpoint nodes and record each node's `+0/+4/+8`; the `+8` value is the endpoint vertex-object pointer.
3. For all three local-list edges plus the remaining face edge, record the same endpoint data. Deduplicate repeated vertex-object pointers.
4. For each distinct endpoint vertex pointer, save its `0x20` bytes. Exact 8.4.1 `005BA930` reads the first three doubles at vertex offsets `+0`, `+8`, `+0x10` and arrays have stride `0x20`.
5. Normalize face, edge, and vertex pointers only after checking they lie inside the captured vector bounds and meet the exact stride. Keep list-node addresses separate from payload-object pointers.

Do not step the game while collecting these values. A screenshot or text dump is enough. Stop and exit after the single hit.

## What this will settle

- whether the runtime plane-thickness value lies in the replay's split window `0.0004948211223303467 < thickness <= 0.0005142677133753715`;
- exact edge-vector indices for the current and remaining edges;
- endpoint vertex-object pointers, indices, and coordinates;
- whether the no-match pair fails by disjoint endpoint identities and the full current face graph's component count.

If the range/pointer checks fail or the face is not index 37, retain the dump as a discrepancy; do not reinterpret addresses or start another trace.
