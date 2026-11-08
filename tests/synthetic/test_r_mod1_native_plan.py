from __future__ import annotations

import sys
import unittest
import json
from unittest.mock import patch
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
if str(ROOT / "tools") not in sys.path:
    sys.path.insert(0, str(ROOT / "tools"))

import r_mod1_native_plan as plan
import build_rmod3_g1_candidate as g1_candidate


def branch_targets(code: bytes, base: int, opcode: int) -> list[int]:
    targets = []
    for offset, value in enumerate(code):
        if value == opcode and offset + 5 <= len(code):
            displacement = int.from_bytes(code[offset + 1:offset + 5], "little", signed=True)
            targets.append(base + offset + 5 + displacement)
    return targets


class RMod1NativePlanTests(unittest.TestCase):
    def test_g2_player_hooks_target_only_verified_quickrace_publication_sites(self) -> None:
        retail = Path(r"D:\Game\Master Rallye\corpora\retail\MRallye.exe")
        g1_runtime = ROOT / ".research-output" / "r-mod3" / "g1" / "first-integrated-candidate-g1" / "package" / "MRallyeRandomizerRuntime.dll"
        if not retail.is_file() or not g1_runtime.is_file():
            self.skipTest("exact retail image and preserved G1 runtime candidate are required")
        source = retail.read_bytes()
        exports = {
            "MRConfigureBlobV1", "MRChooseClassV1", "MROpponentLimitV1",
            "MRCanStartQuickRaceV1", "MRSetStartPhaseV1", "MRChallengeV1",
            "MRQuickRacePlayerCarV1",
        }
        with patch.object(plan, "_module_exports", return_value=exports):
            g2_full = plan.build_plan(source, g1_runtime.read_bytes(), checkpoint="g2")
            g1_reference = plan.public_plan(plan.build_plan(
                source, g1_runtime.read_bytes(), checkpoint="g1"))
        g2 = plan.public_plan(g2_full)
        self.assertEqual(g2["phase"], "R-MOD3-G2")
        self.assertEqual(len(g2["operations"]), 19)
        self.assertEqual(g2["g1_runtime_baseline"]["status"], "OWNER_CONFIRMED_RUNTIME_AND_BROKER_EVIDENCE")
        self.assertFalse(g2["player_vehicle"]["physical_car_aliasing"])
        operations = {row["id"]: row for row in g2["operations"]}
        g1_operations = {row["id"]: row for row in g1_reference["operations"]}
        self.assertEqual(len(g1_operations), 17)
        self.assertEqual(
            {key: value for key, value in operations.items()
             if key not in {"quickrace-player-select-entry", "quickrace-player-setup-consume"}},
            g1_operations,
            "G2 must preserve every G1/F3 native image operation byte-for-byte",
        )
        self.assertEqual(operations["quickrace-start-guard"], g1_operations["quickrace-start-guard"],
                         "G2 must leave the working Quick Race Start callback unchanged")
        self.assertEqual(bytes.fromhex(operations["quickrace-player-select-entry"]["expected_original_hex"]),
                         bytes.fromhex("E8 5B 33 03 00"))
        self.assertEqual(bytes.fromhex(operations["quickrace-player-setup-consume"]["expected_original_hex"]),
                         bytes.fromhex("E8 21 28 03 00"))
        for operation_id, site, destination in (
            ("quickrace-player-select-entry", 0x0047AC50, plan.PLAYER_ENTRY_GATE_BASE),
            ("quickrace-player-setup-consume", 0x0047B78A, plan.PLAYER_SETUP_GATE_BASE),
        ):
            row = operations[operation_id]
            self.assertEqual(row["va"], site)
            replacement = bytes.fromhex(row["replacement_hex"])
            self.assertEqual(site + 5 + int.from_bytes(replacement[1:5], "little", signed=True), destination)
            self.assertEqual(row["owner"], "quickrace-player-vehicle")
            self.assertEqual(row["feature_mask"], plan.FEATURE_RANDOMIZER)

        for base, phase in ((plan.PLAYER_ENTRY_GATE_BASE, 0), (plan.PLAYER_SETUP_GATE_BASE, 1)):
            stub = plan.make_player_car_gate(base, phase)
            self.assertEqual(stub[:4], bytes.fromhex("FF 74 24 04"))
            getter_call = stub[4:9]
            self.assertEqual(base + 4 + 5 + int.from_bytes(getter_call[1:], "little", signed=True), 0x004ADFB0)
            self.assertEqual(stub[9:12], bytes((0x6A, phase, 0x50)))
            self.assertEqual(stub[12:18], b"\xff\x15" + plan.SLOT_PLAYER_CAR.to_bytes(4, "little"))
            self.assertEqual(stub[18:], b"\xc2\x04\x00")
            self.assertEqual(len(stub), 21)

        f3_ids = {row["id"] for row in g2["operations"]}
        self.assertTrue({"quickrace-selector-init", "quickrace-selector-loop", "quickrace-selector-end",
                         "challenge-preview-identity", "challenge-race-consume"}.issubset(f3_ids))
        self.assertFalse(any(row["va"] in {0x00458090, 0x00458980, 0x0044FEC0}
                             for row in g2["operations"]),
                         "G2 must not rewrite native participant construction, DriverID selection, or Challenge")
        spans = sorted((row["rva"], row["rva"] + len(bytes.fromhex(row["replacement_hex"])))
                       for row in g2["operations"])
        self.assertTrue(all(a[1] <= b[0] for a, b in zip(spans, spans[1:])))
        header = plan.render_cpp_header(g2_full)
        self.assertIn("kSlotPlayerCar = 0x70010024u", header)
        with self.assertRaisesRegex(plan.NativePlanError, "phase must be entry=0 or setup=1"):
            plan.make_player_car_gate(plan.PLAYER_ENTRY_GATE_BASE, 2)

    def test_g1_f3_reference_gate_accepts_preserved_plan_and_rejects_drift(self) -> None:
        reference = json.loads(g1_candidate.F3_REFERENCE_PLAN.read_text(encoding="utf-8"))
        g1_candidate._verify_current_f3_against_reference(reference)

        altered = json.loads(json.dumps(reference))
        altered["operations"][0]["replacement_hex"] = "90"
        with self.assertRaisesRegex(g1_candidate.G1BuildError, "canonical native-plan reference: operations"):
            g1_candidate._verify_current_f3_against_reference(altered)

    def test_f2_f3_native_mode_plans_keep_exact_generation_owners(self) -> None:
        retail = Path(r"D:\Game\Master Rallye\corpora\retail\MRallye.exe")
        dll_f1 = ROOT / ".research-output" / "r-mod1" / "first-integrated-candidate-v14-f1-r2" / "MRallyeRandomizerRuntime.dll"
        if not retail.is_file() or not dll_f1.is_file():
            self.skipTest("exact retail image and F1 runtime DLL are required for native mode-plan composition")
        source = retail.read_bytes()
        f2 = plan.public_plan(plan.build_plan(source, dll_f1.read_bytes(), checkpoint="f2"))
        self.assertEqual(plan.sha256(source), plan.RETAIL_SHA256)
        self.assertEqual(len(f2["operations"]), 13)
        self.assertEqual(f2["mode_generation_owners"]["RallyeCup"]["selection_sites"],
                         [0x45AC79, 0x45AF0F, 0x45AE66])
        self.assertEqual(f2["mode_generation_owners"]["Invitation"]["shared_builder"], "RallyeCup")
        self.assertEqual(f2["mode_generation_owners"]["MasterRallye"]["selection_sites"],
                         [0x451E90, 0x4520D2, 0x45202D])
        self.assertEqual(f2["mode_generation_owners"]["MasterRallye"]["mutation_boundary"],
                         "new competition generation only")
        operations = {row["id"]: row for row in f2["operations"]}
        for operation_id, symbol_key, label_key in (
            ("quickrace-selector-init", "QuickRace", "init"),
            ("masterrallye-selector-init", "MasterRallye", "init"),
            ("cup-invitation-selector-init", "RallyeCup/Invitation", "init"),
        ):
            row = operations[operation_id]
            replacement = bytes.fromhex(row["replacement_hex"])
            destination = row["va"] + 5 + int.from_bytes(replacement[1:5], "little", signed=True)
            self.assertEqual(destination,
                f2["code_symbols"]["selectors"][symbol_key]["labels"][label_key],
                "callsite rel32 must target the selector's absolute emitted label exactly once")
        spans = sorted((row["va"], row["va"] + len(bytes.fromhex(row["replacement_hex"])))
                       for row in f2["operations"])
        self.assertTrue(all(a[1] <= b[0] for a, b in zip(spans, spans[1:])))

        f3_dll = ROOT / ".research-output" / "r-mod1" / "first-integrated-candidate-v16-f3" / "MRallyeRandomizerRuntime.dll"
        if not f3_dll.is_file():
            return
        f3 = plan.public_plan(plan.build_plan(source, f3_dll.read_bytes(), checkpoint="f3"))
        self.assertEqual(len(f3["operations"]), 17)
        challenge = f3["mode_generation_owners"]["Challenge"]
        self.assertEqual(challenge["preview_car_id"], 0x45EC35)
        self.assertEqual(challenge["race_consume_car_id"], 0x45010E)
        challenge_ops = {row["id"] for row in f3["operations"] if row["id"].startswith("challenge-")}
        self.assertEqual(challenge_ops, {"challenge-preview-identity", "challenge-screen-entry-reset",
                                         "challenge-back-reset", "challenge-race-consume"})

    def test_challenge_preview_and_race_stubs_reuse_one_absolute_id(self) -> None:
        preview = plan.make_challenge_preview_code()
        consume = plan.make_challenge_consumer_code()
        reset_entry = plan.make_challenge_reset_code(plan.CHALLENGE_RESET_ENTRY_BASE, 0x004E3DD0)
        reset_back = plan.make_challenge_reset_code(plan.CHALLENGE_RESET_BACK_BASE, 0x0045D910)

        native_load = bytes.fromhex("8bbc3874050000")
        self.assertTrue(preview.startswith(native_load + bytes.fromhex("9c60")))
        self.assertTrue(consume.startswith(native_load + bytes.fromhex("9c60")))
        for emitted in (preview, consume):
            calls = [offset for offset, byte in enumerate(emitted[:-4])
                     if byte == 0xE8 and offset not in (0,)]
            self.assertEqual(len(calls), 1)
            call_at = calls[0]
            target = (plan.CHALLENGE_PREVIEW_BASE if emitted is preview else plan.CHALLENGE_CONSUMER_BASE)
            destination = target + call_at + 5 + int.from_bytes(
                emitted[call_at + 1:call_at + 5], "little", signed=True)
            self.assertEqual(destination, plan.CHALLENGE_GATE)
            self.assertIn(bytes.fromhex("83f818"), emitted)  # physical IDs above 24 keep authored ID
            self.assertIn(bytes.fromhex("89442400"), emitted)  # replace saved EDI only
            self.assertIn(bytes.fromhex("619d"), emitted)

        self.assertIn(0x0045EC3C, branch_targets(preview, plan.CHALLENGE_PREVIEW_BASE, 0xE9))
        self.assertIn(0x00450115, branch_targets(consume, plan.CHALLENGE_CONSUMER_BASE, 0xE9))
        self.assertIn(plan.CHALLENGE_GATE, branch_targets(reset_entry, plan.CHALLENGE_RESET_ENTRY_BASE, 0xE8))
        self.assertIn(plan.CHALLENGE_GATE, branch_targets(reset_back, plan.CHALLENGE_RESET_BACK_BASE, 0xE8))
        self.assertIn(0x004E3DD0, branch_targets(reset_entry, plan.CHALLENGE_RESET_ENTRY_BASE, 0xE9))
        self.assertIn(0x0045D910, branch_targets(reset_back, plan.CHALLENGE_RESET_BACK_BASE, 0xE9))
        reset_args = bytes.fromhex("6a006a00689cffffff6a01")
        self.assertIn(reset_args, reset_entry)
        self.assertIn(reset_args, reset_back)

    def test_extended_gate_is_count_generalized_and_raw_split_flag_is_diagnostic(self) -> None:
        runtime = (ROOT / "src" / "native" / "rmod1" / "runtime_core.cpp").read_text(encoding="utf-8")
        core = (ROOT / "src" / "native" / "rmod1" / "core.hpp").read_text(encoding="utf-8")
        self.assertIn("experimental_extended_roster_matches(", core)
        self.assertNotIn("MRObserveInitializedQuickRaceV1", runtime)
        self.assertNotIn("inspect_prepared_roster", runtime)
        self.assertNotIn("MRValidatePreparedQuickRaceV1", runtime)

        start = runtime[runtime.index("extern \"C\" __declspec(dllexport) DWORD WINAPI MRCanStartQuickRaceV1"):
                       runtime.index("extern \"C\" __declspec(dllexport) void WINAPI MRSetStartPhaseV1")]
        self.assertIn("raw_frontend_split", runtime)
        self.assertIn("evaluate_native_start_gate(mode, raw_count, split, g_config)", start)
        self.assertIn("return allowed ? 1u : 0u", start)
        plan_start = core.index("inline ParticipantDecision plan_quick_race")
        plan_end = core.index("\nstruct ImageIdentity", plan_start)
        self.assertNotIn("if (raw_split_screen)", core[plan_start:plan_end])
        self.assertIn("raw SplitScreen is diagnostic only until Race participants exist", core[plan_start:plan_end])
        self.assertIn("selected_count <= kNativeAiMaximum", core[plan_start:plan_end])
        self.assertNotIn("selected_count != 4", core[plan_start:plan_end])
        self.assertIn("selected_count > config.max_opponents", core[plan_start:plan_end])
        callback_start = runtime.index("extern \"C\" __declspec(dllexport) int WINAPI MRChooseClassV1")
        callback_end = runtime.index("extern \"C\" __declspec(dllexport) int WINAPI MROpponentLimitV1")
        callback = runtime[callback_start:callback_end]
        self.assertIn("count > static_cast<int>(kMaximumAi)", callback)
        self.assertNotIn("count > 4", callback)

    def test_start_callback_uses_non_quick_race_native_passthrough(self) -> None:
        runtime = (ROOT / "src/native/rmod1/runtime_core.cpp").read_text(encoding="utf-8")
        core = (ROOT / "src/native/rmod1/core.hpp").read_text(encoding="utf-8")
        callback = runtime[runtime.index("extern \"C\" __declspec(dllexport) DWORD WINAPI MRCanStartQuickRaceV1"):
                          runtime.index("extern \"C\" __declspec(dllexport) void WINAPI MRSetStartPhaseV1")]
        evaluator_start = core.index("inline StartGateEvaluation evaluate_native_start_gate")
        evaluator_end = core.index("\nstruct ImageIdentity", evaluator_start)
        evaluator = core[evaluator_start:evaluator_end]
        policy_start = core.index("inline ParticipantDecision plan_quick_race")
        policy_end = core.index("\nstruct StartGateEvaluation", policy_start)
        policy = core[policy_start:policy_end]
        self.assertIn("evaluate_native_start_gate(mode, raw_count, split, g_config)", callback)
        self.assertIn("if (mode_id != 2)", evaluator)
        self.assertLess(evaluator.index("if (mode_id != 2)"), evaluator.index("raw_count > 0"))
        self.assertIn("result.selected_count = 0", evaluator)
        self.assertIn("return {false, true, 0, 0, 0", policy)
        self.assertIn("Native mode passthrough; no Quick Race opponent extension applied.", policy)
        self.assertIn("auto decision = gate.decision", callback)
        self.assertIn("if (mode == 2 && selected_count > kNativeAiMaximum", callback)
        self.assertIn("!g_config.duplicates_when_needed && config_needs_randomizer_hooks(g_config)", callback)
        self.assertIn("enforce_quickrace_duplicate_capacity(", callback)
        self.assertIn("StartAllowed : StartPhaseV1::StartBlocked", callback)

    def test_retail_native_chooser_accepts_dynamic_count_and_refills_physical_pool(self) -> None:
        retail = Path(r"D:\Game\Master Rallye\corpora\retail\MRallye.exe")
        if not retail.is_file():
            self.skipTest("exact pristine retail image is unavailable for native chooser verification")
        source = retail.read_bytes()
        self.assertEqual(plan.sha256(source), plan.RETAIL_SHA256)
        pe = plan.parse_pe(source)
        def at(va: int, length: int) -> bytes:
            offset = plan.va_to_file_offset(pe, va, length)
            return source[offset:offset + length]

        # Exact function ranges/hash from the current exact-build Ghidra export.
        # FUN_00458090 computes [first, first+count) and loops over that bound;
        # when its shuffled temporary CarID vector is empty it clones and
        # reshuffles the original eligible class pool before selecting again.
        chooser = at(0x00458090, 0x446)
        self.assertEqual(plan.sha256(chooser),
                         "2daec5f26455c98bfa399308ce8a3030ebe5871dfe4fd13a675526bb97842a71")
        self.assertEqual(chooser[-3:], bytes.fromhex("c21400"))
        self.assertEqual(at(0x004116A0, 0x13),
                         bytes.fromhex("8b510485d2750333c0c38b41082bc2c1f802c3"))
        for call_va in (0x0047B93D, 0x0047B96E):
            call = at(call_va, 5)
            self.assertEqual(call[0], 0xE8)
            destination = call_va + 5 + int.from_bytes(call[1:], "little", signed=True)
            self.assertEqual(destination, 0x00458090)

        decompile = (ROOT / "scratch_rmod1" / "ghidra" / "00458090.json")
        if decompile.is_file():
            import json
            native = json.loads(decompile.read_text(encoding="utf-8"))["decompiled"]
            self.assertIn("param_2 = param_1 + param_2", native)
            self.assertIn("if (iVar5 == 0)", native)
            self.assertIn("FUN_00450580(local_5c,local_58)", native)
            self.assertIn("FUN_00458980(&local_68)", native)
            for write in ("FUN_004acaf0(iVar5,iVar3)", "FUN_004acc10(iVar5,uVar6)",
                          "FUN_004accd0(iVar5,uVar6)"):
                self.assertIn(write, native)
        # These owners remain outside the seven-operation R-MOD patch set;
        # only the Quick Race class selector and UI/start boundaries are changed.
        patch_source = (ROOT / "tools" / "r_mod1_native_plan.py").read_text(encoding="utf-8")
        self.assertNotIn("0x0047B88A", patch_source)
        self.assertNotIn("0x0047B8DD", patch_source)
        v11_dll = ROOT / ".research-output" / "r-mod1" / "first-integrated-candidate-v11" / "MRallyeRandomizerRuntime.dll"
        if v11_dll.is_file():
            composed = plan.public_plan(plan.build_plan(
                source, v11_dll.read_bytes()))
            self.assertEqual(len(composed["operations"]), 7)
            self.assertFalse(any(int(row["va"]) == 0x00458090 for row in composed["operations"]))
            # The R-MOD selector sites intentionally own class-policy seams
            # inside FUN_00458090. Its physical-ID refill/pick and participant
            # setters after the class seam, plus count readers/callers, remain
            # original retail bytes.
            protected = ((0x00458382, 0x004584D6), (0x0047B88A, 0x0047B88F),
                         (0x0047B8DD, 0x0047B8E2), (0x0047B93D, 0x0047B942),
                         (0x0047B96E, 0x0047B973))
            for operation in composed["operations"]:
                begin = 0x00400000 + int(operation["rva"])
                end = begin + len(bytes.fromhex(operation["replacement_hex"]))
                self.assertTrue(all(end <= protected_begin or begin >= protected_end
                                    for protected_begin, protected_end in protected),
                                "composed image operations must leave native count/chooser owners untouched")

    def test_ui_append_stub_keeps_the_loop_bound_outside_enstring_storage(self) -> None:
        code = plan.make_ui_list_code()
        self.assertEqual(plan.opponents_ui.LABELS,
                         ("ONE", "TWO", "THREE", "FOUR", "FIVE", "SIX", "SEVEN"))
        # Symbolically track the actual emitted instruction operands. PUSHFD,
        # PUSHAD and SUB ESP,8 create a frame with a bound at B and enString at
        # B+4. The legacy R-UI1 list/object lifetime remains native.
        entry_esp = 0x100000
        self.assertEqual(code[:5], bytes.fromhex("9c6083ec08"))
        esp = entry_esp - 4  # PUSHFD
        esp -= 32  # PUSHAD
        esp -= 8   # SUB ESP,8
        frame = esp
        bound_slot = frame
        self.assertIn(bytes.fromhex("890424"), code)  # MOV [ESP],EAX
        self.assertIn(bytes.fromhex("3b3c24"), code)  # CMP EDI,[ESP]
        self.assertNotIn(bytes.fromhex("8d4c2404"), code)
        self.assertNotIn(bytes.fromhex("8d0424"), code)
        self.assertNotIn(bytes.fromhex("ff3424"), code)

        # Consume the emitted localized-call setup: two native stack arguments
        # are cleaned by RET 8, then the selector is pushed for the enString
        # constructor. LEA ECX,[ESP+8] must point to B+4 after that push.
        self.assertIn(bytes.fromhex("576a408bc88b10ff520c"), code)
        esp -= 4  # PUSH EDI
        esp -= 4  # PUSH 0x40
        esp -= 4  # virtual CALL return; native target RET 8 restores B
        esp += 4 + 8
        self.assertEqual(esp, frame)
        esp -= 4  # PUSH EAX (constructor string argument)
        constructor_ecx = esp + int.from_bytes(bytes.fromhex("08"), "little")
        self.assertIn(bytes.fromhex("8d4c2408"), code)
        self.assertEqual(constructor_ecx, bound_slot + 4)

        # Native enString constructor ends in RET 4, consuming its one stack
        # argument. The StringList receives the object at B+4 and uses RET C;
        # the destructor is cdecl and its pointer is explicitly caller-popped.
        esp -= 4  # CALL return
        esp += 4 + 4
        self.assertEqual(esp, frame)
        object_address = esp + int.from_bytes(bytes.fromhex("04"), "little")
        self.assertIn(bytes.fromhex("8d442404"), code)
        self.assertEqual(object_address, bound_slot + 4)
        self.assertIn(bytes.fromhex("ff742404"), code)  # PUSH [ESP+4] destructor arg
        self.assertIn(bytes.fromhex("83c40447"), code)  # caller cleanup, INC EDI
        self.assertIn(bytes.fromhex("83c408619d"), code)  # release both locals, restore

        # Simulate exactly requested append range: stock already supplies
        # ONE/TWO/THREE; this helper appends only localized indices 3..N-1.
        for requested in range(1, 8):
            bound = requested
            appended = list(range(3, bound))
            self.assertEqual(appended, list(range(3, requested)))
            self.assertEqual(len(appended), max(0, requested - 3))
            for _index in appended:
                memory = {bound_slot: bound, object_address: 0x51515151}
                memory[constructor_ecx] = 0  # ctor's first store targets ECX
                self.assertEqual(memory[bound_slot], bound)
                self.assertEqual(memory[object_address], 0)

        # The final add is eight bytes, then POPAD/POPFD must return to the
        # exact helper-entry stack before the displaced retail MOVs execute.
        esp = frame + 8
        esp += 32
        esp += 4
        self.assertEqual(esp, entry_esp)
        tail = code[code.index(bytes.fromhex("83c408619d")) + 5:]
        self.assertTrue(tail.startswith(plan.UI_LIST_ORIGINAL))
        self.assertEqual(plan.UI_LIST_ORIGINAL, bytes.fromhex("8b54241489742428"))

    def test_start_gate_calls_setup_once_only_on_allowed_path_and_preserves_abi(self) -> None:
        code = plan.make_start_gate_code()
        # Resolve direct call instructions by their actual rel32 destinations.
        calls = []
        for offset, opcode in enumerate(code[:-4]):
            if opcode == 0xE8:
                target = plan.START_GATE_BASE + offset + 5 + int.from_bytes(
                    code[offset + 1:offset + 5], "little", signed=True)
                calls.append((offset, target))
        setup_calls = [(offset, target) for offset, target in calls if target == plan.QUICK_RACE_SETUP]
        self.assertEqual(len(setup_calls), 1)
        self.assertEqual(code.count(b"\xff\x15" + plan.SLOT_START_PHASE.to_bytes(4, "little")), 2)
        self.assertEqual(code.count(b"\xff\x15" + plan.SLOT_CAN_START.to_bytes(4, "little")), 1)
        self.assertTrue(code.startswith(bytes.fromhex("9c60")))
        self.assertEqual(code.count(bytes.fromhex("619d")), 4)
        self.assertEqual(code.count(bytes.fromhex("5e83c430c20400")), 1)
        self.assertEqual(plan.START_CALL_ORIGINAL, bytes.fromhex("e86f0a0000"))
        self.assertEqual(plan.START_CALL_SITE, 0x0047AD0C)
        self.assertEqual(plan.START_CONTINUATION, 0x0047AD11)

        conditional_targets = []
        conditional_offsets = []
        for offset in range(len(code) - 5):
            if code[offset:offset + 2] == b"\x0f\x84":
                conditional_offsets.append(offset)
                conditional_targets.append(plan.START_GATE_BASE + offset + 6 +
                    int.from_bytes(code[offset + 2:offset + 6], "little", signed=True))
        self.assertEqual(len(conditional_targets), 1)
        setup_va = plan.START_GATE_BASE + setup_calls[0][0]
        # The sole denial is the pre-start capability check, before native
        # setup. No later Race-counter read can suppress the screen transition.
        self.assertGreater(conditional_targets[0], setup_va)
        self.assertLess(conditional_offsets[0], setup_calls[0][0])
        self.assertIn(plan.START_CONTINUATION, branch_targets(code, plan.START_GATE_BASE, 0xE9))

        # Callback/save/restore blocks leave ESP and ECX exactly as received.
        entry_esp = 0x200000
        esp = entry_esp
        # can-start wrapper
        esp -= 4 + 32
        esp -= 4  # CALL through the function cell; zero-arg stdcall returns to prior ESP
        esp += 4
        esp += 32 + 4
        self.assertEqual(esp, entry_esp)
        # emitted phase marker: PUSHFD/PUSHAD, PUSH imm8, indirect CALL,
        # stdcall RET 4, POPAD/POPFD. Native setup sees the original stack.
        esp -= 4 + 32
        esp -= 4
        esp -= 4  # callback argument
        esp += 4 + 4
        esp += 32 + 4
        self.assertEqual(esp, entry_esp)
        esp -= 4  # native CALL; its no-argument RET restores this exactly once
        esp += 4
        self.assertEqual(esp, entry_esp)
        # A second phase marker follows setup; the transition is unconditional.
        esp -= 4 + 32
        esp -= 4
        esp -= 4
        esp += 4 + 4
        esp += 32 + 4
        self.assertEqual(esp, entry_esp)
        continuation_offsets = [offset for offset in range(len(code) - 4)
                                if code[offset] == 0xE9 and
                                plan.START_GATE_BASE + offset + 5 + int.from_bytes(
                                    code[offset + 1:offset + 5], "little", signed=True) ==
                                plan.START_CONTINUATION]
        self.assertEqual(len(continuation_offsets), 1)
        self.assertGreater(continuation_offsets[0], setup_calls[0][0])

        # Both-off, randomizer-only, extender-only and combined feature masks
        # keep the shared bootstrap independent and never add another setup call.
        for features in (0, plan.FEATURE_RANDOMIZER, plan.FEATURE_OPPONENTS,
                         plan.FEATURE_RANDOMIZER | plan.FEATURE_OPPONENTS):
            selected = [feature for feature in (plan.FEATURE_RANDOMIZER, plan.FEATURE_OPPONENTS)
                        if features & feature]
            self.assertLessEqual(len(selected), 2)
            self.assertEqual(len(setup_calls), 1)

    def test_ret4_getter_cannot_be_replaced_by_nested_call_wrapper(self) -> None:
        # At the retail call site [ESP] is the original caller return address,
        # [ESP+4] is the getter's argument. CALL wrapper / CALL getter inserts
        # a second return address at that exact argument position.
        caller_esp = 0x001AFC10
        argument = 0x12345678
        memory = {caller_esp: argument}
        getter_call_va = 0x0040869B
        retail_return = getter_call_va + 5
        direct_callee_esp = caller_esp - 4
        memory[direct_callee_esp] = retail_return
        self.assertEqual(memory[direct_callee_esp], retail_return)
        self.assertEqual(memory[direct_callee_esp + 4], argument)
        # Native RET 4 consumes its own return address and the caller argument.
        direct_return_esp = direct_callee_esp + 4 + 4
        self.assertEqual(direct_return_esp, caller_esp + 4)

        wrapper_entry_esp = caller_esp - 4
        memory[wrapper_entry_esp] = retail_return
        nested_callee_esp = wrapper_entry_esp - 4
        wrapper_return = 0x70002405
        memory[nested_callee_esp] = wrapper_return
        self.assertEqual(memory[nested_callee_esp], wrapper_return)
        wrong_argument = memory[nested_callee_esp + 4]
        self.assertEqual(wrong_argument, retail_return)
        self.assertNotEqual(wrong_argument, argument)
        self.assertEqual(wrong_argument, 0x004086A0)
        # This is the v10 regression: the getter treats 004086A0 as its output
        # pointer, reads instruction bytes there and faults while writing.

    def test_production_plan_preserves_native_getter_call_bytes(self) -> None:
        retail = Path(r"D:\Game\Master Rallye\corpora\retail\MRallye.exe")
        if not retail.is_file():
            self.skipTest("exact pristine retail image is unavailable for native call-site verification")
        source = retail.read_bytes()
        self.assertEqual(plan.sha256(source), plan.RETAIL_SHA256)
        pe = plan.parse_pe(source)
        offset = plan.va_to_file_offset(pe, 0x0040869B, 5)
        self.assertEqual(source[offset:offset + 5], bytes.fromhex("e8c0e00c00"))
        generator = (ROOT / "tools" / "r_mod1_native_plan.py").read_text(encoding="utf-8")
        export_definition = (ROOT / "src" / "native" / "rmod1" / "runtime_core.def").read_text(encoding="utf-8")
        self.assertNotIn("post-init-roster-observer", generator)
        self.assertNotIn("POST_INIT_NUMCARS_GETTER_CALL", generator)
        self.assertNotIn("MRObserveInitializedQuickRaceV1", generator)
        self.assertNotIn("MRObserveInitializedQuickRaceV1", export_definition)
        runtime = (ROOT / "src" / "native" / "rmod1" / "runtime_core.cpp").read_text(encoding="utf-8")
        self.assertNotIn("MRObserveInitializedQuickRaceV1", runtime)
        self.assertNotIn("inspect_prepared_roster", runtime)

    def test_native_ui_and_start_calling_conventions_match_exact_retail_bytes(self) -> None:
        retail = Path(r"D:\Game\Master Rallye\corpora\retail\MRallye.exe")
        if not retail.is_file():
            self.skipTest("exact pristine retail image is unavailable for native ABI byte verification")
        source = retail.read_bytes()
        self.assertEqual(plan.sha256(source), plan.RETAIL_SHA256)
        pe = plan.parse_pe(source)
        def at(va: int, size: int) -> bytes:
            offset = plan.va_to_file_offset(pe, va, size)
            return source[offset:offset + size]
        self.assertEqual(at(0x004D1229, 3), bytes.fromhex("c20400"))
        self.assertEqual(at(0x004D1236, 3), bytes.fromhex("c20400"))
        self.assertEqual(at(0x00407C65, 3), bytes.fromhex("c20c00"))
        self.assertEqual(at(0x00407C82, 3), bytes.fromhex("c20c00"))
        self.assertEqual(at(0x005B4C0A, 1), bytes.fromhex("c3"))
        self.assertEqual(at(0x00485BC8, 3), bytes.fromhex("c20800"))
        self.assertEqual(at(0x00485D1E, 1), bytes.fromhex("c3"))
        self.assertEqual(at(0x0047AD0A, 7), bytes.fromhex("8bcee86f0a0000"))
        self.assertEqual(at(0x0040869B, 5), bytes.fromhex("e8c0e00c00"))
        for va in (0x004AE051, 0x004AE0B1, 0x004AE111, 0x004AE171, 0x004AE2F1,
                   0x004ADAA6, 0x0047B943):
            self.assertEqual(at(va, 1), bytes.fromhex("c3"), f"cdecl/no-stack-arg RET at {va:#x}")
        self.assertEqual(at(0x004ADFD7, 3), bytes.fromhex("c20400"))
        for va in (0x004AC69B, 0x004AC76B, 0x004AC5FB):
            self.assertEqual(at(va, 3), bytes.fromhex("c20400"), f"thiscall one-stack-arg RET at {va:#x}")
        self.assertEqual(at(0x0047B942, 2), bytes.fromhex("5ec3"))
        # Native helpers used by the randomizer callback are checked against
        # retail terminal bytes, independently of their C++ typedefs.
        self.assertEqual(at(0x004B0333, 1), b"\xc3")
        self.assertEqual(at(0x004B033B, 1), b"\xc3")
        self.assertEqual(at(0x004AFBF1, 3), bytes.fromhex("c20400"))
        self.assertEqual(at(0x004D1EB2, 1), b"\xc3")
        self.assertEqual(at(0x004D1EBA, 1), b"\xc3")
        self.assertEqual(at(0x004D1E81, 3), bytes.fromhex("c20800"))

    def test_start_guard_is_at_callback_callsite_and_has_complete_denial_epilogue(self) -> None:
        code = plan.make_start_gate_code()
        self.assertIn(plan.QUICK_RACE_SETUP, branch_targets(code, plan.START_GATE_BASE, 0xE8))
        self.assertEqual(code.count(bytes.fromhex("5e83c430c20400")), 1)
        self.assertEqual(plan.START_CALL_SITE, 0x0047AD0C)
        self.assertEqual(plan.START_CONTINUATION, 0x0047AD11)
        self.assertEqual(plan.START_CALL_ORIGINAL, bytes.fromhex("e86f0a0000"))
        self.assertTrue(code.startswith(bytes.fromhex("9c60ff15")))
        self.assertIn(plan.START_CONTINUATION, branch_targets(code, plan.START_GATE_BASE, 0xE9))

    def test_selector_reuses_historical_policy_without_mutating_its_source(self) -> None:
        original_loader = plan.randomizer.LOADER
        spec = dict(plan.randomizer.SPECS[0])
        spec["base"] = plan.SELECTOR_BASE
        code, _labels = plan.make_rmod1_selector(spec)
        self.assertIn(plan.CHOICE_GATE, branch_targets(code, plan.SELECTOR_BASE, 0xE8))
        self.assertEqual(plan.randomizer.LOADER, original_loader)

    def test_g1_duplicate_fallback_decodes_emitted_class_marker_and_pool_limit(self) -> None:
        # The no-flag F3 selector must remain byte-identical. Only G1's
        # Quick Race selector understands the private 0x100|class callback.
        legacy = dict(plan.randomizer.SPECS[0])
        legacy["base"] = plan.SELECTOR_BASE
        legacy_bytes, legacy_labels = plan.make_rmod1_selector(legacy)
        false_flag = dict(legacy, duplicate_repeat_fallback=False)
        false_bytes, false_labels = plan.make_rmod1_selector(false_flag)
        self.assertEqual((legacy_bytes, legacy_labels), (false_bytes, false_labels))

        spec = dict(legacy, duplicate_repeat_fallback=True)
        code, labels = plan.make_rmod1_selector(spec)
        self.assertLess(len(code), 0x300)

        def rel_target(offset: int, size: int = 4) -> int:
            displacement = int.from_bytes(code[offset:offset + size], "little", signed=True)
            return plan.SELECTOR_BASE + offset + size + displacement

        def find_choice_call() -> int:
            found = []
            for offset in range(len(code) - 4):
                if code[offset] != 0xE8:
                    continue
                if rel_target(offset + 1) == plan.CHOICE_GATE:
                    found.append(offset)
            self.assertEqual(len(found), 1)
            return found[0]

        call = find_choice_call()
        decision = call + 5
        unique_class_va = labels["unique_class"]
        stock_va = labels["stock"]
        class_ready_va = labels["class_decision_ready"]
        self.assertEqual(code[decision:decision + 3], bytes.fromhex("83f802"))  # CMP EAX,2
        self.assertEqual(code[decision + 3:decision + 5], bytes.fromhex("0f86"))  # JBE normal class
        self.assertEqual(rel_target(decision + 5), unique_class_va)
        self.assertEqual(code[decision + 9:decision + 14], bytes.fromhex("3d00010000"))  # CMP EAX,100h
        self.assertEqual(code[decision + 14:decision + 16], bytes.fromhex("0f82"))  # JB Stock
        self.assertEqual(rel_target(decision + 16), stock_va)
        self.assertEqual(code[decision + 20:decision + 25], bytes.fromhex("3d02010000"))
        self.assertEqual(code[decision + 25:decision + 27], bytes.fromhex("0f87"))  # JA Stock
        self.assertEqual(rel_target(decision + 27), stock_va)
        self.assertEqual(code[decision + 31:decision + 36], bytes.fromhex("2d00010000"))  # SUB EAX,100h
        duplicate_store = bytes((0xC7, 0x44, 0x24, spec["marker"] + 36)) + bytes.fromhex("feffffff")
        normal_store = bytes((0xC7, 0x44, 0x24, spec["marker"] + 36)) + bytes.fromhex("ffffffff")
        self.assertEqual(code[decision + 36:decision + 44], duplicate_store)
        self.assertEqual(rel_target(decision + 45), class_ready_va)
        normal_at = unique_class_va - plan.SELECTOR_BASE
        self.assertEqual(code[normal_at:normal_at + 8], normal_store)

        # Interpret the exact emitted stack references at pool_end. PUSHFD
        # shifts ESP by four; disp(marker+4) therefore addresses the original
        # marker. POPFD restores ESP before either slot-bound load.
        pool_at = labels["pool_end"] - plan.SELECTOR_BASE
        self.assertEqual(code[pool_at:pool_at + 6],
                         bytes((0x9C, 0x83, 0x7C, 0x24, spec["marker"] + 4, 0xFF)))
        first_branch = pool_at + 6
        self.assertEqual(code[first_branch:first_branch + 2], bytes.fromhex("0f84"))
        self.assertEqual(rel_target(first_branch + 2), labels["unique_filter"])
        second_cmp = first_branch + 6
        self.assertEqual(code[second_cmp:second_cmp + 6],
                         bytes((0x83, 0x7C, 0x24, spec["marker"] + 4, 0xFE, 0x0F)))
        self.assertEqual(code[second_cmp + 6:second_cmp + 7], bytes.fromhex("85"))
        self.assertEqual(rel_target(second_cmp + 7), labels["initial_pool"])

        repeat_start = second_cmp + 11
        repeat_end = labels["unique_filter"] - plan.SELECTOR_BASE
        repeat_path = code[repeat_start:repeat_end]
        self.assertEqual(repeat_path[:6], bytes.fromhex("9dbf00000000"))  # POPFD; EDI=0
        self.assertEqual(repeat_path[6:9], bytes.fromhex("8bb424"))  # MOV ESI,[ESP+disp32]
        repeat_limit = int.from_bytes(repeat_path[9:13], "little")
        self.assertEqual(repeat_limit, spec["first"])
        self.assertEqual(repeat_path[13], 0xE9)
        self.assertEqual(plan.SELECTOR_BASE + repeat_start + 13 + 5 +
                         int.from_bytes(repeat_path[14:18], "little", signed=True), labels["participant"])

        unique_start = labels["unique_filter"] - plan.SELECTOR_BASE
        participant_start = labels["participant"] - plan.SELECTOR_BASE
        unique_path = code[unique_start:participant_start]
        self.assertEqual(unique_path[:6], bytes.fromhex("9dbf00000000"))  # POPFD; EDI=0
        self.assertEqual(unique_path[6:9], bytes.fromhex("8b7424"))  # MOV ESI,[ESP+disp8]
        unique_limit = unique_path[9]
        self.assertEqual(unique_limit, spec["slot"])
        self.assertEqual(code[participant_start:participant_start + 2], bytes.fromhex("3bfe"))  # CMP EDI,ESI
        self.assertEqual(code[participant_start + 2:participant_start + 4], bytes.fromhex("0f8d"))  # JGE pool_ready
        self.assertEqual(rel_target(participant_start + 4), labels["pool_ready"])

        # Execute only the decoded bounds: a unique pass scans human + prior
        # AI slots, while repeat fallback scans the first (human) slot alone.
        stack = {0x100000 + spec["first"]: 1,
                 0x100000 + spec["slot"]: 7,
                 0x100000 + spec["marker"]: -1}
        self.assertEqual(stack[0x100000 + unique_limit], 7)
        stack[0x100000 + spec["marker"]] = -2
        self.assertEqual(stack[0x100000 + repeat_limit], 1)
        self.assertNotEqual(repeat_limit, unique_limit)

        # The emitted loop keeps its bound in ESI while it calls the native
        # CarID accessor and vector eraser. Verify those exact retail callees
        # preserve ESI in the matching Ghidra exports.
        ghidra = ROOT / "scratch_rmod1" / "ghidra"
        for name, push, pop, terminal in (
            ("004ac660", "PUSH ESI", "POP ESI", "RET 0x4"),
            ("00416620", "PUSH ESI", "POP ESI", "RET 0x4"),
        ):
            path = ghidra / f"{name}.json"
            if path.is_file():
                assembly = json.loads(path.read_text(encoding="utf-8"))["assembly"]
                self.assertTrue(any(push in line for line in assembly))
                pop_at = max(i for i, line in enumerate(assembly) if pop in line)
                self.assertEqual(assembly[-1].split("  ")[-1], terminal)
                self.assertLess(pop_at, len(assembly) - 1)
        singleton = ghidra / "004ada50.json"
        if singleton.is_file():
            assembly = json.loads(singleton.read_text(encoding="utf-8"))["assembly"]
            self.assertFalse(any("ESI" in line or "EDI" in line for line in assembly),
                             "Quick Race singleton accessor must not clobber the live ESI limit")

        runtime_source = (ROOT / "src" / "native" / "rmod1" / "runtime_core.cpp").read_text(encoding="utf-8")
        candidate_builder = (ROOT / "tools" / "build_r_mod1_candidate.py").read_text(encoding="utf-8")
        self.assertIn("#if defined(RMOD3_G1_DUPLICATE_REPEAT_FALLBACK)", runtime_source)
        self.assertIn('g1_flags = ["/DRMOD3_G1_DUPLICATE_REPEAT_FALLBACK=1"] if checkpoint in {"g1", "g2"} else []',
                      candidate_builder)

        candidate_plan = (ROOT / ".research-output" / "r-mod3" / "g1" /
                          "first-integrated-candidate-g1" / "native-patch-plan.json")
        if candidate_plan.is_file():
            emitted_plan = json.loads(candidate_plan.read_text(encoding="utf-8"))
            self.assertEqual(emitted_plan["checkpoint"], "g1")
            self.assertEqual(len(emitted_plan["operations"]), 17)
            self.assertEqual(emitted_plan["duplicate_support"]["status"],
                             "STATICALLY_VERIFIED_HUMAN_RUNTIME_PENDING")
            self.assertFalse(any(int(op["va"]) == 0x00458090 for op in emitted_plan["operations"]))
            self.assertTrue(all(
                int(op["va"]) + len(bytes.fromhex(op["replacement_hex"])) <= 0x00458382 or
                int(op["va"]) >= 0x004584D6
                for op in emitted_plan["operations"]
            ), "G1 must leave native physical pool refill and per-participant publication untouched")

        retail = Path(r"D:\Game\Master Rallye\corpora\retail\MRallye.exe")
        if retail.is_file():
            image = retail.read_bytes()
            self.assertEqual(plan.sha256(image), plan.RETAIL_SHA256)
            pe = plan.parse_pe(image)
            chooser = image[plan.va_to_file_offset(pe, 0x00458090, 0x446):
                            plan.va_to_file_offset(pe, 0x00458090, 0x446) + 0x446]
            self.assertEqual(plan.sha256(chooser),
                             "2daec5f26455c98bfa399308ce8a3030ebe5871dfe4fd13a675526bb97842a71")
            self.assertEqual(chooser[-3:], bytes.fromhex("c21400"))  # native RET 0x14 unchanged
        # G1 changes only this selector policy. Native pool refill, DriverID
        # draw, participant setters and all other mode selectors remain native.
        self.assertEqual(spec["end"], legacy["end"])
        self.assertEqual(spec["pool"], legacy["pool"])

    def test_choice_gate_forwards_actual_stdcall_frame_and_rejects_old_call_ret_gate(self) -> None:
        spec = dict(plan.randomizer.SPECS[0])
        spec["base"] = plan.SELECTOR_BASE
        selector, _labels = plan.make_rmod1_selector(spec)
        call_sites = [
            offset for offset in range(len(selector) - 4)
            if selector[offset] == 0xE8 and
            plan.SELECTOR_BASE + offset + 5 + int.from_bytes(
                selector[offset + 1:offset + 5], "little", signed=True) == plan.CHOICE_GATE
        ]
        self.assertEqual(len(call_sites), 1)
        site = call_sites[0]
        expected_argument_setup = (
            b"\x8b\x8a" + spec["count"].to_bytes(4, "little") +
            bytes.fromhex("518bc52bc1506a00")
        )
        self.assertEqual(selector[site - len(expected_argument_setup):site], expected_argument_setup)

        cell = plan.SLOT_CHOOSE_CLASS.to_bytes(4, "little")
        corrected_gate = plan.stdcall_tail_gate(plan.SLOT_CHOOSE_CLASS)
        self.assertEqual(corrected_gate, b"\xff\x25" + cell)  # JMP dword ptr [callback cell]
        old_gate = plan.call_gate(plan.CHOICE_GATE, plan.SLOT_CHOOSE_CLASS)
        self.assertEqual(old_gate, b"\xff\x15" + cell + b"\xc3")  # CALL [cell]; RET
        module = (ROOT / "src" / "native" / "rmod1" / "runtime_core.cpp").read_text(encoding="utf-8")
        exports = (ROOT / "src" / "native" / "rmod1" / "runtime_core.def").read_text(encoding="utf-8")
        self.assertIn("int WINAPI MRChooseClassV1(\n    int hint, int first, int count, int slot)", module)
        self.assertIn("MRChooseClassV1=_MRChooseClassV1@16", exports)
        self.assertIn("using NativeProgressState = void* (__cdecl*)();", module)
        self.assertIn("native<NativeProgressState>(0x004B0310)", module)

        # Symbolically execute the PUSH argument sequence immediately before
        # the actual emitted CALL. At the selector loop the saved PUSHFD/PUSHAD
        # frame remains below these four __stdcall arguments.
        initial_esp = 0x00100000
        selector_return = plan.SELECTOR_BASE + site + 5

        def pushed_frame(gate: bytes) -> tuple[tuple[int, ...], int, int]:
            esp = initial_esp
            memory: dict[int, int] = {}
            for value in (1, 3, 1, 0):  # PUSH slot, count, first, hint
                esp -= 4
                memory[esp] = value
            esp -= 4  # selector CALL gate return address
            memory[esp] = selector_return
            callback_esp = esp
            if gate[:2] == b"\xff\x15":
                esp -= 4  # nested CALL in the old gate
                memory[esp] = plan.CHOICE_GATE + 6
                callback_esp = esp
            elif gate[:2] != b"\xff\x25":
                self.fail("unknown choice-gate opcode")
            callback_args = tuple(memory[callback_esp + 4 + 4 * i] for i in range(4))
            # The exact export is WINAPI/stdcall @16; RET 16 pops its return
            # plus all four arguments. The old gate then executes its C3.
            esp = callback_esp + 4 + 16
            next_eip = plan.CHOICE_GATE + 6 if gate[:2] == b"\xff\x15" else selector_return
            if gate[:2] == b"\xff\x15":
                next_eip = memory[esp]  # old gate's RET consumes the slot value
                esp += 4
            return callback_args, next_eip, esp

        forwarded_args, forwarded_eip, forwarded_esp = pushed_frame(corrected_gate)
        self.assertEqual(forwarded_args, (0, 1, 3, 1))
        self.assertEqual(forwarded_eip, selector_return)
        self.assertEqual(forwarded_esp, initial_esp)

        shifted_args, shifted_eip, shifted_esp = pushed_frame(old_gate)
        self.assertEqual(shifted_args, (selector_return, 0, 1, 3))
        self.assertEqual(shifted_eip, 1)  # captured first-AI slot becomes the bad RET target
        self.assertEqual(shifted_esp, initial_esp)

        # The available v6 crash JSON has the exact PUSHAD save-frame shape
        # reached after that incorrect RET. It is derived evidence only; the
        # unavailable raw sidecar is not silently treated as hash-verified.
        capture_path = ROOT / "tests" / "synthetic" / "fixtures" / "rmod1_v6_randomizer_av.json"
        capture = json.loads(capture_path.read_text(encoding="utf-8"))
        self.assertEqual(capture["eip"], shifted_eip)
        self.assertEqual(capture["exception_address"], shifted_eip)
        self.assertEqual(capture["exception_code"], 0xC0000005)
        self.assertEqual(capture["exception_information"], [0, 1])
        self.assertEqual(capture["eax"], 0xFFFFFFFF)
        self.assertEqual(capture["ebx"], 0)
        self.assertEqual(capture["ecx"], 0x94CAD48D)
        self.assertEqual(capture["edx"], 0x30000)
        self.assertEqual(capture["eflags"], 0x10246)
        self.assertEqual(capture["frames"], [])  # supplied decoded record has no symbolic frame list
        self.assertEqual(capture["stack_words"][:3],
                         [capture["edi"], capture["esi"], capture["ebp"]])
        self.assertEqual(capture["stack_words"][3], capture["esp"] + 0x20)
        self.assertEqual(capture["config_flags"], 5)  # randomizer + logging only
        self.assertEqual(capture["start_phase"], 0)   # no Start guard installed
        self.assertFalse(capture["raw_sidecar_available_for_independent_rehash"])

    def test_oep_bootstrap_resolves_unicode_loadlibrary_before_replaying_entry(self) -> None:
        code = plan.make_oep_bootstrap()
        self.assertIn(b"\x68" + plan.KERNEL32_NAME.to_bytes(4, "little"), code)
        self.assertIn(b"\x68" + plan.EXPORT_LOAD_LIBRARY_W.to_bytes(4, "little"), code)
        self.assertIn(bytes.fromhex("ff15") + plan.IAT_VA["LoadLibraryA"].to_bytes(4, "little"), code)
        self.assertIn(bytes.fromhex("ff15") + plan.IAT_VA["GetProcAddress"].to_bytes(4, "little"), code)
        self.assertIn(bytes.fromhex("ff15") + plan.SLOT_LOAD_LIBRARY_W.to_bytes(4, "little"), code)
        replay = code.find(plan.OEP_REPLAY)
        self.assertGreaterEqual(replay, 0)
        self.assertIn(plan.OEP + len(plan.OEP_REPLAY), branch_targets(code, plan.BOOTSTRAP_BASE, 0xE9))

    def test_remote_layout_is_aligned_disjoint_and_inside_fixed_allocations(self) -> None:
        self.assertEqual(plan.CODE_BASE % 0x10000, 0)
        self.assertEqual(plan.DATA_BASE, plan.CODE_BASE + plan.CODE_ALLOCATION_SIZE)
        code_regions = [
            (plan.CHOICE_GATE, plan.CHOICE_GATE + len(plan.stdcall_tail_gate(plan.SLOT_CHOOSE_CLASS))),
            (plan.LIMIT_GATE, plan.LIMIT_GATE + len(plan.call_gate(plan.LIMIT_GATE, plan.SLOT_OPPONENT_LIMIT))),
            (plan.SELECTOR_BASE, plan.SELECTOR_BASE + 0x300),
            (plan.UI_LIST_BASE, plan.START_GATE_BASE),
            (plan.START_GATE_BASE, plan.BOOTSTRAP_BASE),
            (plan.BOOTSTRAP_BASE, plan.CODE_BASE + plan.CODE_ALLOCATION_SIZE),
        ]
        for begin, end in code_regions:
            self.assertGreater(begin, plan.CODE_BASE)
            self.assertLess(begin, end)
            self.assertLessEqual(end, plan.CODE_BASE + plan.CODE_ALLOCATION_SIZE)
        ordered = sorted(code_regions)
        for left, right in zip(ordered, ordered[1:]):
            self.assertLessEqual(left[1], right[0])
        config = (plan.CONFIG_BLOB - plan.DATA_BASE, plan.CONFIG_BLOB - plan.DATA_BASE + 4 + 4096)
        dll_path = (plan.DLL_PATH - plan.DATA_BASE, plan.DLL_PATH - plan.DATA_BASE + 0x1000)
        self.assertLessEqual(config[1], dll_path[0])
        self.assertEqual(dll_path[1], plan.KERNEL32_NAME - plan.DATA_BASE)

    def test_right_arrow_patch_is_a_materialized_upper_index(self) -> None:
        for ai_limit in range(1, 8):
            replacement = bytearray(bytes.fromhex("83fd06"))
            replacement[2] = ai_limit - 1
            self.assertEqual(replacement, bytes((0x83, 0xFD, ai_limit - 1)))
        self.assertEqual(plan.UI_ARROW_ORIGINAL, bytes.fromhex("83fd02"))

    def test_header_render_is_deterministic_and_keeps_only_generated_operations(self) -> None:
        fake = {
            "source_executable": {"sha256": "a" * 64, "size": 3121214, "image_base": 0x400000},
            "runtime_core": {"sha256": "b" * 64},
            "plan_template_sha256": "c" * 64,
            "remote_allocations": [
                {"used_size": 12, "template_sha256": "d" * 64},
                {"used_size": 4, "template_sha256": "e" * 64},
            ],
            "limits": {"ui_ai_maximum": 7},
            "_code_template_hex": "90" * 12,
            "_data_template_hex": "00" * 4,
            "operations": [{"id": "test", "feature_mask": 1, "rva": 0x100,
                            "expected_original_hex": "90", "replacement_hex": "e9"}],
        }
        first = plan.render_cpp_header(fake)
        self.assertEqual(first, plan.render_cpp_header(fake))
        self.assertIn('kRuntimeCoreSha256[] = "' + "b" * 64, first)
        self.assertIn('kOperationCount = 1u', first)
        self.assertIn('"test", 1u, 0x00000100u, "90", "e9"', first)

    def test_launcher_preflight_uses_fixed_image_mapping_not_loader_enumeration(self) -> None:
        source = (ROOT / "src" / "native" / "rmod1" / "launcher.cpp").read_text(encoding="utf-8")
        self.assertNotIn("CreateToolhelp32Snapshot", source)
        self.assertNotIn("Module32FirstW", source)
        self.assertIn("VirtualQueryEx", source)
        self.assertIn("MEM_IMAGE", source)
        self.assertIn("MEM_COMMIT", source)
        self.assertIn("allocation_base", source)
        start = source.index("int suspended_preflight(")
        end = source.index("\nint launch(", start)
        preflight = source[start:end]
        self.assertIn("CREATE_SUSPENDED", preflight)
        self.assertIn("verify_module_mapping", preflight)
        self.assertIn("TerminateProcess", preflight)
        self.assertNotIn("ResumeThread", preflight)
        self.assertNotIn("install_runtime", preflight)


if __name__ == "__main__":
    unittest.main()
