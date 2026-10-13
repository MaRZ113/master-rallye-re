# Yellow checkpoint barrels: separate mechanism

The user screenshot of PS2 Turkey3 confirms the visual appearance of yellow checkpoint barrels in that view (**USER_RUNTIME_OBSERVATION / SCREENSHOT_CORRELATION**). A screenshot cannot establish a rigid owner or a contact response.

Existing CDELTA1 byte evidence selects `misc\objects\checkpoints\checkpoint` in 431 PS2 checkpoint-model Eggs across the paired 36 scenes. Every such Egg has `Hitable=True` and no non-Null authored AI owner; they are not `gaAiRigidBody` Eggs. Separate `gaRaceSplitTimeAI` model-less Eggs own gameplay split timing. PC selects `misc\checkpoints\checkpoint` in 440 paired visual references, also with `Hitable=True`, while the user reports different collision behavior. These are authored reference counts, not live simultaneous barrel counts.

The active PS2 barrel PSM is 4,924 bytes, with `drum $shader(metal)` / `top $shader(metal)` and c-point/aluminium/top texture references. The legacy PS2 planks/stamp checkpoint is a different 7,465-byte resource that no scanned PS2 RaceTest Egg selects. Never replace the timing trigger or derive barrel placement from its radius.

PC contains a native `gaAiHayBale` physical-prop owner, but that does not prove automatic checkpoint barrels use it. The exact PS2 barrel tag101/implicit collision/body creation path and its PC equivalent remain **UNKNOWN**. A visual-only private barrel would not satisfy the requested collision/knockability goal and should be labeled accordingly.

Required bounded follow-up after the tumbleweed native control: trace the active PS2 checkpoint PSM load and scene registration to its collision carrier/body, correlate one original barrel contact in PCSX2, and compare the PC legacy checkpoint registration. Do not attach the tumbleweed's mass/inertia or create a gameplay split owner without this evidence. Dynamic barrel port is not implementation-ready in this preparation.

Source: `ps2-research/cdelta1/checkpoint-survey.md`, CDELTA1 checkpoint/source resource evidence; `ps2-research/rigid1/` for the independently different rigid owner.
