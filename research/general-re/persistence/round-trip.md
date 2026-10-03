# What a round trip would and would not prove

The static cycle is established:

`live eligible entries → native XML → loose file → native typed load → merged entries`.

Reload is not a byte-for-byte memory restoration. Scope and SaveFile are assigned
by the load, revisions are reconstructed, empty slots are not serialized and some
XmlData classes return no tree. Name/type/value and save annotations are the
appropriate semantic comparison set. Diagnose metadata changes separately.

First compare a normal Options value in a disposable install (U2), then a normal
PlayerState change (U3). Record raw/JSON pairs before/after/relaunch, native file
hashes and backup hashes. Use the native application to write; do not produce
synthetic XML for the first validation. Recovery is restoring the stopped
disposable install's baseline copy, never the authoritative corpus.

The original static phase performed no round trip. The later
[U3 name observation](u3-runtime-result.md) confirmed UI/runtime use but did not
observe persistence; it is not FULL PASS. Follow the
[single mapped trigger test](u3-save-trigger-test.md). Synthetic parser/filter/storage
tests do not prove persistence works in the game. Broad developer Game save remains
behind the archive-only backup and metadata-retagging questions.
