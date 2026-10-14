# Brake/lamp follow-up handoff

Read implementation.md, runtime-ab.md and model-readiness.md. Terrano rear-lamp
native-material and additive-glow controls are implemented; new DLL runtime is
pending. Original PC brake switching is proven by x86 bytes and the user's F10
pair. PS2 mode 14 was independently revalidated. Defaults remain Stock.
No complete model or wheel replacement, or PS2 visual parity, is claimed.

The ZIP contains clean committed source/tests/docs, exact overlay patches/lock,
both DLLs, build report and SHA-256 manifest. It excludes original game assets,
screenshots, raw buffers, databases and full model exports. The glow retains the
PC texture and requires no new asset. The old headlight private asset is separate.

Build: python ps2-research/pc-port/overlay/build_overlay.py
Requires pinned renderer Git objects 0bddf7c7bc5e95831f98714ff6231da05ab073ea and
MSVC Win32/CMake/SDK. Reuses .build/baseline, .build/ps2-enabled and .staging with
--parallel 1. Byte probes require hash-locked original binaries and the existing
EER/Rabbitizer installations. Extracted Python tests need no private game data.
Source regeneration requires protected retail DX, PS2 PackFS and read-only SDK.
Manual installation only; retain the accepted DLL and user config.
