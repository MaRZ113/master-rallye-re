# R4D.1 runtime closeout

The project owner supplied in-game observations and screenshots for four controlled Astero DXT replacements. Candidate metadata preserves source hashes, dimensions, headers and per-candidate SHA-256. Its original `runtime_tested=false` describes generation time; it was not rewritten. These runtime observations are combined with the separate executable and corpus evidence in `findings.md`.

| Test | Controlled edit | In-game result | Status |
|---|---|---|---|
| M1 whitepaint-tga.dxt | white, black, gray | body and helmets; chrome, lamps, glass, and number stickers unaffected; white/gray/black changes the reflection contribution continuously; disappears with Reflections OFF. | CONFIRMED_BY_RUNTIME |
| M2 windscreen32-tga.dxt | alpha255, alpha128, alpha0 | glazing around vehicle; lamps unaffected; 255/128/0 alpha changes transparency continuously; normal glass uses source-alpha blending. | CONFIRMED_BY_RUNTIME |
| M3 chrome-tga.dxt | asymmetric | rims, bullbar and reflective trim; asymmetric helper appears with Reflections ON and disappears with OFF. | CONFIRMED_BY_RUNTIME |
| M4 breaklightsonglow-tga.dxt | alpha255, alpha128, alpha0 | active rear brake-light glow while braking; base lamp stays; 255/128/0 alpha changes glow strength/transparency; additive and emission remain unproved. | CONFIRMED_BY_RUNTIME |

M1 whitepaint contributes continuously to body/helmet environment reflection; it is not ordinary diffuse paint. M3 chrome is an environment helper for reflective trim. Both disappear with Reflections OFF, consistent with the recovered stage-1 path.

M2 glass is source-alpha blended, consistent with D3D8 SRCALPHA/INVSRCALPHA and alpha test disabled for normal vehicle glass. M4 changes the active braking layer, while the base rear lamp remains. No additive blend or emission claim follows from its name.

Human result source: `.research-output/r4d_1/runtime-tests/user_results.txt`. Local screenshot counts: M1=12, M2=9, M3=6, M4=3. Game screenshots, candidate DXT and source assets remain outside Git.

Limits: tested on Astero and these candidates. Sorting, damage fade and unusual Null-slot bindings remain unresolved.


