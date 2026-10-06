# Historical demo Mercedes audio mapping

## Finding

Demo 8.4.1 and demo 9.3.1 each have a native Mercedes registry record at
physical ID2, class T1. In both audio constructors, IDs 0 and 2 enter the same
tuned `vehicles/rev9` sample branch. The second selector uses the shared
curve-table-A arrays. The resource-object constructor supplies the same
`+0x1C = 0x3FC00000` default as the corresponding ordinary profile.

This is an authentic historical **native mapping** for a demo Mercedes, but
not a Mercedes-specific sample or unique tuning identity: in those builds,
ID0 Landcruiser and ID2 Mercedes share the observed switch arms. Retail ID0
also uses `vehicles/rev9`, the same primary raw scalar and table-A data. The
sample hash and table-A hash are byte-identical across the analyzed builds.

## Compatibility and limits

Candidate A selects current retail ID0 for audio while physical CarID remains
26. This is a semantic reconstruction of the historical demo mapping using
the current retail switch/table layout, not a transplant of demo bytes. The
full old-build tuning object is not asserted byte-equivalent. Human listening
now confirms retail ID0 is an ordinary stock-style sound on ID26, making it a
suitable historical-compatible current-retail policy, but not an authentic
unique Mercedes recording.

The useful classification is:

* historical Mercedes mapping exists: **YES, demo 8.4.1 and 9.3.1**;
* unique Mercedes engine sample/profile: **NO evidence**;
* current retail donor chosen: **stock ID0 / Landcruiser**;
* retail ID0 audible result on physical ID26: **HUMAN_RUNTIME_OBSERVATION**;
  ordinary / normal stock-style sound.
