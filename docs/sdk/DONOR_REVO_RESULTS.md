# Source Garage — Sega Rally Revo bounded archive smoke

Research date: **2026-10-28**. Exactly one original car-related SBF was inspected:
`E:/RallyWorkshop_Sources/sources/Sega Rally/Main_release/cars/205_t16gravel_model.sbf`.
The file stem is preserved as source identity; a complete original vehicle/catalog
join was not performed. This is not a vehicle importer or an MR build.

| Evidence | Result |
|---|---|
| Original input | 462,576 bytes, SHA-256 `37bccb579e0cc86aa6eeaaf25177135bc5a4d06fdc8432fea6142eda99438c2a` |
| Container | Uncompressed little-endian4 header,16 zero bytes,9 directory records |
| Directory | Starts24, ends96; first member7996. Bytes96–7995 remain uninterpreted metadata/padding, not deleted. |
| L0 | **WARN**: all9 ranges valid;5 DDS headers valid; type2/type3 semantics unknown |
| L1 geometry / hierarchy / UV | **NOT TESTED**; one type1 mesh candidate retained as metadata |
| Individual texture | **PASS**: first DDS decoded through Pillow13.0.0;512×512,DXT1,10 mipmaps |
| L2 original vehicle rendering | **NOT TESTED**; individual atlas PNG does not qualify vehicle rendering |
| Gameplay | **NOT TESTED** |
| Original bytes | Re-read and SHA-256 compared after probe; unchanged |

The first decoded image was visually inspected and contains wheel/tyre imagery.
That observation does not establish native texture role, material bindings, wheel
mesh identity, suspension transforms or vehicle generation. Only one of the five
DDS members was decoded to pixels; the other four were validated at header/range
level.

## Exact member boundaries

Offsets are decimal in the **expanded archive** address space. The selected file
is uncompressed, so they also match original file offsets. Directory keys remain
opaque identifiers. End offsets are exclusive. Payload lengths/hashes cover the
exact bounded spans and may include trailing archive padding; no nominal DDS
length is inferred from an unexplained member-header field.

| Directory index | Key | Type | Member range | Payload offset / bytes | DDS header |
|---|---|---|---|---|---|
| 0 | `57e0efe6` | 4 | 7996–184124 | 8064 /176060 | 512×512 |
| 1 | `7b267cda` | 4 | 184124–188220 | 184192 /4028 | 32×32 |
| 2 | `b06858e1` | 4 | 188220–192316 | 188288 /4028 | 32×32 |
| 3 | `0901dd97` | 4 | 192316–198012 | 192384 /5628 | 128×8 |
| 4 | `bd525b1c` | 3 | 198012–203220 | 198044 /5176 | Not interpreted |
| 5 | `e0debdf7` | 2 | 203220–208700 | 203252 /5448 | Not interpreted |
| 6 | `becf1c95` | 4 | 208700–214396 | 208768 /5628 | 128×8 |
| 7 | `332ab384` | 2 | 214396–215840 | 214428 /1412 | Not interpreted |
| 8 | `6a5cb3b8` | 1 | 215840–462576 | 215872 /246704 | Mesh candidate only |

Private `report.json` records every member/payload hash and original header words.
First DDS SHA-256:
`2c047818f7469a357abbc22ec134ff75f54fb42e6765e90f4ec7264c033e6d8b`.
Decoded PNG SHA-256:
`a13c9a3ad7ce5d5aeb7239f1896601bd8d14417ec16ffa25e51577746abea4b3`.

## Reproduction and safety bounds

From repository root:

```powershell
python tools/source_garage_revo_probe.py `
  --config research/vehicles/source-garage/roots.example.json `
  --source-root 'E:/RallyWorkshop_Sources/sources/Sega Rally' `
  --protected-root 'E:/RallyWorkshop_Sources/tools' `
  --input 'E:/RallyWorkshop_Sources/sources/Sega Rally/Main_release/cars/205_t16gravel_model.sbf' `
  --output '.research-output/vehicles/source-garage/revo/205-t16-gravel-review'
python -m unittest discover -s tests/synthetic -p test_source_garage_revo_probe.py -v
```

Choose a fresh output directory; the probe rejects existing reports and uses
exclusive file creation. Required `--config` protects the collection base and
every configured donor root, including absolute paths outside the base.
Repeatable `--protected-root` also protects the local tool collection in this run.
Outputs cannot be inside, equal to or an ancestor of any protected or selected
source root. Linked/reparse path components are rejected. No original file is
opened for writing. Nothing is installed or patched.

Stored input is limited to64MiB; SBZ1 advertised/actual expansion to128MiB;
directory to20,000 entries; DDS to8192 pixels per side and16,777,216 pixels total.
SBZ1 uses zlib with an explicit output limit, requires stream completion/exact
advertised size and rejects trailing input. Duplicate/out-of-range offsets,
overlapping directory/member headers and invalid DDS dimensions are rejected.
Unknown member types remain visible. This probe validates the documented LE4/SBZ1
layout; it does not declare every Revo archive revision supported.

**17 synthetic tests PASS**, covering uncompressed/compressed equivalence,
malformed/truncated streams, expansion under/overstatement, size/count/range
budgets, duplicate/overlapping offsets, directory-order identity, output
containment across other titles, collection base and additional tool roots,
config validation, read-only source behavior and a fabricated one-pixel DDS decode.
The real selected input exercised the **uncompressed** path; SBZ1 was exercised
only with synthetic fixtures, not a second original car archive.

Private outputs:
`.research-output/vehicles/source-garage/revo/205-t16-gravel-final/report.json` and
`member-0000-texture.png`. The folder is ignored and excluded from source-only
review archives. No DDS, PNG, model bytes or donor assets are tracked.

## Existing-tool comparison

Wire facts were checked against the primary
[Game Extractor archive reader](https://github.com/wattostudios/GameExtractor/blob/1d3201e2fff3ba3a7fd0f72b12cb9d0738a89e6a/src/org/watto/ge/plugin/archive/Plugin_SBF_SBZ1.java).
Its separate
[Revo mesh viewer](https://github.com/wattostudios/GameExtractor/blob/1d3201e2fff3ba3a7fd0f72b12cb9d0738a89e6a/src/org/watto/ge/plugin/viewer/Viewer_SBF_SBZ1_MESH.java)
uses zero UV coordinates and duplicates two-sided faces. Those limitations make
it insufficient for source-faithful vehicle reconstruction. This independent
probe incorporates no third-party implementation and does not use that viewer.

Result: **existing archive/texture knowledge matches one actual local car file**.
A full Revo adapter still needs UV streams, materials, hierarchy, wheel transforms,
LODs and source catalog joins. No importer development is authorized by this smoke.
