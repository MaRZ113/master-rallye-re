# R4F F1 human runtime test

Use only the ignored `.research-output/r4f/runtime-tests/F1_raised_triangle/car.dx` as an Astero race `DataGx/Vehicles/Astero/car.dx` override. Build a full-tree Python `Data.sma` using the already runtime-confirmed packaging workflow, one candidate at a time. Compare with the protected original Astero. The candidate adds one raised triangle on the right-side hood/body draw 7, using original triangle 27 and a 0.05-source-unit outward offset. Collision bytes are unchanged. Candidate SHA-256: `b03e8402baef682bb5665ccbce3a9cc8342e87409b3a5bd2170e9674d6ed7835`. Keep a stock copy available for comparison and restore it after testing.

Report: game loads; Astero loads; extra triangle visible; texture and shading on the new triangle correct; rest of body normal; collision behaves normally; ordinary damage works; breakable glass works; wheels normal; artifacts or crashes. A cautious ordinary damage/glass check is sufficient; no extreme-speed crash is needed.

A visible extra triangle with normal vehicle behavior would confirm the topology writer by runtime. A crash, missing geometry or material/shading corruption requires investigation. Automated parse, corpus and Blender checks do **not** confer runtime confirmation. The next phase after a human pass is to decide whether R4G vehicle SDK hardening is needed; do not begin tracks.
