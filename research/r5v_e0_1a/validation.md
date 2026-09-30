# R5V-E0.1a validation and provenance

## Inputs

- Retail executable: `D:\Game\Master Rallye\MRallye.exe`, SHA-256
  `bf8aef32407eb6552c05045b8abef149f32983cedd9503b865069b444c5f96b4`.
- Existing E0 Trooper candidate: SHA-256
  `3022bdc6eb07d1e388f9c8ef693b83ce1c20c12c2c1a62719aad1cc59a1b1f13`.
- Existing Ghidra Bridge 12.0.4 and read-only copy of the retail project were
  used. Focused raw assembly, P-code and temporary exports are ignored under
  `.research-output/r5v_e0_1a/bridge/`.
- Scene XML and image metadata were read from the local retail `Data.sma`
  extraction. No asset bytes are committed.

## SmallCarSheet inventory

Retail contains one `smallcarsheet_NNN_000.dxt` per index 0–29. Each file is
2,068 bytes; the decoded sheet dimensions are 32x16. The 25 normal record
initializer arguments in `research/r5v_a/final-vehicle-registry.json`, read
in push order and mapped to `+0x1C` by the raw consumer, prove that frames
12, 18, 23 and 29 are not selected by normal retail records. A visual
inspection of the ignored montage records them conservatively:

| Frame | SHA-256 | Finding |
|---:|---|---|
| 12 | `0eb040b2acfe2c46b2472f97a212af31a0f46e00230b4f8b14c2b639b01b1007` | Unused by normal records; appears blank; no identity assigned |
| 18 | `8097ffe6d993900cb2afcfc736ea486228745929ba10c3832d2f0111d4cc58f7` | UNIDENTIFIED UNUSED FRAME; vehicle art |
| 23 | `7a85d3c421ba35b99e65586fcee16cfd97a6adb164ec93f0656d9355094d51e0` | UNIDENTIFIED UNUSED FRAME; vehicle art |
| 29 | `a1e0486a1042a843487c48c27b97db3e4b96d35b9bc63d1aadbc44f7d6fee742` | Unused by normal records; visually matches Forklift art; historical ID assignment not proven |

The demo builds were not re-audited in this microphase for exact frame
matches. Numeric file order and visual resemblance are not used to assign
identities to frames 12, 18 or 23.

## Candidate checks

- The unchanged `trooper` profile regenerated the existing Trooper candidate
  byte for byte and retained its SHA-256.
- The `trooper-smallsheet29` candidate was rebuilt deterministically from the
  locked retail source.
- Direct comparison against the Trooper baseline found exactly one changed
  executable byte at file offset `0x28E2D5` / VA `0x68E2D5`, the initializer
  immediate changing 0 to 29.
- Candidate output is confined to ignored `.research-output/r5v_e0_1a/`.
  Source hash matched before and after generation.
- Existing writer tests exercise different source/output paths, source hash
  rejection, dry-run behavior, and source preservation.

## Automated tests

Targeted R5V-C patcher tests after adding the profile passed: **19 tests**.
The full synthetic suite passed: **198 tests** in 11.764 seconds. A separate
clean-source rebuild verified the ignored candidate and manifest; source hash
preservation and JSON parsing also passed. These checks establish patch
construction and byte identity; they do not establish HUD rendering or
gameplay behavior.

## Runtime gate

No runtime candidate has been launched in this phase. The R5V-E0.1a HUD
identity result remains pending the owner's visual observations. Do not
upgrade the top-left mapping to runtime-confirmed until those are returned.
