# R5T-SDK1 Retail corpus validation

Evidence: **CONFIRMED_BY_CORPUS**. This report was recomputed from the curated
local Retail baseline; it contains derived parser and resource-resolution
metadata only.

## Corpus selection

- Source: `corpora/retail/Data.sma_unpacked`.
- Course folders: 36; RaceTest XML files: 41; HNT files: 36; ICont SFL files: 36.
- The live unpack at `../Data.sma_unpacked` was excluded because it contains
  runtime probe edits. France1 DX/XML hashes differ from the curated baseline;
  the live unpack was read only and not modified.

France1 source comparison:

| Resource | Curated corpus SHA256 | Live unpack SHA256 |
|---|---|---|
| `france1.dx` | `A6BFCEF97684F41154596F91FDFAA9522A8FDF6B65D181F4D1AC327B9CAF07D5` | `CE596ACF34FF2C36D2C7D09C3B42BA8AEF8EA00553B9FDFE95FF2609E2FA484A` |
| `France1.xml` | `BEAA2180912FFD54F313A149962E295F9894239014481D2C7BA2DB84FB1E08E1` | `B36C13DD45DA67651FC34E747F6749A8A0D7FCE609994AD1BC9F7EDC99101EDD` |

## Course package coverage

- Course folders: 36
- DX render parse and validation: 36/36
- TXT parsed: 36/36
- HNT parsed and linked through exact Model paths: 36/36
- RaceTest XML composed: 36/36
- SFL parsed: 36/36
- Course GXM prefix parsed: 0/36
- CourseProject diagnostics: 0

The resource associations use exact resolved HNT `Model` paths and HNT stems
for RaceTest XML and SFL. TXT/GXM sidecars may match the selected model stem.
Ambiguous resources remain unselected.

## HNT references

- References: 2,843
- Resolved by exact path: 2,842
- Unresolved: 1
- Ambiguous: 0
- The runtime necessity of the unresolved texture reference is **UNKNOWN**;
  no basename fallback was used. Its full record is retained in the JSON.

The unresolved record is `Turkey_s2_flip` → `Texture`
`course\turkey_s2_flip\pathesport-tga`.

## RaceTest XML

All 41 XML files in the curated RaceTest folder parsed. The HNT-matched
principal course group has 36 files, 36 StartArea lists, 36 FinishArea lists,
and 110 complete split records. Split counts per XML: 34 courses with three
records and two with four. Principal Radius range: 7–30. The remaining five
XML files are listed separately; no local runtime probe copies are part of
this corpus.

## Sample fingerprints

- France1: `DataGx/Course/France1/france1.dx`, 13,489,510 bytes, SHA256 `A6BFCEF97684F41154596F91FDFAA9522A8FDF6B65D181F4D1AC327B9CAF07D5`.
- Italy1: `DataGx/Course/Italy1/track01.dx`, 10,243,860 bytes, SHA256 `971B44AB0F1543E457245731789DAD2439259B37D206B6CA588F0130D84911E2`.

## Blender and test validation

- Blender 5.2.2 geometry smoke passed on curated Italy1 and France1:
  41,722 / 64,577 triangles, 837 / 995 draws, and 75 / 97 DXT-backed
  materials loaded.
- Curated France1 RaceTest helper smoke passed with 1,080 markers, four
  StartArea points, four FinishArea points, three visual signs, three trigger
  spheres, and 12 visual companions.
- The packaged add-on ZIP smoke passed against the same curated France1 DX/XML
  and produced the same helper counts.
- Blender used the isolated profile under ignored
  `.research-output/r5t_sdk1/blender-profile`; the user's installed
  add-on/profile was not changed.
- The synthetic suite passed 158/158 tests; `compileall` and JSON parsing
  passed; `git diff --check` reported no whitespace errors.

Commands for the corpus and Blender validation:

```powershell
python -m unittest discover -s tests\synthetic -v
python -m compileall -q src blender tools tests
python -m json.tool research\r5t_sdk1\retail-corpus-validation.json
python tools\build_blender_addon.py --output dist\master_rallye_io.zip
& 'D:\Game\Master Rallye\_reverse-tools\blender-5.2.2-windows-x64\blender.exe' --background --factory-startup --python-exit-code 1 --python tests\blender\r5t_a_course_smoke.py -- 'D:\Game\Master Rallye\corpora\retail\Data.sma_unpacked\DataGx\Course\Italy1\track01.dx' 'D:\Game\Master Rallye\corpora\retail\Data.sma_unpacked\DataGx\Course\France1\france1.dx' .research-output\r5t_sdk1\r5t_a_course_smoke.json
& 'D:\Game\Master Rallye\_reverse-tools\blender-5.2.2-windows-x64\blender.exe' --background --factory-startup --python-exit-code 1 --python tests\blender\r5t_b_xml_smoke.py -- 'D:\Game\Master Rallye\corpora\retail\Data.sma_unpacked\DataGx\Course\France1\france1.dx' 'D:\Game\Master Rallye\corpora\retail\Data.sma_unpacked\DataScene\RaceTest\France1.xml' .research-output\r5t_sdk1\r5t_b_xml_smoke.json
& 'D:\Game\Master Rallye\_reverse-tools\blender-5.2.2-windows-x64\blender.exe' --background --factory-startup --python-exit-code 1 --python tests\blender\r5t_d0_zip_smoke.py -- dist\master_rallye_io.zip 'D:\Game\Master Rallye\corpora\retail\Data.sma_unpacked\DataGx\Course\France1\france1.dx' 'D:\Game\Master Rallye\corpora\retail\Data.sma_unpacked\DataScene\RaceTest\France1.xml' .research-output\r5t_sdk1\r5t_d0_zip_smoke.json
```

The machine-readable per-course inventory and unresolved HNT references are
in this directory beside this report.
