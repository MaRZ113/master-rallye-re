# Course resource graph (R5T-A)

Course folders are paired to RaceTest XML/HNT and ICont field files by an exact normalized stem. HNT paths resolve case-insensitively against the actual `DataGx` relative path; the resolver does not fall back to a matching basename.

| Build | folders | scene XML | HNT | empty HNT | DX | TXT | DXT files | SFL/FL/SF | resolved HNT refs | unresolved HNT | ambiguous HNT | XML refs resolved/unresolved |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| Demo 8.4.1 | 2 | 2 | 1 | 0 | 2 | 2 | 114 | 5 | 73 | 40 | 0 | 0/0 |
| Demo 9.3.1 | 2 | 2 | 0 | 0 | 2 | 2 | 145 | 2 | 0 | 0 | 0 | 0/0 |
| Demo 9.10.0 | 2 | 2 | 1 | 1 | 2 | 2 | 178 | 2 | 0 | 0 | 0 | 0/0 |
| Retail | 36 | 36 | 36 | 0 | 36 | 36 | 3998 | 36 | 2842 | 1 | 0 | 0/0 |

## Retail HNT graph

Retail contains 36 nonempty course HNT manifests, 36 Model entries, and 2807 Texture entries.
Exact path resolution: 2842 resolved, 1 unresolved, 0 ambiguous.
Shared resolved dependencies across course manifests: 1.
The single unresolved retail entry and every shared dependency are listed below and in JSON.

- **demo-8.4.1 / Italy1** `DataScene/RaceTest/Italy1.hnt` line 52: `Texture [vehicles\mercedes\msbackc-tga]` -> unresolved
- **demo-8.4.1 / Italy1** `DataScene/RaceTest/Italy1.hnt` line 53: `Texture [vehicles\mercedes\silverpaint-tga]` -> unresolved
- **demo-8.4.1 / Italy1** `DataScene/RaceTest/Italy1.hnt` line 54: `Texture [vehicles\mercedes\mbackb-tga]` -> unresolved
- **demo-8.4.1 / Italy1** `DataScene/RaceTest/Italy1.hnt` line 55: `Texture [vehicles\mercedes\mfgrill64-tga]` -> unresolved
- **demo-8.4.1 / Italy1** `DataScene/RaceTest/Italy1.hnt` line 56: `Texture [vehicles\mercedes\mdoor64-tga]` -> unresolved
- **demo-8.4.1 / Italy1** `DataScene/RaceTest/Italy1.hnt` line 57: `Texture [vehicles\mercedes\mblight64-tga]` -> unresolved
- **demo-8.4.1 / Italy1** `DataScene/RaceTest/Italy1.hnt` line 60: `Texture [vehicles\mercedes\mpanel16-tga]` -> unresolved
- **demo-8.4.1 / Italy1** `DataScene/RaceTest/Italy1.hnt` line 62: `Texture [vehicles\mercedes\whitesuit32-tga]` -> unresolved
- **demo-8.4.1 / Italy1** `DataScene/RaceTest/Italy1.hnt` line 64: `Texture [vehicles\mercedes\mhelmet32-tga]` -> unresolved
- **demo-8.4.1 / Italy1** `DataScene/RaceTest/Italy1.hnt` line 67: `Texture [vehicles\mercedes\mastersticker-tga]` -> unresolved
- **demo-8.4.1 / Italy1** `DataScene/RaceTest/Italy1.hnt` line 70: `Texture [vehicles\mercedes\mercwheel64-tga]` -> unresolved
- **demo-8.4.1 / Italy1** `DataScene/RaceTest/Italy1.hnt` line 72: `Texture [vehicles\mercedes\merctread-tga]` -> unresolved
- **demo-8.4.1 / Italy1** `DataScene/RaceTest/Italy1.hnt` line 73: `Texture [vehicles\mercedes\mercwheel643-tga]` -> unresolved
- **demo-8.4.1 / Italy1** `DataScene/RaceTest/Italy1.hnt` line 75: `Texture [vehicles\mercedes\mercwheelrim-tga]` -> unresolved
- **demo-8.4.1 / Italy1** `DataScene/RaceTest/Italy1.hnt` line 76: `Model [vehicles\citroen\car]` -> unresolved
- **demo-8.4.1 / Italy1** `DataScene/RaceTest/Italy1.hnt` line 77: `Texture [vehicles\citroen\underdash-tga]` -> unresolved
- **demo-8.4.1 / Italy1** `DataScene/RaceTest/Italy1.hnt` line 78: `Texture [vehicles\citroen\pcitrwing32-tga]` -> unresolved
- **demo-8.4.1 / Italy1** `DataScene/RaceTest/Italy1.hnt` line 79: `Texture [vehicles\citroen\perspex-tga]` -> unresolved
- **demo-8.4.1 / Italy1** `DataScene/RaceTest/Italy1.hnt` line 80: `Texture [vehicles\citroen\pcitsport32-tga]` -> unresolved
- **demo-8.4.1 / Italy1** `DataScene/RaceTest/Italy1.hnt` line 81: `Texture [vehicles\citroen\pcitrear128-tga]` -> unresolved
- **demo-8.4.1 / Italy1** `DataScene/RaceTest/Italy1.hnt` line 82: `Texture [vehicles\citroen\redpaint-tga]` -> unresolved
- **demo-8.4.1 / Italy1** `DataScene/RaceTest/Italy1.hnt` line 83: `Texture [vehicles\citroen\pcitlogos128-tga]` -> unresolved
- **demo-8.4.1 / Italy1** `DataScene/RaceTest/Italy1.hnt` line 84: `Texture [vehicles\citroen\pcitfrontgrill64-tga]` -> unresolved
- **demo-8.4.1 / Italy1** `DataScene/RaceTest/Italy1.hnt` line 85: `Texture [vehicles\citroen\pcitfrontpanels64-tga]` -> unresolved
- **demo-8.4.1 / Italy1** `DataScene/RaceTest/Italy1.hnt` line 86: `Texture [vehicles\citroen\pcitblight32-tga]` -> unresolved
- **demo-8.4.1 / Italy1** `DataScene/RaceTest/Italy1.hnt` line 87: `Texture [vehicles\citroen\chair2-tga]` -> unresolved
- **demo-8.4.1 / Italy1** `DataScene/RaceTest/Italy1.hnt` line 88: `Texture [vehicles\citroen\whitesuit32-tga]` -> unresolved
- **demo-8.4.1 / Italy1** `DataScene/RaceTest/Italy1.hnt` line 89: `Texture [vehicles\citroen\dcambell-tga]` -> unresolved
- **demo-8.4.1 / Italy1** `DataScene/RaceTest/Italy1.hnt` line 90: `Texture [vehicles\citroen\black-tga]` -> unresolved
- **demo-8.4.1 / Italy1** `DataScene/RaceTest/Italy1.hnt` line 91: `Texture [vehicles\citroen\cithelmet32-tga]` -> unresolved
- **demo-8.4.1 / Italy1** `DataScene/RaceTest/Italy1.hnt` line 92: `Texture [vehicles\citroen\whitepaint-tga]` -> unresolved
- **demo-8.4.1 / Italy1** `DataScene/RaceTest/Italy1.hnt` line 93: `Texture [vehicles\citroen\drichard-tga]` -> unresolved
- **demo-8.4.1 / Italy1** `DataScene/RaceTest/Italy1.hnt` line 94: `Texture [vehicles\citroen\mastersticker-tga]` -> unresolved
- **demo-8.4.1 / Italy1** `DataScene/RaceTest/Italy1.hnt` line 95: `Texture [vehicles\citroen\pcithlight32-tga]` -> unresolved
- **demo-8.4.1 / Italy1** `DataScene/RaceTest/Italy1.hnt` line 96: `Texture [vehicles\citroen\windscreen32-tga]` -> unresolved
- **demo-8.4.1 / Italy1** `DataScene/RaceTest/Italy1.hnt` line 97: `Texture [vehicles\citroen\glass-tga]` -> unresolved
- **demo-8.4.1 / Italy1** `DataScene/RaceTest/Italy1.hnt` line 98: `Model [null]` -> unresolved
- **demo-8.4.1 / Italy1** `DataScene/RaceTest/Italy1.hnt` line 105: `Texture [markers\null]` -> unresolved
- **demo-8.4.1 / Italy1** `DataScene/RaceTest/Italy1.hnt` line 106: `Texture [course\italy1\null]` -> unresolved
- **demo-8.4.1 / Italy1** `DataScene/RaceTest/Italy1.hnt` line 107: `Texture [markers\lose rock texture-tga]` -> unresolved
- **retail / Turkey_s2_flip** `DataScene/RaceTest/turkeyS2Flip.hnt` line 69: `Texture [course\turkey_s2_flip\pathesport-tga]` -> unresolved

## Shared dependencies

- `retail:misc/water/watersurface3.dxt` used by France1, France2, France_M, France_S1, France_S2, France_W, France_W_flip, Italy2, Italy3, Italy_M1, Italy_M1_flip, Italy_M2, Italy_S1, Italy_S2, Italy_S3, Italy_S3_flip, Italy_S4, Italy_W1, Italy_W2, Spain1, Spain2, Spain_M, Spain_S1, Spain_S1_flip, Spain_S2, Spain_W, Spain_W_flip, Turkey2, Turkey_m, Turkey_s1, Turkey_s2, Turkey_s2_flip, Turkey_w.

HNT edges are dependency declarations; this report does not claim that every entry is runtime-essential.
Explicit XML references are resolved only when their literal path exactly matches a corpus-relative file. Extensionless and other resource-like XML values remain uninterpreted in `racetest-xml.json`.
