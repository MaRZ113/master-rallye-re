# R-COOKER3.1 third-family preflight: Trooper

**Status:** `STATIC_PREFLIGHT_PASS`; native cook and runtime gates remain
pending. This is preparation for a later operator-controlled test, not evidence
that Trooper has been cooked by the retail harness in this phase.

## Source inventory

The selected source set is the local Demo 9.3.1 Trooper corpus at the
repository-relative location `inputs/9.3.1_Trooper/`. The scanner and plan
record only relative paths and hashes; proprietary files remain ignored and
are not copied into this document or the release.

| Role | GXM SHA256 | GXM size | DX SHA256 | DX revision | DX size |
|---|---|---:|---|---:|---:|
| `complete` | `122d84a45a6b2f81989e645c18ecfd7a32392bf029c7503698fb5fc900eb5c34` | 260,220 | `fe4dfa6639c0ac2c9baf4e07428abe4ea3a528bb86b411a3034d74d4ce83a3a9` | 131 | 134,349 |
| `car` | `5caed6da1213f17e2638d0ee47860cf521d4715475418e028bfd13f7c0e87642` | 222,754 | `bf644c0530b3908789676564b4761cd670cc2bb187b084983d414bba458fa041` | 131 | 124,568 |
| `wheel` | `ade8e42e4e1c4c946b2bf726c722494b31854ee0ebd2e16384db675a7595aa65` | 27,234 | `4611a14326b0413cab8bffc7a61e0c6ee710f69bb986f0cab83921193bf8505f` | 131 | 12,924 |

## Preflight result

The actual `plan` result selects `retail-native-gxm` for all three supported
GXM roles. It reports 54 embedded authoring references, 24 unique referenced
GXI files, one historical authoring root, and zero unresolved references.
The texture plan has 24 dependencies: 23 valid DXT files are reused and one
missing DXT is eligible for the supported offline GXI-to-DXT encoder.

The source inventory contains 3 GXM, 3 DX, 26 GXI, 24 DXT, and 4 TXT file
instances. This preflight checks role/prefix and dependency readiness; it does
not certify a retail cook, runtime load, collision behavior, or Trooper
physics. The machine-readable record is
[third-family-preflight.json](third-family-preflight.json).

## Next controlled gate

If a native cook is performed later, it must use a separate copy of the
verified retail harness and a job-owned authoring mirror. Preserve the
canonical input tree. After cooking, collect and statically validate all
three roles before requesting runtime review. Report any temporary runtime
family namespace explicitly; a model result under another family namespace
does not prove Trooper physics configuration.
