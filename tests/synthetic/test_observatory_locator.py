import struct
import unittest

import observatory_locator as locator

BASE = 0x00400000
TEXT, RDATA, DATA = 0x1000, 0x20000, 0x30000
SIZE = 0x40000
SECTIONS = [
    {"name": ".text", "rva": TEXT, "virtual_size": 0x1F000, "raw_size": 0x1F000, "raw_offset": TEXT,
     "characteristics": 0x60000020},
    {"name": ".rdata", "rva": RDATA, "virtual_size": 0x10000, "raw_size": 0x10000, "raw_offset": RDATA,
     "characteristics": 0x40000040},
    {"name": ".data", "rva": DATA, "virtual_size": 0x10000, "raw_size": 0x8000, "raw_offset": DATA,
     "characteristics": 0xC0000040},
]


def fill(sig, **dwords):
    """Signature bytes with ?? replaced; dwords maps offset -> u32."""
    raw = bytearray(sig[0])
    for offset, value in dwords.items():
        struct.pack_into("<I", raw, int(offset[1:], 16), value & 0xFFFFFFFF)
    return bytes(raw)


def call(at, target):
    return b"\xE8" + struct.pack("<i", target - (at + 5))


def build(shift=0, *, dump_case=True, slot=0x10, walker=None):
    """A synthetic module whose layout matches every locator signature."""
    img = bytearray(SIZE)
    t = TEXT + shift
    sink, manager = DATA + 0x100 + shift, DATA + 0x200 + shift
    vtable = RDATA + 0x40 + shift

    def put(rva, data):
        img[rva:rva + len(data)] = data

    logger = t + 0x100
    put(logger, fill(locator.SIG_LOGGER, o5=BASE + sink, o0C=BASE + sink + 8))
    put(logger + 0x51, fill(locator.SIG_LOGGER_APPEND, o3=BASE + RDATA))
    ctor = t + 0x300
    put(ctor, fill(locator.SIG_SINK_CTOR, oA=BASE + RDATA, o10=BASE + vtable, o17=BASE + vtable - 4))
    put(ctor + 0x5F, fill(locator.SIG_SINK_CTOR_BUFFER))
    struct.pack_into("<II", img, vtable, BASE + t + 0x3000, BASE + t + 0x3100)

    route, table, case = t + 0x500, t + 0x600, t + 0x700
    accessor, walker_rva = t + 0x800, t + 0x1000
    put(route, fill(locator.SIG_BROKER_ROUTE, o1E=BASE + table))
    struct.pack_into("<III", img, table, BASE + t + 0x780, BASE + t + 0x790, BASE + case)
    if dump_case:
        put(case, call(case, accessor) + bytes.fromhex("50 8D 8C 24 80 00 00 00") + call(case + 0x0D, walker_rva))
    put(accessor, fill(locator.SIG_ACCESSOR, o1=BASE + manager))
    put(walker_rva, walker if walker is not None else bytes(range(256)) * 6)

    switch, bytetab, jumptab = t + 0x2000, t + 0x2100, t + 0x2200
    put(switch, fill(locator.SIG_MAIN_SWITCH, oD=BASE + bytetab, o14=BASE + jumptab))
    img[bytetab + 0x27], img[bytetab + 0x30] = 1, 2
    broker_case, flow_case = t + 0x2300, t + 0x2400
    opener, flow = t + 0x2500, t + 0x2600
    struct.pack_into("<III", img, jumptab, BASE + t + 0x2700, BASE + broker_case, BASE + flow_case)
    for case_rva, member, target in ((broker_case, slot, opener), (flow_case, 0x08, flow)):
        body = (call(case_rva, t + 0x2800) + b"\x8B\x70\x38" + call(case_rva + 8, t + 0x2800)
                + bytes([0x8B, 0x40, member, 0x56, 0x8B, 0xC8]) + call(case_rva + 0x13, target))
        put(case_rva, body)
    put(opener, fill(locator.SIG_BROKER_OPENER, o11=0))
    return locator.MappedImage(BASE, SIZE, SECTIONS, bytes(img), "disk"), {
        "debug_sink_global": sink, "debug_sink_vtable": vtable, "broker_editor_dump_route": route,
        "broker_singleton_accessor": accessor, "broker_manager_global": manager,
        "native_dump_walker": walker_rva, "broker_editor_opener": opener, "flow_builder_opener": flow,
    }


class LocatorTests(unittest.TestCase):
    def test_locates_every_item_and_follows_shifted_code(self):
        for shift in (0, 0x1230):
            image, expected = build(shift)
            layout = locator.locate(image)
            self.assertEqual(layout.problems, {})
            for name, rva in expected.items():
                self.assertEqual(layout.rva(name), rva, name)
            caps = layout.capabilities()
            self.assertTrue(caps["broker_read"] and caps["native_dump"])
            self.assertTrue(caps["open_broker_editor"] and caps["flow_builder"])

    def test_missing_dump_case_disables_only_dump(self):
        image, _ = build(dump_case=False)
        layout = locator.locate(image)
        caps = layout.capabilities()
        self.assertTrue(caps["broker_read"])
        self.assertFalse(caps["native_dump"])
        self.assertFalse(caps["open_broker_editor"])
        self.assertIn("broker_editor_dump_route", layout.problems)

    def test_command_0x27_to_another_member_is_not_the_broker_opener(self):
        image, _ = build(slot=0x14)
        layout = locator.locate(image)
        self.assertIsNone(layout.rva("broker_editor_opener"))
        self.assertIn("different application member", layout.problems["broker_editor_opener"])
        self.assertFalse(layout.capabilities()["open_broker_editor"])

    def test_ambiguous_signature_is_rejected(self):
        image, expected = build()
        data = bytearray(image.data)
        copy = TEXT + 0x9000
        data[copy:copy + 0x50] = data[TEXT + 0x100:TEXT + 0x150]
        layout = locator.locate(locator.MappedImage(BASE, SIZE, SECTIONS, bytes(data), "disk"))
        self.assertIn("ambiguous", layout.problems["debug_logger"])
        self.assertFalse(layout.capabilities()["broker_read"])

    def test_unknown_walker_requires_confirmation_not_refusal(self):
        image, _ = build()
        layout = locator.locate(image)
        locator.classify_walker(image, layout)
        caps = layout.capabilities()
        self.assertEqual(caps["native_dump_walker_variant"], "unknown")
        self.assertTrue(caps["native_dump"])
        self.assertTrue(caps["native_dump_requires_confirmation"])
        self.assertIsNone(caps["post_results_native_dump_safe"])

    def test_exact_classifier_recognizes_hardened_variant(self):
        image, _ = build()
        layout = locator.locate(image)
        locator.classify_walker(image, layout, lambda img, rva: {
            "variant": "native-hardened-test", "post_results_safe": True, "hardened": True})
        caps = layout.capabilities()
        self.assertEqual(caps["broker_dump_variant"], "native_hardened")
        self.assertTrue(caps["post_results_native_dump_safe"])
        self.assertFalse(caps["native_dump_requires_confirmation"])

    def test_relocation_mask_compares_moved_code(self):
        ref = bytes.fromhex("A1 10 94 6F 00 E8 00 01 00 00 85 C0")
        moved = bytes.fromhex("A1 F8 83 6F 00 E8 F0 FE FF FF 85 C0")
        mask = locator.relocation_mask(ref, 0x400000, 0x311000)
        self.assertTrue(locator.equal_modulo_relocation(moved, ref, mask))
        self.assertFalse(locator.equal_modulo_relocation(moved[:-1] + b"\xC1", ref, mask))

    def test_reader_image_matches_disk_image(self):
        image, _ = build()
        live = locator.MappedImage.from_reader(lambda rva, n: image.data[rva:rva + n],
                                               {"size_of_image": SIZE, "sections": SECTIONS},
                                               module_base=BASE)
        self.assertEqual(locator.locate(live).items, locator.locate(image).items)

    def test_fingerprints_cover_located_code(self):
        image, _ = build()
        layout = locator.locate(image)
        names = {row["name"] for row in locator.fingerprints(image, layout)}
        self.assertTrue({"debug_logger", "debug_sink_vtable", "native_dump_walker",
                         "broker_editor_opener"} <= names)


if __name__ == "__main__":
    unittest.main()


class LiveLocatedVerificationTests(unittest.TestCase):
    def setUp(self):
        import broker_observatory as core
        from observatory_build_profiles import ObservatoryBuildProfile
        self.core = core
        self.image, _ = build()
        layout = locator.locate(self.image)
        self.profile = ObservatoryBuildProfile(
            "local-located-test", "test", "0" * 64, SIZE, layout.rva("debug_sink_global"),
            layout.rva("debug_sink_vtable"), "LOCATED_BY_SIGNATURE", ("broker-editor",),
            profile_origin="locally_located", capabilities=layout.capabilities(),
            located_layout=dict(layout.items))
        self.pe = {"image_base": BASE, "size_of_image": SIZE, "sections": SECTIONS}
        self.saved_read = core._read_remote
        self.saved_policy = dict(core.NATIVE_DUMP_POLICY)

    def tearDown(self):
        self.core._read_remote = self.saved_read
        self.core.NATIVE_DUMP_POLICY.update(self.saved_policy)

    def verify(self, memory, capability):
        self.core._read_remote = lambda _k, _p, address, size, _c: memory[address - BASE:address - BASE + size]
        return self.core._verify_live_located(None, None, BASE, None, self.profile, capability, self.pe)

    def test_live_layout_matching_profile_is_verified(self):
        report = self.verify(self.image.data, "broker_read")
        self.assertEqual(report["verified_anchors"], ["debug_sink_global", "debug_sink_vtable"])
        report = self.verify(self.image.data, "open_broker_editor")
        self.assertIn("broker_editor_opener", report["verified_anchors"])

    def test_unknown_walker_needs_policy(self):
        self.core.NATIVE_DUMP_POLICY["allow_unknown_walker"] = False
        with self.assertRaises(self.core.UnknownWalkerError):
            self.verify(self.image.data, "native_dump")
        self.core.NATIVE_DUMP_POLICY["allow_unknown_walker"] = True
        report = self.verify(self.image.data, "native_dump")
        self.assertEqual(report["native_dump_verification"], "unknown_walker_confirmed")
        self.assertIsNone(report["native_dump_post_results_safe"])

    def test_code_moved_in_memory_after_resolution_fails(self):
        moved, _ = build(0x40)
        with self.assertRaisesRegex(self.core.ObservatoryError, "moved from RVA"):
            self.verify(moved.data, "broker_read")

    def test_route_patched_out_in_memory_fails_dump_only(self):
        broken, _ = build(dump_case=False)
        self.verify(broken.data, "broker_read")
        self.core.NATIVE_DUMP_POLICY["allow_unknown_walker"] = True
        with self.assertRaisesRegex(self.core.ObservatoryError, "broker_editor_dump_route not found"):
            self.verify(broken.data, "native_dump")


class UnknownWalkerConfirmationTests(unittest.TestCase):
    def setUp(self):
        import broker_observatory as core
        import mr_observe
        self.core, self.front = core, mr_observe
        self.saved = (core.verify_live_capability_report, dict(core.NATIVE_DUMP_POLICY))
        core.NATIVE_DUMP_POLICY["allow_unknown_walker"] = False

        def unknown(*_args):
            raise core.UnknownWalkerError("walker unknown")
        core.verify_live_capability_report = unknown

        class Profile:
            sha256 = "1" * 64

        class Process:
            pid, profile = 7, Profile()
        self.process = Process()

    def tearDown(self):
        self.core.verify_live_capability_report = self.saved[0]
        self.core.NATIVE_DUMP_POLICY.clear()
        self.core.NATIVE_DUMP_POLICY.update(self.saved[1])

    def test_yes_enables_policy_for_session(self):
        self.front.confirm_unknown_walker(self.process, lambda _prompt: "y")
        self.assertTrue(self.core.NATIVE_DUMP_POLICY["allow_unknown_walker"])

    def test_no_cancels_without_dispatch(self):
        with self.assertRaisesRegex(self.core.ObservatoryError, "cancelled"):
            self.front.confirm_unknown_walker(self.process, lambda _prompt: "")
        self.assertFalse(self.core.NATIVE_DUMP_POLICY["allow_unknown_walker"])

    def test_non_interactive_points_to_flag(self):
        with self.assertRaisesRegex(self.core.ObservatoryError, "--allow-unknown-walker"):
            self.front.confirm_unknown_walker(self.process, None)
