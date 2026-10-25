# Source-only phase handoff

`V-PHYS3-V-AUDIO1-source.zip` is a source overlay for the existing Vehicle SDK
checkout on `research/vehicles`, not a standalone retail game package. It
contains the files changed during this phase: shared integration, optional
profiles, tools, tests and documentation. Earlier SDK dependencies must already
exist in the checkout. Preserve unrelated local work before applying an overlay.

No extracted WAV, model, texture, bank, database, executable, raw decompiler
dump or screenshot is included. Input hashes and editable source-selection
metadata do not provide the underlying proprietary resources. Native audition
requires the user's original exact-build executable at runtime; the SDK does
not bundle the original DSP code. GT4 extraction is optional. User-created
PCM can use the same audio-profile importer without any GT installation.

Generated local candidates and convenience launchers remain under the ignored
private output roots. See README.md here and ../vphys3/README.md for their names,
evidence boundaries and human test sequence. Neither source tests nor native
controlled replay establish gameplay qualification.

The archive index records every included source file and its SHA256. Assets
and bulk diagnostics remain outside this clean handoff. No commit/push or
publication was performed.
