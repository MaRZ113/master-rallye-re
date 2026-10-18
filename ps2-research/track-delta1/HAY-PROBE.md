# Probe: native hay bales added through the data channel (T3b + T7 step 1)

Question: can a physical prop be added to a PC course with data only, by authoring a `gaAiHayBale` Egg in a loose `Turkey3.xml` (loose files confirmed to load by the user)?
Background: `pc-port/docs/rigid-port1.3/final-report.md` (native class `gaAiHayBale`, initializer `0x004C9CF0` renames the Egg, selects `Misc/Haybale/haybaletest`, creates the body itself with mass 350). This is a channel test, not the tumbleweed: the model is the PC hay bale.

## Candidate
`D:\Game\Master Rallye\research-output\hay-probe\Turkey3.xml` from `hay_probe.py` (source SHA-256 `9f00ef08...`, candidate `91f6cb8f...`, +6229 bytes). It parses as XML and adds three Eggs to the `IContManager` list, where the PS2 course keeps its tumbleweeds:
| Egg | Position (x, y, z) | Source |
|---|---|---|
| hay1 | 3213.66, 43.78, -155.14 | PS2 tumbleweed 1 (y = PC ground + 1.5) |
| hay2 | 2856.79, 22.73, 473.86 | PS2 tumbleweed 2 |
| hay3 | 2856.33, 23.42, 471.85 | PS2 tumbleweed 3 |
Each Egg: model `misc\haybale\haybaletest`, AI 0 `gaAiHayBale` with an empty property element (like `gaVehicleResetManager`), AI 1..3 Null. The rest of the file is byte-identical to the retail PC XML.

## How to run
1. Copy the candidate to `D:\Game\Master Rallye Pristine\DataScene\RaceTest\Turkey3.xml` (replace the limits candidate if that is installed) and start Turkey3.
2. Teleport next to the bales (add to `[ProbeTeleport]`): `Point1=3203.7,43.8,-155.1,0` for hay1, `Point2=2866.8,23.3,473.9,0` for hay2 and hay3.
3. Record: does the game load the course (no crash, no black screen); are bales visible; does the car push or bounce off them; do they fall to the ground and stay stable; does a restart (race, menu, race, three times) crash.
4. Delete the file to return to stock.
Possible outcomes: crash or hang on load (the Egg or class does not accept this authoring, tell me where it stopped), course loads with no bales (silently ignored), or bales that react to the car (the data channel works for native physics props).

## Result 1 (user, 2026-10-18)
Crash during course load, exactly while `haybaletest.dx` is loaded (seen in the debug window). The file itself looks sane: header `0xD00D`, revision 135, same layout as `checkpoint.dx` and `banner.dx`; texture `hay-tga.dxt` sits next to it like the other models. The crash therefore comes either from the model loader or collision resource for this dormant 2001 asset, or from the `gaAiHayBale` initializer.

## Bisect B: same model, no hay AI
`D:\Game\Master Rallye\research-output\hay-probe-visual\Turkey3.xml` (`hay_probe.py --count 1 --visual-only`): one Egg `hay1`, model `misc\haybale\haybaletest`, all AI slots Null, same position as hay1. Install it in place of the hay candidate.
- It crashes at the same place: the model loader fails on `haybaletest.dx` itself, the AI is not involved.
- It loads and the bale is drawn: the loader is fine, and `gaAiHayBale` (initializer, body or collision resource) is the culprit.
Useful with either outcome: the crash address and module from the debugger (exception code, EIP, and the top frames).

## Result 2 and bisect C (2026-10-18)
Bisect B (same model, no hay AI): loads, the bale is visible. So the model file and the loader are fine and the crash comes from `gaAiHayBale`.
Disassembly of its initializer (`0x004C9CF0`, objdump): it takes the Egg's en3d component (`[Egg+0x50]`), calls `0x004F5B70` with the model string `Misc/Haybale/haybaletest` (the call that loads the model), ORs flag 1 into the component, then calls `0x0043E2A0` to create the physical body from the Egg position (`[component+0x4C]`). The model is therefore loaded a second time over a model that the XML had already loaded. Hypothesis: replacing an already loaded en3d model crashes.
Candidate C: `D:\Game\Master Rallye\research-output\hay-probe-nullmodel\Turkey3.xml` (`hay_probe.py --count 1 --model-null`): one Egg `hay1`, en3d model `Null`, AI 0 `gaAiHayBale`. Expected if the hypothesis holds: loads, the bale is drawn by the initializer's model and is physical.
