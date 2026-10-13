"""Focused corpus-independent integration/provenance checks for reflection PORT1."""
import configparser
import importlib.util
import json
import os
from pathlib import Path
import unittest

PORT = Path(__file__).resolve().parents[1]
RENDERER = Path(os.environ.get("MRR_PC_PORT_RENDERER_ROOT",
    PORT / ".staging" / "ps2-enabled" / "modernization" / "renderer"))


class ReflectionContractTests(unittest.TestCase):
    def test_all_pilot_defaults_are_stock(self):
        ini = configparser.ConfigParser()
        ini.read(PORT / "PS2Port.ini.example")
        for key in ("FoliageMode", "PixelProbe", "ReflectionMode", "ReflectionDiagnostics"):
            self.assertEqual(ini.getint("PS2Port", key), 0)

    def test_source_witness_is_a_single_original_vehicle_material(self):
        evidence = json.loads((PORT / "docs/reflection-port1/material-source-contract.json").read_text())
        self.assertEqual(evidence["ps2_material"]["contract"]["mode"], 3)
        self.assertEqual(evidence["ps2_material"]["source_triangles"], 57)
        self.assertEqual(evidence["pc_material"]["source_triangles"], 55)
        self.assertEqual(evidence["pc_material"]["texture_slots"], ["tatabon-tga", "whitepaint-tga", "Null"])
        self.assertEqual(evidence["pc_material"]["signature_unique_in_car_dx"], [19])
        header = (PORT / "renderer/reflection_pilot.hpp").read_text()
        self.assertIn(evidence["pc_material"]["geometry_sha256"], header)
        self.assertIn(evidence["env_source"]["provenance"]["payload_sha256"], header)

    def test_one_native_draw_and_restoration_wrap_existing_reflection_scope(self):
        source = (RENDERER / "src/visual_wrappers.cpp").read_text()
        start = source.index("HRESULT Device8::draw_indexed_at(")
        end = source.index("HRESULT Device8::repair_reflection()", start)
        body = source[start:end]
        self.assertEqual(body.count("real_->DrawIndexedPrimitive("), 1)
        self.assertLess(body.index("ReflectionScope reflection"), body.index("ps2integration::Scope ps2_reflection"))
        self.assertLess(body.index("ps2integration::Scope ps2_reflection"), body.index("real_->DrawIndexedPrimitive("))
        self.assertIn("ps2_reflection.draw_result(hr)", body)
        self.assertIn("return hr;", body)
        self.assertIn("ps2integration::repair(*this)", source[end:])

    def test_mixed_capture_is_separate_and_only_requested_in_mode4(self):
        source = (PORT / "renderer/reflection_pilot.cpp").read_text()
        self.assertNotIn("CopyRects(", source)
        self.assertNotIn("SetRenderTarget(", source)
        self.assertNotIn("DrawPrimitive", source)
        integration = (PORT / "renderer/reflection_native_integration.hpp").read_text()
        self.assertIn("PS2_STATIC_TERM_80_OVER_128", integration)
        self.assertIn('identity_.accepted && pilot_->needs_mixed_source()', integration)
        self.assertIn('capture.ready_texture(device_.trace.frame_number())', integration)
        capture = (PORT / 'renderer/reflection_capture.cpp').read_text()
        self.assertEqual(capture.count('native.CopyRects('), 1)
        self.assertEqual(capture.count('native.DrawPrimitiveUP('), 2)
        self.assertNotIn('DrawIndexedPrimitive(', capture)
        self.assertNotIn('.after(71', capture)
        self.assertNotIn('.after(72', capture)
        self.assertIn('same_surface(current.value,back.value)', capture)
        self.assertIn('multisample_copy_unsupported', capture)
        self.assertIn('attempted_frame_==frame', capture)
        self.assertIn('transaction_.restore(native)', capture)

    def test_original_foliage_identity_and_producer_remain_available(self):
        header = (PORT / "renderer/ps2_port_extension.hpp").read_text()
        source = (PORT / "renderer/ps2_port_extension.cpp").read_text()
        self.assertIn("2b60b1f044601052bb5eaeca074615abe3947fdc1b0769c17d300a0b3b3e6f7d", source)
        self.assertIn("kPixelProbeMaxSamples = 4", header)
        self.assertIn("pixel_probe_before_reset()", source)

    def test_owned_reflection_resources_release_before_final_native_device_release(self):
        source = (RENDERER / "src/wrappers.cpp").read_text()
        start = source.index("ULONG STDMETHODCALLTYPE Device8::Release()")
        end = source.index("HRESULT STDMETHODCALLTYPE Device8::GetDirect3D", start)
        release = source[start:end]
        self.assertLess(release.index("reflection()->shutdown()"), release.index("n=real_->Release()"))

    def test_independent_synthetic_geometry_signature(self):
        script = PORT / "tools/prepare_reflection_pilot.py"
        spec = importlib.util.spec_from_file_location("reflection_prepare", script)
        prepare = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(prepare)
        face = ((0.,0.,0.), (1.,0.,0.), (0.,1.,0.))
        self.assertEqual(prepare.geometry_signature([face]), prepare.geometry_signature([tuple(reversed(face))]))
        self.assertNotEqual(prepare.geometry_signature([face]), prepare.geometry_signature([face,face]))
        self.assertNotEqual(prepare.geometry_signature([face]), prepare.TATA_DX_SHA)


if __name__ == "__main__":
    unittest.main()
