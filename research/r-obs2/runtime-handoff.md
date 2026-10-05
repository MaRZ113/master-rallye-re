# R-OBS2 / mercv2 runtime handoff

First confirm that the exact Mercedes v2 executable is available to the main checkout or provide its existing path. Do not alter or patch it.

1. Run the structural audit on the user-provided `MRallye.exe`; it must print SHA `1fbb3489…`, family `retail-broker-v1`, registry `merc-id26`, Broker capture enabled, post-Results Dump unsafe, and legacy Attract path present:

   ```powershell
   python tools/research_build_profiles.py audit-build "<folder containing MRallye.exe>\MRallye.exe" --output .research-output/observatory/audits/mercv2-audit.json
   ```

   If any required Broker anchor/layout fails, stop. Do not bypass the result.

2. Use a fresh process and a fresh ordinary active race with a stock vehicle. Capture `mercv2-stock-race`.

3. In a new fresh process, use Mercedes ID26 in one ordinary active race. Capture `mercv2-id26-race`.

   ```powershell
   python tools/r_ai1_observe.py --observatory "<audited Observatory directory>" --exe "<folder containing MRallye.exe>\MRallye.exe" -- --label mercv2-id26-race
   ```

4. Verify JSON/raw integrity and run the registry-aware checker against the ID26 capture. It must report `BROKER_STATE_MATCH_ONLY`, CarID26/class0 and Mercedes family identity; that automated result does not prove actor visibility/gameplay.

Human checks that the game remains alive, each capture completes, and the Mercedes is visible/functional. Do not use Restart before capture and do not invoke native Dump after Results. Keep captures and generated local profiles ignored/uncommitted.
