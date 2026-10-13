# Vehicle source audit validation

Executed read-only from the primary `master-rallye-re-general` checkout:

```powershell
python ps2-research/pc-port/docs/full-coverage/vehicles/audit.py
python -m unittest discover -s ps2-research/pc-port/docs/full-coverage/vehicles -p test_audit.py -v
python -m compileall -q ps2-research/pc-port/docs/full-coverage/vehicles
git diff --check
```

Audit executed three times, approximately 4.3–5.4 seconds each. The two final
JSON outputs were SHA-256 identical on regeneration. All four canonical PS2
input files were independently rehashed by existing `water_runtime.verify_inputs`.
All 29 original CAR.PSM payloads were extracted in memory using the existing
validated PackFS decoder; their source hashes/range provenance are retained.
The 78 retail PC vehicle DX files parsed without a decoder error. No original
input, full proprietary mesh dump, texture, frozen renderer or SDK file changed.

Six focused tests PASS, including 174 per-record registry subtests. Tests cover
unsigned corner permutations/winding, adjacent quantization bins, rejection of
stacked surfaces, duplicate-face digest multiplicity, previous Tata/Kia frozen
geometry hash anchors, complete family inventory and explicit exclusions.
Compileall PASS; diff-check PASS (unrelated pre-existing CRLF notices only).

Dependencies: existing research modules and read-only Course SDK checkout at
`D:/Game/Master Rallye/master-rallye-re-course/src`; audit requires canonical
`D:/Game/Master Rallye PS2` and protected retail
`D:/Game/Master Rallye/corpora/retail/Data.sma_unpacked/DataGx/Vehicles`.
The compact JSON/synthetic tests do not read original game files. They verify
the source admission criteria, not live runtime material availability, MSAA,
visual parity or native state restoration. Native integration/builds belong to
the main agent.
