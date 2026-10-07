# PackFS/LZO framing

This layout is confirmed by ELF and fresh canonical bytes. Multibyte fields
are little-endian; records and payloads have **no alignment padding**.

| File offset | Type | Meaning |
| --- | --- | --- |
| +0x00 | u32 | Total decoded byte count |
| +0x04 | u8 | Compressor identifier; 1 selects LZO (0x002bc6c0) |
| +0x05 | u8 | unknown_0x05; canonical value 1; unsupported alternatives rejected |
| +0x06 | u16 | Nominal decoded block size, canonical 8192 |
| +0x08 | u32 | Previous compressed payload length; first is 0 |
| +0x0c | u32 | Current compressed payload length |
| +0x10 | bytes | One inner LZO1X stream of exactly current length |

After each payload comes another `(previous_length,current_length)` pair.
Previous length equals the immediately preceding payload length, excluding
the 8-byte record. Current length likewise excludes that record. The ELF
keeps these fields in state +0x24/+0x28; header/block readers are 0x002bc068
and 0x002bc1e8, payload/virtual decode is 0x002bc380.

The terminal record has previous=last payload length and current=0. Offline
validation requires total output reached, correct previous length, and exact
input exhaustion. Every inner stream must also reach its LZO end token and
consume its full supplied input. These strict corruption checks intentionally
exceed the unsafe game's decoder checks.

Golden PAK: 8-byte header + 33 nonterminal records + 33 payloads + 8-byte terminal
= 135556 bytes. First payload is at 16, stored length 5984, decoded length 8192.
The first 32 blocks decode to 8192 each, last to 7524. Terminal offset is 135548,
previous=3865, current=0. Decoded size=269668; exact hash is in
`golden-validation.json`, with every block boundary.

No raw-block escape appears in the investigated LZO wrapper: a nonzero current
length is passed to the virtual LZO decoder. Raw **resources** exist via the
directory `raw` codec; they are distinct from an inner raw-block mode. No mixed
compressed/raw block support is assumed.

## Algorithm and provenance

`tngtool.py` implements the observed literal/M1/M2/M3/M4 token behavior of
0x002c0cd0, including zero-extended run lengths, overlapping match copies,
low-bit literal tails and LZO end marker. Bounds/size/consumption checks were
added for offline safety. The source was written for this track; no third-party
implementation was pasted or vendored. It requires no LZO package or executable.

An independent local oracle called exported `av_lzo1x_decode` from installed
FFmpeg 8.0 `avutil-60.dll`. Its bundled `include/libavutil/lzo.h` documents the
contract, padding and LGPL 2.1-or-later provenance. The DLL and header are not
redistributed and are not runtime dependencies of the tool. Input/output buffers
had the required 8/12 padding bytes. All 33 independent blocks returned status 0,
zero input remainder and the expected decoded length. The resulting directory
hash matched both the golden and the Python decoder.

Full framed PAK fed directly to that inner decoder returned error flag 8 with
135471 input bytes remaining. First inner stream (offset 16, length 5984)
returned success and 8192 bytes. Stripping 24 bytes would discard inner stream
data; one must parse the records, not strip a fixed header.

Fresh compressed GXI resources demonstrate first u32 sizes 16392 and 65544,
equal to 8 + 64*64*4 and 8 + 128*128*4. The same framing decoder reconstructs
the complete GXI header and payload. The historical 4104 example was not among
the eight extraction targets and is not claimed validated here.
