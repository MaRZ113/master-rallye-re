# V-AUDIO2 fix1: protected publication-map crash

## Evidence and root cause

The reported all-car race-load crash is explained by mutable whine state embedded
in an executable extension that the launcher finalized entirely PAGE_EXECUTE_READ.
The universal physics-publication hook executes for all participants, even stock
cars. Its CarID-independent map writes therefore fault before an optional custom
sound needs to play.

For the original V-FIT4 candidate, the reported WER EIPs map exactly to:

- `1001296A`: `rep stosd`, clearing the whine publication map (`10012C78`).
- `10012A29`: `mov [edx],ecx`, writing a publication-map entry.

Original executable SHA256:
`bf8aef32407eb6552c05045b8abef149f32983cedd9503b865069b444c5f96b4`.
This is a protection/lifetime implementation defect, not proof that the whine
source waveform, Lancer physics, or GT4 geometry causes the crash.

## Correction

The whine generator places its map and cursor in one dedicated, absolute
page-aligned, zero-initialized 4096-byte page after all executable code and
immutable profile/response strings. It reports that exact range for the sealed
launcher. Code and profile data remain RX; the map page must be RW and
non-executable. Subsequent native extensions begin after the full reserved page.
Absent a whine profile, no range or whine hooks are emitted.

The addon CarID gating, unchanged native optional-SFX ownership, engine WAV,
response formulas and existing physics remain unchanged. No original game file
is patched on disk. The launcher must consume the reported writable range; the
code-only change by itself is intentionally insufficient.

## Offline checks

`tools/vehicle_whine_validate_native.py` now reproduces the previous RX policy
as a negative control: the universal publisher faults with UC_ERR_WRITE_PROT.
The corrected run executes with RX code, one RW/NX map page and unmapped page
zero. There are 28 identity/RPM/load/gear/finish cases, bounded-map overflow,
native sound registration/binding/destruction and strict preimage/allocation
reject checks. External broker/CarID/allocator/interner stubs explicitly clobber
volatile registers. Four synthetic tests also pass, including absolute page
alignment when the extension prefix itself is unaligned.

Unicorn has no Windows TEB. The native destructor body is executed while its
FS:[0] SEH registration/restore alone is excluded; page zero is no longer mapped
merely to let that scaffolding execute.

Result: `.research-output/vehicles/vfit4-fix1/whine-native.json`.

These checks identify and reproduce the observed fault mechanism offline; they
do not qualify DirectSound device behavior or actual race stability. Human tests
must include stock and Lancer race entry, AI, finish, exit and second race entry.
