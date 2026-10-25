# Accumulated vehicles work — local phase commits

The owner authorized committing all preceding vehicles work before V-SDK3. Each row records the current consolidated files attributed to that phase. These commits do not recreate unavailable intermediate versions of shared modules. The complete final pre-Studio tree passed778 synthetic tests (one skipped). No push occurred.

| Phase | Commit | Files |
| --- | --- | ---: |
| shared-foundation | `d4d3f891e6ae19355e8a41712964468a0a8fa64b` | 48 |
| j2 | `a933e68bfb05879d72f44c5238b467f75b264c2b` | 56 |
| j3 | `f8a939056875e2993d994afe2df630d0e5113b09` | 17 |
| vlaunch1 | `8ed475bc9184015904010bf66055ae6a735f5bd5` | 3 |
| vmesh | `880b8af3666f5626f52173d71f53e5eef3b14119` | 26 |
| vmesh3 | `d4fc9acc879f0f72569ff0c4b2023dd2731f9372` | 3 |
| vmesh4 | `cb44267a92b4b1fc2787848f5f517f27ad4b487c` | 3 |
| vmesh41 | `f7c484d70a0892bc239af62ae7092b2a19112965` | 3 |
| vmesh42 | `0fffa92667e39d4c4411964cda11fe0a05b7ee0e` | 3 |
| vmesh43 | `0947f317119ffe8b736b9f87585e6283ca1df0c8` | 2 |
| vmesh44 | `af2c4d2410c76e36e61b7f54155f7b6dc1c431b0` | 2 |
| vmesh45 | `f4e13139d6f405d19c562c413a1c55cc15587472` | 3 |
| vmesh46 | `9cddfd424fb9482a4c3a84ce68db9e01abd9ffcc` | 5 |
| vmesh47 | `35f025c8f7581a744ffac82fcc47703e771c5f4d` | 5 |
| vmesh48 | `56d3448113e9f0a683c3d376163411b576172beb` | 5 |
| vmesh49 | `ec86623ae64bc26fd2c905ad00a9db7154ec4864` | 6 |
| vmesh410 | `1d2f74f7aee4f067372bfe024362abf7a6a5c30e` | 6 |
| vmesh411 | `3bd6b9977fc1a4e54a817281d0649071b49dd8c5` | 3 |
| vmesh412 | `d3284963ed22ad9d79a0c9b971f39093319ab09e` | 5 |
| vmesh413 | `da9fa7a2ac0a2d90aa072e021426cbe9eecb5ace` | 4 |
| vlancer1 | `0b0c185d4cd295ab065edef7ac0e8cef8b678d2a` | 2 |
| vlancer2 | `adba1bb21df8cfbfe1f948eef790981f94ddb5a5` | 1 |
| scale1 | `552b1447a141ad65cabe57de6bcc00283b3a972a` | 11 |
| vlancer3 | `9844f1b2485d3d39a61f56037bd5e6dc309000b1` | 38 |
| vlancer3-perf1 | `9d411de06707fb121df9c167fe3ad594c08387bf` | 1 |
| scale1-crash | `b0d4114efa49e998b74fe0a49bddc433d1c81c1a` | 1 |
| vlancer4 | `02eea3404fc2f371e408e9a4e399f8b865422843` | 1 |
| vlancer5 | `866949ae099035fdcd502fcd7e81a0ab348f0e9f` | 6 |
| vlancer6 | `8309d0d3e9d55fc897a96c123e6b65739c83e369` | 15 |
| vphys1 | `7b6eb609b0cf6666b2aecff5507efe5e7248a116` | 19 |
| vphys2 | `3f61c39aeff2228a515c847e133ae6270b6952ae` | 11 |
| vphys3 | `8b13641d21915e73999d5f57e335b3acf5f930bf` | 6 |
| vaudio1 | `e57e1f4b04d6048af888965b3191a561b5917f5d` | 26 |
| vaudio2 | `cc914a03bfd6bb1a7300e060f87085f277ae6f77` | 2 |
| vaudio2-fix2 | `1f2b4fc61a7053dbe2cd514eb7fb8b90e61b68e7` | 3 |
| vturbo1 | `1efff98cd1bd79d98db3384a87887792a3b5428d` | 11 |
| vfit4 | `fde30ba7420ca16c9ae4f3866acd1d509167bcd1` | 25 |
| vfit4-fix1 | `dc0ce43edb9f77d79505211c3824fd7911e7c1ab` | 3 |
| vsdk1 | `2a53ed438491191e40803805932ced26ae1354a8` | 26 |
| vsdk1-perf2 | `f7a081c22215cf6cf81e66a54afec0314ebe8f0d` | 21 |
| vpajero2 | `4e1e0eb984792a2699bf0d7ca2218959caaf707c` | 7 |
| vpajero3 | `1f03bcd59fe537fe0b9ec2465e3e4a8f8583d10f` | 6 |
| vsdk2 | `47d4c326c4ea2cbe89f0628c6438f83c86e6f277` | 10 |

Private game resources and generated candidates remain ignored. Of the 422 previously untracked files, 421 source/research text files were committed with the tracked changes. The unrelated generated `console-example-internal.log` was excluded and explicitly ignored.

## Studio follow-up history

| Phase | Local commit | Validation / scope |
| --- | --- | --- |
| V-SDK3 | `2a42ee769b5a2f014fbe414f6eea11bbe4afe3d7` |790 tests, one skipped; original Studio foundation |
| V-SDK3.1 + V-SDK4A actual accumulated state | `f4df4f4594e43dfc15a78266508cfddeafe7348e` |799 tests, one skipped on revalidation; owner accepted Previewer corrections and texture replacement. No historical snapshot fabrication |

Owner explicitly authorized subsequent local phase commits; no push/release/publication. Further phase IDs are recorded in subsequent documentation commits to avoid self-referential commit IDs.
# V-SDK4A.1 and V-SDK4C continuation — 25 October 2026

- `c3c0b12`: V-SDK4C tracks B/C / V-SDK4A.2 existing native diffuse-slot assignment,
  shared compiler/history integration and offline F1/context Help. Initial suite
  810/1 skip; actual Windows addon and stock build/restore checks passed.
- Following glass phase: original retail instruction evidence, native CPU switch
  replay, explicit pane profile and isolated candidate. Release suite 814/1 skip;
  64 native Previewer captures; all 368 resources unchanged except Subaru car.dx;
  native extension/patch operations/plan identical. Gameplay remains pending.
  Resolved glass commit ID is recorded in the final evidence-index entry.

- `8085800`: V-SDK4A.1 filtered, bounded texture rasterization; original CC0 SVG/ICO;
  Windows identity. 805 tests / 1 skip, 56 real Windows zoom captures, source pixel
  invariance, native Previewer build and four-family GUI smoke. No game byte edits.
- Next scoped material/Help commit: V-SDK4A.2 and V-SDK4C tracks B/C; 810 tests /
  1 skip, real Windows slot picker and addon/stock build/restore validation.
  Its resolved commit ID is recorded by the following phase entry.

