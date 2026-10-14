#pragma once
// Compiled only into the staged baseline. The extension classifies and owns its
// private texture; this native integration alone applies/restores draw state.
#include "wrappers.hpp"
#include "reflection_pilot.hpp"
#include "vehicle_partition.hpp"
#include "ps2_port_extension.hpp"
#include "buffer_provenance.hpp"
#include "camera_probe.hpp"
#include "provenance.hpp"
#include <cstring>
#include <utility>

namespace gfx2 {
namespace ps2integration {
template<class T> struct Ref {
    T* value = nullptr;
    ~Ref() { if (value) value->Release(); }
};
inline bool snapshot(Device8& device, const DrawClassification& classification,
                     D3DPRIMITIVETYPE type, UINT min_index, UINT vertices,
                     UINT start, UINT count, ps2port::DrawSnapshot& geometry,
                     ps2port::ReflectionSnapshot& out, bool partition=false) noexcept {
    auto* extension = device.ps2_port();
    if (!extension || !extension->reflection() || !extension->reflection()->active()) return false;
    if (type != D3DPT_TRIANGLELIST || !(partition ? ps2port::vehicle_partition_layout(count,vertices) :
        ps2port::reflection_layout(count,vertices,extension->reflection()->expanded()))) return false;
    geometry = {}; out = {}; out.geometry = &geometry;
    out.requested_mode=extension->reflection()->mode_value();
    geometry.supported_build = session().target;
    geometry.device_id = device.trace.device_id();
    geometry.reset_generation = extension->reset_generation();
    out.stock_coordinate_policy = device.visuals.effective.reflection_mode == "Stock";
    out.vehicle_body_verified = std::strcmp(reflection_exclusion(classification),"eligible") == 0;
    // Like baseline learned-material admission, source authority does not infer
    // wheel constellations. The extension still requires the complete exact
    // registered geometry hash, live race certificate and current native state.
    // Never allow a shared callsite or rigid transform by itself.
    D3DMATRIX native_world{};
    const auto& tracked_world=device.trace.effective_shadow.matrices[D3DTS_WORLD];
    out.source_material_context_verified = extension->reflection()->mode_value()==4 && ps2port::source_material_context(classification,
        tracked_world.known && SUCCEEDED(device.native()->GetTransform(D3DTS_WORLD,&native_world)) &&
        !std::memcmp(&native_world,&tracked_world.value,sizeof(native_world)));
    const uintptr_t image = reinterpret_cast<uintptr_t>(GetModuleHandleW(nullptr));
    uintptr_t manager = 0, camera = 0; uint32_t cameras = 0;
    if (image == 0x00400000 &&
        safe_copy(&manager,reinterpret_cast<const void*>(image+CAMERA_MANAGER_RVA),4) && manager &&
        safe_copy(&cameras,reinterpret_cast<const void*>(manager+16),4) && cameras == 1 &&
        safe_copy(&camera,reinterpret_cast<const void*>(manager),4) && camera) {
        const auto certificate = live_race_certificate(camera);
        out.live_race_verified = certificate.valid;
        out.race_generation = certificate.race_generation;
        out.owner_lifetime = certificate.owner_lifetime;
    }
    auto& native = *device.native();
    Ref<IDirect3DVertexBuffer8> vb; Ref<IDirect3DIndexBuffer8> ib;
    DWORD fvf = 0, pixel_shader = 0; UINT stride = 0, base = 0;
    if (FAILED(native.GetVertexShader(&fvf)) || fvf != 0x152 ||
        FAILED(native.GetPixelShader(&pixel_shader)) || pixel_shader != 0 ||
        FAILED(native.GetStreamSource(0,&vb.value,&stride)) || !vb.value || stride != 36 ||
        FAILED(native.GetIndices(&ib.value,&base)) || !ib.value) return false;
    D3DVERTEXBUFFER_DESC vd{}; D3DINDEXBUFFER_DESC id{};
    if (FAILED(vb.value->GetDesc(&vd)) || FAILED(ib.value->GetDesc(&id))) return false;
    const UINT size = id.Format == D3DFMT_INDEX16 ? 2u : id.Format == D3DFMT_INDEX32 ? 4u : 0u;
    if (!size) return false;
    const uint64_t vo = (uint64_t(base)+min_index)*stride, vs = uint64_t(vertices)*stride;
    const uint64_t io = uint64_t(start)*size, is = uint64_t(count)*3u*size;
    if (vo > vd.Size || vs > vd.Size-vo || io > id.Size || is > id.Size-io) return false;
    geometry.primitive_type=type; geometry.min_index=min_index; geometry.vertex_count=vertices;
    geometry.start_index=start; geometry.primitive_count=count; geometry.fvf=fvf; geometry.stride=stride;
    geometry.base_vertex=base; geometry.index_format=id.Format; geometry.vertex_byte_offset=vo;
    geometry.vertex_resource=reinterpret_cast<uintptr_t>(vb.value);
    geometry.index_resource=reinterpret_cast<uintptr_t>(ib.value);
    geometry.vertex_generation=device.trace.resources.generation(geometry.vertex_resource);
    geometry.index_generation=device.trace.resources.generation(geometry.index_resource);
    if (!geometry.vertex_generation || !geometry.index_generation ||
        !device.copy_buffer_shadow(vb.value,BufferKind::Vertex,geometry.vertex_generation,vo,
             static_cast<size_t>(vs),geometry.vertex_bytes,geometry.vertex_revision) ||
        !device.copy_buffer_shadow(ib.value,BufferKind::Index,geometry.index_generation,io,
             static_cast<size_t>(is),geometry.index_bytes,geometry.index_revision)) return false;
    geometry.complete_mirror_coverage=true;
    out.native_states_complete=true; out.native_matches_effective=true; out.textures_are_2d=true;
    for (size_t n=0; n<ps2port::kReflectionRenderStates.size(); ++n) {
        const auto key=ps2port::kReflectionRenderStates[n];
        const auto& tracked=device.trace.effective_shadow.rs[key];
        if (FAILED(native.GetRenderState(key,&out.render_states[n]))) out.native_states_complete=false;
        else if (!tracked.known || tracked.value!=out.render_states[n]) out.native_matches_effective=false;
    }
    for (DWORD stage=0; stage<2; ++stage) {
        for (size_t n=0; n<ps2port::kReflectionStageStates.size(); ++n) {
            const auto key=ps2port::kReflectionStageStates[n];
            const auto& tracked=device.trace.effective_shadow.tss[stage][key];
            if (FAILED(native.GetTextureStageState(stage,key,&out.stages[stage][n]))) out.native_states_complete=false;
            else if (!tracked.known || tracked.value!=out.stages[stage][n]) out.native_matches_effective=false;
        }
        Ref<IDirect3DBaseTexture8> texture;
        if (FAILED(native.GetTexture(stage,&texture.value)) || !texture.value) { out.textures_are_2d=false; continue; }
        out.textures[stage]=reinterpret_cast<uintptr_t>(texture.value);
        out.texture_generations[stage]=device.trace.resources.generation(out.textures[stage]);
        const auto& tracked=device.trace.effective_shadow.bindings.textures[stage];
        if (!tracked.known || tracked.value!=out.textures[stage]) out.native_matches_effective=false;
        if (texture.value->GetType()!=D3DRTYPE_TEXTURE) out.textures_are_2d=false;
    }
    D3DMATRIX matrix{};
    const auto& tracked=device.trace.effective_shadow.matrices[D3DTS_TEXTURE1];
    out.texture_matrix_known=tracked.known && SUCCEEDED(native.GetTransform(D3DTS_TEXTURE1,&matrix)) &&
        std::memcmp(&tracked.value,&matrix,sizeof(matrix))==0;
    return true;
}

inline HRESULT color_write(Device8& device, DWORD value, uintptr_t pc) noexcept {
    const Args args=pack(1,D3DTSS_COLOROP,value);
    const HRESULT hr=device.native()->SetTextureStageState(1,D3DTSS_COLOROP,value);
    device.trace.after(63,args,static_cast<uint32_t>(hr),pc,&args,8,false,true);
    return hr;
}
inline HRESULT texture_write(Device8& device, IDirect3DBaseTexture8* value, uintptr_t pc) noexcept {
    const Args args=pack(1,value);
    const HRESULT hr=device.native()->SetTexture(1,value);
    device.trace.after(61,args,static_cast<uint32_t>(hr),pc,&args,8,false,true);
    return hr;
}
inline bool pending(Device8& device) noexcept {
    auto* extension=device.ps2_port();
    auto* p=extension?extension->reflection():nullptr;
    return p && (p->blocked() || p->mixed_capture().pending() || p->transaction().changed_mask);
}
inline HRESULT repair(Device8& device) noexcept {
    auto* extension=device.ps2_port();
    if (!extension || !extension->reflection()) return S_OK;
    auto& pilot=*extension->reflection();
    if (pilot.blocked()) return D3DERR_DEVICELOST; // No native draw in an unrecovered device.
    auto& capture=pilot.mixed_capture();
    capture.set_writer(&device,[](void* owner,uint32_t slot,const Args& args,HRESULT hr) noexcept {
        auto& d=*static_cast<Device8*>(owner);
        d.trace.after(slot,args,static_cast<uint32_t>(hr),0,&args,256,false,true);
    });
    if (capture.pending()) {
        const HRESULT hr=capture.repair(*device.native());
        if (FAILED(hr)) return hr;
    }
    auto& t=pilot.transaction();
    if (!t.changed_mask) return S_OK;
    return ps2port::restore_reflection_transaction(t,
        [&](DWORD v) noexcept { return color_write(device,v,0); },
        [&](IDirect3DBaseTexture8* v) noexcept { return texture_write(device,v,0); });
}

class Scope {
    Device8& device_;
    ps2port::ReflectionPilot* pilot_=nullptr;
    ps2port::ReflectionIdentity identity_{};
    uintptr_t pc_=0, original_texture_=0;
    uint64_t texture_generation_=0;
    DWORD original_color_op_=0;
    bool original_color_op_known_=false;
    const ps2port::DrawSnapshot* geometry_=nullptr;
    uintptr_t temporary_texture_=0;
    HRESULT apply_hr_=E_PENDING, draw_hr_=E_PENDING, restore_hr_=E_PENDING;
    bool applied_=false;
    uint32_t requested_mask_=0, applied_mask_=0;
    HRESULT capture_hr_=E_PENDING;
public:
    Scope(Device8& device, const ps2port::ReflectionSnapshot& snapshot,
          ps2port::ReflectionIdentity identity, uintptr_t pc) noexcept
        : device_(device), identity_(std::move(identity)), pc_(pc) {
        auto* extension=device.ps2_port();
        if (!extension || !extension->reflection()) return;
        pilot_=extension->reflection();
        original_texture_=snapshot.textures[1]; texture_generation_=snapshot.texture_generations[1];
        original_color_op_=snapshot.stages[1][0];
        original_color_op_known_=snapshot.native_states_complete;
        geometry_=snapshot.geometry;
        IDirect3DTexture8* mixed=nullptr;
        if (identity_.accepted && pilot_->needs_mixed_source()) {
            auto& capture=pilot_->mixed_capture();
            capture.set_writer(&device_,[](void* owner,uint32_t slot,const Args& args,HRESULT hr) noexcept {
                auto& d=*static_cast<Device8*>(owner);
                d.trace.after(slot,args,static_cast<uint32_t>(hr),0,&args,256,false,true);
            });
            if (device_.trace.scene_active && GetCurrentThreadId()==device_.trace.render_thread_id()) {
                capture_hr_=capture.capture(*device_.native(),pilot_->static_texture(),device_.trace.frame_number(),
                    device_.trace.shadow.recording || device_.trace.effective_shadow.recording);
                mixed=capture.ready_texture(device_.trace.frame_number());
                if (capture.pending()) {
                    restore_hr_=repair(device_);
                    if (FAILED(restore_hr_)) pilot_->disable("mixed_capture_restore_failed");
                }
            }
        }
        const auto request=pilot_->request(identity_,mixed);
        requested_mask_=request.override_mask;
        if (!request.requested) return;
        temporary_texture_=reinterpret_cast<uintptr_t>(request.texture);
        apply_hr_=ps2port::apply_reflection_transaction(request,pilot_->transaction(),
            [&](DWORD& value) noexcept {
                const HRESULT hr=device_.native()->GetTextureStageState(1,D3DTSS_COLOROP,&value);
                const auto& expected=device_.trace.effective_shadow.tss[1][D3DTSS_COLOROP];
                return SUCCEEDED(hr) && expected.known && value==expected.value ? S_OK : FAILED(hr) ? hr : E_FAIL;
            },
            [&](IDirect3DBaseTexture8*& value) noexcept {
                const HRESULT hr=device_.native()->GetTexture(1,&value);
                if (FAILED(hr)) return hr;
                if (reinterpret_cast<uintptr_t>(value)!=original_texture_) {
                    if (value) value->Release(); value=nullptr; return E_FAIL;
                }
                return S_OK;
            },
            [&](DWORD v) noexcept { return color_write(device_,v,pc_); },
            [&](IDirect3DBaseTexture8* v) noexcept { return texture_write(device_,v,pc_); }, applied_);
        if (applied_) applied_mask_=request.override_mask;
        if (FAILED(apply_hr_) && pilot_->transaction().changed_mask) {
            restore_hr_=repair(device_);
            if (FAILED(restore_hr_)) pilot_->disable("partial_apply_restore_failed");
        }
    }
    HRESULT pre_draw_status() const noexcept { return FAILED(restore_hr_) && restore_hr_!=E_PENDING ? restore_hr_ : S_OK; }
    bool applied() const noexcept { return applied_; }
    void draw_result(HRESULT hr) noexcept { draw_hr_=hr; }
    ~Scope() noexcept {
        if (!pilot_) return;
        if (pilot_->transaction().changed_mask) {
            restore_hr_=repair(device_);
            if (FAILED(restore_hr_)) {
                pilot_->disable("native_reflection_restore_failed");
                try { session().write("{\"type\":\"ps2_reflection_restore_failure\",\"device\":"+
                    std::to_string(device_.trace.device_id())+",\"hresult\":"+std::to_string(static_cast<uint32_t>(restore_hr_))+"}"); } catch (...) {}
            }
        } else if (applied_) restore_hr_=S_OK;
        if (!std::strcmp(identity_.vehicle,"UNKNOWN") ||
            !geometry_ || !pilot_->claim_diagnostic(applied_,identity_.vehicle)) return;
        try {
            session().write("{\"type\":\"ps2_reflection_material\",\"device\":"+std::to_string(device_.trace.device_id())+
                ",\"frame\":"+std::to_string(device_.trace.frame_number())+",\"mode\":"+std::to_string(pilot_->mode_value())+
                ",\"source\":"+quote(pilot_->needs_mixed_source()?"PS2_STATIC_PLUS_PC_FRAMEBUFFER_APPROXIMATION":
                    pilot_->mode_value()==3?"NATIVE_PC_ENVIRONMENT_IMAGE":"PS2_STATIC_TERM_80_OVER_128")+
                ",\"vehicle\":"+quote(identity_.vehicle)+",\"source_group\":"+
                quote(identity_.geometry_sha256==ps2port::kTataBonnetGeometrySha?"TATA_RECORD_19_HOOD_AND_ROOF":
                    identity_.geometry_sha256==ps2port::kKiaBonnetGeometrySha?"KIA_RECORD_14_PAINTED_GROUP":"VERIFIED_CARSHINY_SOURCE_GROUP")+
                ",\"requested_mask\":"+std::to_string(requested_mask_)+
                ",\"applied_mask\":"+std::to_string(applied_mask_)+
                ",\"capture_hresult\":"+std::to_string(static_cast<uint32_t>(capture_hr_))+
                ",\"capture_reason\":"+quote(pilot_->mixed_capture().last_status().reason)+
                ",\"copy_hresult\":"+std::to_string(static_cast<uint32_t>(pilot_->mixed_capture().last_status().copy_hr))+
                ",\"capture_restore_hresult\":"+std::to_string(static_cast<uint32_t>(pilot_->mixed_capture().last_status().restore_hr))+
                ",\"capture_source_format\":"+std::to_string(static_cast<uint32_t>(pilot_->mixed_capture().last_status().source_format))+
                ",\"capture_target_format\":"+std::to_string(static_cast<uint32_t>(pilot_->mixed_capture().last_status().target_format))+
                ",\"precision_fallback\":"+(pilot_->mixed_capture().last_status().precision_fallback?"true":"false")+
                ",\"capture_source_multisample\":"+std::to_string(static_cast<uint32_t>(pilot_->mixed_capture().last_status().source_multisample))+
                ",\"capture_width\":"+std::to_string(pilot_->mixed_capture().last_status().layout.source_width)+
                ",\"capture_height\":"+std::to_string(pilot_->mixed_capture().last_status().layout.source_height)+
                ",\"capture_copy_bytes\":"+std::to_string(pilot_->mixed_capture().last_status().layout.bytes)+
                ",\"capture_private_draws\":"+std::to_string(pilot_->mixed_capture().last_status().private_draws)+
                ",\"geometry_sha256\":"+quote(identity_.geometry_sha256)+
                ",\"identity_authority\":"+quote(identity_.source_material_authority?
                    "EXACT_SOURCE_MATERIAL_AND_CURRENT_NATIVE_CONTEXT":"LEGACY_VEHICLE_BODY_PROOF")+
                ",\"identity_reason\":"+quote(identity_.reason)+",\"override_applied\":"+(applied_?"true":"false")+
                ",\"original_stage1_texture\":"+std::to_string(original_texture_)+
                ",\"original_texture_generation\":"+std::to_string(texture_generation_)+
                ",\"temporary_stage1_texture\":"+std::to_string(temporary_texture_)+
                ",\"vertex_generation\":"+std::to_string(geometry_->vertex_generation)+
                ",\"index_generation\":"+std::to_string(geometry_->index_generation)+
                ",\"vertex_revision\":"+std::to_string(geometry_->vertex_revision)+
                ",\"index_revision\":"+std::to_string(geometry_->index_revision)+
                ",\"original_colorop\":"+(original_color_op_known_?std::to_string(original_color_op_):"null")+
                ",\"temporary_colorop\":"+((applied_mask_&1u)?"7":"null")+",\"apply_hresult\":"+
                std::to_string(static_cast<uint32_t>(apply_hr_))+",\"native_draw_hresult\":"+
                std::to_string(static_cast<uint32_t>(draw_hr_))+",\"restore_hresult\":"+
                std::to_string(static_cast<uint32_t>(restore_hr_))+"}");
        } catch (...) {}
    }
};
} // namespace ps2integration
} // namespace gfx2
