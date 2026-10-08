# Observatory J.1 Live-Memory Compatibility

## Result

The J.1 process keeps the exact pristine retail `MRallye.exe` on disk and
installs the NULL-safe native Dump guards only in the running image. The
previous live verifier compared the in-memory walker with the stock bytes
resolved from disk, so it rejected the approved process at
`native_dump_walker`. The correction keeps disk identity and process-memory
variant as separate evidence.

## Independently checked reference identity

The pristine reference is SHA256
`bf8aef32407eb6552c05045b8abef149f32983cedd9503b865069b444c5f96b4`, size
3,121,214 bytes, PE32/I386, preferred base `0x00400000`, and
`SizeOfImage=0x00311000`.

The complete walker occupies VA `0x00601D00`, length 1,536. Its stock SHA256 is
`27a0c5e3329ea58c7f9d573b33d1f86feeb3d39eea28177ac4c13ce7392d7c53`. The
J.1 reconstructed runtime reference has walker SHA256
`16d85b7cae971b50f0ad1fd33425bae992cc758c0416c856199eb5ea3dfe2fe9`.

The reconstruction was derived from the pristine retail bytes and the exact
J.1 native patch manifest (SHA256
`78c1070f2e656677f02d22f5d4fdff457e43c7ba74c67bb4e5a5c1488ca53179`). The
reconstructed full-image hash is
`dd03adbd9f45c679e59d09e0a9f09337bd99c787d81f4ce018edb654c1cec881`. This
is an analysis artifact only; it is not the executable launched by J.1 and is
not included in the review package.

## Exact live variant

The only live hardened exception is
`native-hardened-null-safe-stubs-v1`, pinned to the complete walker hash above
and both trampoline records below:

| Hook | Patch RVA / length | Trampoline VA / length | Trampoline SHA256 |
|---|---:|---:|---|
| StringList null guard | `0x20201E` / 6 | `0x0068E6D0` / 19 | `1262617fb90ce85e293c226ac947578ec8e844e6c9048f51696205501114a4c5` |
| XmlData null guard | `0x202153` / 7 | `0x0068E6F0` / 20 | `247e2d5ea0fd0c7b0c97cbc79247d39bfad7b783c023fe641d6af44a71c85a87` |

The shared semantic verifier also checks each exact E9 target, the executable
file-backed `.text` range, the complete stub bytes, null branch, stock
continuation branch, stable walker spans, and non-overlap. A byte-reader
adapter supplies either PE-file bytes or bounded process-memory bytes; the
semantic checks are shared.

## Live acceptance boundary

Native Dump acceptance requires all of the following in the same process
attestation:

- Exact pristine retail SHA256 and byte size on disk.
- `MRallye.exe` mapped from that same resolved path.
- x86 PE32 headers matching the verified disk headers, preferred base, and
  `SizeOfImage`.
- Exact unchanged live Broker/Dump code anchors used by passive Broker read,
  the native Dump route, and the singleton accessor.
- Either the exact stock walker, which does **not** grant Results safety, or
  the exact J.1 walker and both verified trampolines.

An on-disk stock profile alone never marks a process hardened. A live mismatch
fails the native Dump gate; the separate passive Broker read remains usable
when its own gates pass. Observatory remains read-only and never injects code
or writes process memory.

## Runtime status

This change establishes static/mock-memory verification only. A Windows live
capture from an integrated J.1 process remains a human gate. Do not report
`LIVE NATIVE DUMP PASS` until Status shows the approved J.1 runtime variant and
a fresh normal-race native Dump is captured and parsed without a crash.
