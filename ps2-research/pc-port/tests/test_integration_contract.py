import pathlib
import os
import unittest


ROOT = pathlib.Path(__file__).resolve().parents[3]
RENDERER = pathlib.Path(os.environ.get(
    "MRR_PC_PORT_RENDERER_ROOT",
    ROOT / "ps2-research" / "pc-port" / ".staging" / "ps2-enabled" / "modernization" / "renderer",
))


class IntegrationContractTests(unittest.TestCase):
    def test_stock_build_is_opt_in_and_source_free(self):
        cmake = (RENDERER / "CMakeLists.txt").read_text(encoding="utf-8")
        self.assertIn('option(MRR_ENABLE_PS2_PORT "Build the existing proxy with the opt-in PS2 port extension" OFF)', cmake)
        self.assertIn("if(MRR_ENABLE_PS2_PORT)", cmake)
        self.assertIn("target_sources(proxy_core PRIVATE", cmake)
        self.assertIn("target_compile_definitions(proxy_core PUBLIC MRR_ENABLE_PS2_PORT=1)", cmake)

    def test_mirror_gates_are_separate_from_f10_logging(self):
        provenance = (RENDERER / "src" / "buffer_provenance.cpp").read_text(encoding="utf-8")
        self.assertIn("!owner_->buffer_mirroring_enabled()", provenance)
        forwarders = (RENDERER / "src" / "forwarders.cpp").read_text(encoding="utf-8")
        for marker in ("CreateVertexBuffer", "CreateIndexBuffer", "GetStreamSource", "GetIndices"):
            start = forwarders.index("Device8::" + marker)
            end = forwarders.find("\n}", start)
            self.assertIn("buffer_mirroring_enabled()", forwarders[start:end])
        visual = (RENDERER / "src" / "visual_wrappers.cpp").read_text(encoding="utf-8")
        self.assertIn("visuals.effective.foliage_diagnostics&&trace.enabled&&trace.control.active", visual)

    def test_indexed_draw_is_single_and_transaction_is_local(self):
        source = (RENDERER / "src" / "visual_wrappers.cpp").read_text(encoding="utf-8")
        start = source.index("HRESULT Device8::draw_indexed_at(")
        end = source.index("HRESULT Device8::repair_reflection()", start)
        draw = source[start:end]
        self.assertEqual(draw.count("real_->DrawIndexedPrimitive("), 1)
        self.assertLess(draw.index("extension->classify(snapshot)"), draw.index("real_->DrawIndexedPrimitive("))
        self.assertLess(draw.index("real_->DrawIndexedPrimitive("), draw.rindex("restore_pilot_states(*real_,trace,pilot_states,pc)"))
        self.assertIn("return hr;", draw)
        self.assertIn("valid_state_override_mask(request.override_mask)", (ROOT / "ps2-research" / "pc-port" / "renderer" / "ps2_port_extension.hpp").read_text(encoding="utf-8"))
        self.assertIn("effective.known&&SUCCEEDED(native.GetRenderState(key,&value))&&value==effective.value", source)
        for state in ("D3DRS_ALPHATESTENABLE", "D3DRS_ALPHABLENDENABLE", "D3DRS_SRCBLEND", "D3DRS_DESTBLEND", "D3DRS_ZWRITEENABLE"):
            self.assertIn(state, source)

    def test_masked_state_lifecycle_and_bounded_diagnostic(self):
        extension = (ROOT / "ps2-research" / "pc-port" / "renderer" / "ps2_port_extension.hpp").read_text(encoding="utf-8")
        visual = (RENDERER / "src" / "visual_wrappers.cpp").read_text(encoding="utf-8")
        self.assertIn("valid_state_override_mask(request.override_mask)", extension)
        self.assertIn("if ((request.override_mask & bit) == 0) continue;", extension)
        self.assertIn("transaction.changed_mask |= bit;", extension)
        self.assertIn("restore_state_transaction(transaction, write);", extension)
        self.assertIn("ps2port::restore_state_transaction(transaction,write)", visual)
        self.assertIn("extension->claim_draw_diagnostic()", visual)
        self.assertIn("requested_mask", visual)
        self.assertIn("applied_mask", visual)
        self.assertEqual(visual.count("real_->DrawIndexedPrimitive("), 1)

    def test_mode_selection_is_logged_once_at_device_setup(self):
        wrappers = (RENDERER / "src" / "wrappers.cpp").read_text(encoding="utf-8")
        self.assertIn("ps2_port_mode_selected", wrappers)
        self.assertIn("device_config", wrappers)
        self.assertIn("applied_mask", wrappers)
        self.assertIn("requested_mask", wrappers)

    def test_four_mode_masks_and_default_stock(self):
        extension = (ROOT / "ps2-research" / "pc-port" / "renderer" / "ps2_port_extension.hpp").read_text(encoding="utf-8")
        implementation = (ROOT / "ps2-research" / "pc-port" / "renderer" / "ps2_port_extension.cpp").read_text(encoding="utf-8")
        self.assertIn("Stock = 0", extension)
        self.assertIn("override_mask = kStateMaskAll", extension)
        self.assertIn("kStateSourceBlend | kStateDestinationBlend", extension)
        self.assertIn("request.override_mask = kStateZWrite", extension)
        self.assertIn('mode == 2', implementation)
        self.assertIn('mode == 3', implementation)

    def test_target_predicate_uses_live_owner_and_current_geometry_not_texture_or_ordinal(self):
        source = (RENDERER / "src" / "visual_wrappers.cpp").read_text(encoding="utf-8")
        ext = (ROOT / "ps2-research" / "pc-port" / "renderer" / "ps2_port_extension.cpp").read_text(encoding="utf-8")
        self.assertIn("live_race_certificate(camera)", source)
        self.assertIn("race_course_is_france1", source)
        self.assertIn("copy_buffer_shadow", source)
        self.assertIn("geometry_sha256", ext)
        self.assertIn("vertex_generation", ext)
        self.assertIn("index_revision", ext)
        geometry_builder = ext[ext.index("std::string geometry_sha"):ext.index("bool is_france1_bush01_geometry")]
        classifier = ext[ext.index("Classification PS2PortExtension::classify"):ext.index("void PS2PortExtension::device_reset")]
        self.assertNotIn("texture", (geometry_builder + classifier).lower())
        self.assertNotIn("draw_index", (geometry_builder + classifier).lower())

    def test_reset_echo_precedes_extension_invalidation(self):
        source = (RENDERER / "src" / "quality_wrappers.cpp").read_text(encoding="utf-8")
        echo = source.index("window_commit_active()")
        reset = source.index("ps2_port_reset_begin()")
        self.assertLess(echo, reset)

    def test_pixel_probe_is_one_frame_bounded_and_exact_target_only(self):
        visual = (RENDERER / "src" / "visual_wrappers.cpp").read_text(encoding="utf-8")
        quality = (RENDERER / "src" / "quality_wrappers.cpp").read_text(encoding="utf-8")
        extension = (ROOT / "ps2-research" / "pc-port" / "renderer" / "ps2_port_extension.cpp").read_text(encoding="utf-8")
        header = (ROOT / "ps2-research" / "pc-port" / "renderer" / "ps2_port_extension.hpp").read_text(encoding="utf-8")
        self.assertIn("pixel_probe_enabled())pilot_ordinal=pilot_extension->note_indexed_draw", visual)
        self.assertIn('std::strcmp(match.identity,"exact_france1_bush01_source_geometry_current_generations")', visual)
        self.assertIn('"before_target_draw"', visual)
        self.assertIn('"after_target_draw"', visual)
        self.assertIn('"after_later_indexed_draw"', visual)
        self.assertIn('"before_present"', quality)
        self.assertEqual(visual.count("real_->DrawIndexedPrimitive("), 1)
        self.assertIn("std::array<PixelProbeSample, kPixelProbeMaxSamples>", header)
        self.assertIn("kPixelProbeMaxSamples = 4", header)
        self.assertIn("pixel_probe_has_sample_capacity(pixel_probe_sample_count_)", extension)
        self.assertNotIn("pixel_probe_sample_count_ < pixel_probe_samples_.size()", extension)
        self.assertIn("RECT source{pixel_probe_x_, pixel_probe_y_, pixel_probe_x_ + 1, pixel_probe_y_ + 1}", extension)
        self.assertIn("RECT full{0, 0, 4, 1}", extension)
        self.assertIn("D3DRS_COLORWRITEENABLE", extension)
        self.assertIn("device.GetTextureStageState", extension)
        self.assertIn("device.GetViewport", extension)
        self.assertNotIn("GetRenderTargetData", extension)
        self.assertNotIn("depth_surface.value->LockRect", extension)
        self.assertIn("not_readable_by_copyrects_depth_stencil_format_lock_not_attempted", extension)
        self.assertIn("GetBackBuffer(0, D3DBACKBUFFER_TYPE_MONO", extension)
        self.assertIn("same_com_identity(color_surface.value, backbuffer.value", extension)
        self.assertIn("get_render_target_identity_hresult", extension)

    def test_pixel_probe_reset_is_real_reset_only_and_logs_once(self):
        wrappers = (RENDERER / "src" / "wrappers.cpp").read_text(encoding="utf-8")
        quality = (RENDERER / "src" / "quality_wrappers.cpp").read_text(encoding="utf-8")
        echo = quality.index("window_commit_active()")
        begin = quality.index("ps2_port_reset_begin()")
        native_call = quality.index("quality?quality->reset", begin)
        complete = quality.index("ps2_port_reset(native_reset_called,SUCCEEDED(hr))", native_call)
        self.assertLess(echo, begin)
        self.assertLess(begin, native_call)
        self.assertLess(native_call, complete)
        self.assertIn("if(native_reset_called&&successful)ps2_port_->device_reset(true)", wrappers)
        self.assertIn("pixel_probe_after_reset(*real_,native_reset_called,successful)", wrappers)
        extension = (ROOT / "ps2-research" / "pc-port" / "renderer" / "ps2_port_extension.cpp").read_text(encoding="utf-8")
        self.assertIn("pixel_probe_samples_ = {}", extension)
        self.assertIn("pixel_probe_copy_mask_ = 0", extension)
        self.assertIn(r'\"type\":\"ps2_pixel_probe_config\"', wrappers)
        self.assertIn(r'\"type\":\"ps2_pixel_probe\"', extension)


if __name__ == "__main__":
    unittest.main()
