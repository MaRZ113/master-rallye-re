# R5V-F.2c material and texture validation

Material mappings were reconstructed by material-number and draw order from the pinned Copy of Mercedes car.txt and wheel.txt sidecars, then cross-checked against DX texture slots and the runtime load log.

| Role | DX draws | Source materials | Unique matches | Unmatched/ambiguous |
|---|---:|---:|---:|---:|
| complete | 18 | 22 across car.txt plus wheel.txt | 18 | 0 |
| car | 17 | 17 in car.txt | 17 | 0 |
| wheel | 5 | 5 in wheel.txt | 5 | 0 |

The complete model's 22 source material records are not a one-to-one mapping to its 18 physical DX draw records; each draw was nevertheless resolved uniquely. Car draw flags distinguish the windscreen's alpha-enabled slot from the other opaque material draws. The windscreen DXT has 1024 non-opaque alpha pixels in its 32x32 image. Wheel draw flags are consistent across all five wheel materials. Null slots are sentinels, not missing textures.

The union contains 25 unique non-null DXT references. All 25 files exist in the isolated runtime tree, match the pinned source manifest, pass the current DXT parser, and appear as successfully loaded in the relevant runtime logs. There are no unresolved core texture dependencies. The log's failed null.dxt request corresponds to Null material slots and is excluded.

Per-role dependency lists, hashes, dimensions, alpha counts and material mappings are in research-output/r5v_f_2b/cook-a/validation.json. This closes model material and texture dependency checks for Cook A. It does not prove cache-only portability because the authoring junction remains present and a fresh no-GXM runtime has not been run.
