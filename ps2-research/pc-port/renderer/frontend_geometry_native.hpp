#pragma once
#include "reflection_native_integration.hpp"
#include "frontend_source_registry.hpp"
#include "xtrail_frontend_registry.hpp"
#include <algorithm>
#include <sstream>
#include <iomanip>
#include <limits>
#include <cmath>

namespace gfx2::frontendintegration {
inline bool layout(uint32_t count,uint32_t vertices) noexcept {
    for(const auto& s:ps2port::kForesterCompleteSources)if(s.triangles==count&&s.vertices==vertices)return true;
    for(const auto& s:ps2port::kXtrailCompleteSources)if(s.triangles==count&&s.vertices==vertices)return true;
    return false;
}
// Read-only source/resource diagnostic. This explicitly does not establish the
// current frontend Egg/model cache owner and never suppresses native geometry.
inline void observe(Device8& d,D3DPRIMITIVETYPE type,UINT min_index,UINT vertices,
                    UINT start,UINT count) noexcept {
    auto* e=d.ps2_port();
    if(!d.trace.enabled||!d.trace.control.active||!e || !e->frontend_geometry_diagnostics() || type!=D3DPT_TRIANGLELIST || !layout(count,vertices))return;
    if(!e->claim_frontend_probe_attempt())return; // hard lifetime cap, no steady menu rescan
    try {
        ps2port::DrawSnapshot g;
        g.supported_build=session().target;if(!g.supported_build)return;
        g.device_id=d.trace.device_id();g.reset_generation=e->reset_generation();
        ps2integration::Ref<IDirect3DVertexBuffer8> vb;ps2integration::Ref<IDirect3DIndexBuffer8> ib;
        auto& n=*d.native();DWORD fvf=0,shader=0;UINT stride=0,base=0;
        if(FAILED(n.GetVertexShader(&fvf)) || (fvf!=0x142&&fvf!=0x152&&fvf!=0x112) ||
           FAILED(n.GetPixelShader(&shader)) || shader ||
           FAILED(n.GetStreamSource(0,&vb.value,&stride)) || !vb.value || stride!=(fvf==0x152?36u:fvf==0x112?32u:24u) ||
           FAILED(n.GetIndices(&ib.value,&base)) || !ib.value)return;
        D3DVERTEXBUFFER_DESC vd{};D3DINDEXBUFFER_DESC id{};
        if(FAILED(vb.value->GetDesc(&vd)) || FAILED(ib.value->GetDesc(&id)))return;
        const uint32_t size=id.Format==D3DFMT_INDEX16?2u:id.Format==D3DFMT_INDEX32?4u:0;
        const uint64_t vo=(uint64_t(base)+min_index)*stride,vs=uint64_t(vertices)*stride;
        const uint64_t io=uint64_t(start)*size,is=uint64_t(count)*3*size;
        if(!size || vo>vd.Size || vs>vd.Size-vo || io>id.Size || is>id.Size-io)return;
        g.primitive_type=type;g.primitive_count=count;g.min_index=min_index;g.vertex_count=vertices;
        g.start_index=start;g.base_vertex=base;g.fvf=fvf;g.stride=stride;g.index_format=id.Format;g.vertex_byte_offset=vo;
        g.vertex_resource=reinterpret_cast<uintptr_t>(vb.value);g.index_resource=reinterpret_cast<uintptr_t>(ib.value);
        g.vertex_generation=d.trace.resources.generation(g.vertex_resource);g.index_generation=d.trace.resources.generation(g.index_resource);
        if(!g.vertex_generation || !g.index_generation ||
           !d.copy_buffer_shadow(vb.value,BufferKind::Vertex,g.vertex_generation,vo,static_cast<size_t>(vs),g.vertex_bytes,g.vertex_revision) ||
           !d.copy_buffer_shadow(ib.value,BufferKind::Index,g.index_generation,io,static_cast<size_t>(is),g.index_bytes,g.index_revision))return;
        g.complete_mirror_coverage=true;
        // Diagnostic-only XYZ adapter; does NOT widen body/render admission.
        auto geometry=g;
        if(fvf==0x112){geometry.fvf=0x152;geometry.stride=36;geometry.base_vertex=0;geometry.vertex_byte_offset=uint64_t(min_index)*36;geometry.vertex_bytes.assign(uint64_t(vertices)*36,0);for(unsigned i=0;i<vertices;++i)std::memcpy(geometry.vertex_bytes.data()+i*36,g.vertex_bytes.data()+i*32,12);}
        auto faces=ps2port::vehicle_face_hashes(geometry);if(faces.empty())return;
        std::sort(faces.begin(),faces.end());std::string joined;for(const auto& f:faces)joined+=f;
        const auto digest=sha256_bytes(joined.data(),joined.size());
        for(size_t i=0;i<std::size(ps2port::kForesterCompleteSources)+std::size(ps2port::kXtrailCompleteSources);++i) {
            const auto forester_count=std::size(ps2port::kForesterCompleteSources);const bool xtrail=i>=forester_count;
            const auto& source=xtrail?ps2port::kXtrailCompleteSources[i-forester_count]:ps2port::kForesterCompleteSources[i];
            if(digest!=source.hash || count!=source.triangles || vertices!=source.vertices)continue;
            if(!e->claim_frontend_geometry(i,d.trace.frame_number()))return;
            std::ostringstream matrices;matrices<<std::setprecision(std::numeric_limits<float>::max_digits10)<<'[';
            bool current=true;
            std::string matrix_hr="[";
            for(unsigned k=0;k<3;++k) {
                const auto key=k==0?D3DTS_WORLD:k==1?D3DTS_VIEW:D3DTS_PROJECTION;
                D3DMATRIX matrix{};const auto hr=n.GetTransform(key,&matrix);
                const auto& tracked=d.trace.effective_shadow.matrices[key];
                if(k)matrix_hr+=',';matrix_hr+=std::to_string(static_cast<uint32_t>(hr));
                bool finite=true;for(unsigned a=0;a<16;++a)finite=finite&&std::isfinite(matrix.m[a/4][a%4]);
                current=current&&SUCCEEDED(hr)&&tracked.known&&!std::memcmp(&matrix,&tracked.value,sizeof(matrix));
                current=current&&finite;
                if(k)matrices<<',';
                if(FAILED(hr)||!finite){matrices<<"null";continue;}
                matrices<<'[';
                for(unsigned a=0;a<16;++a){if(a)matrices<<',';matrices<<matrix.m[a/4][a%4];}matrices<<']';
            }
            matrices<<']';
            matrix_hr+=']';
            session().write("{\"type\":\"ps2_frontend_upload_identity\",\"frame\":"+
                std::to_string(d.trace.frame_number())+",\"source\":"+quote(xtrail?"Xtrail/complete.dx":"Forester/complete.dx")+",\"source_geometry_sha256\":"+
                quote(digest)+",\"source_record_metadata_index\":"+std::to_string(xtrail?i-forester_count:i)+
                ",\"vertex_generation\":"+std::to_string(g.vertex_generation)+",\"index_generation\":"+
                std::to_string(g.index_generation)+",\"vertex_revision\":"+std::to_string(g.vertex_revision)+
                ",\"index_revision\":"+std::to_string(g.index_revision)+",\"reset_generation\":"+
                std::to_string(g.reset_generation)+",\"fvf\":"+std::to_string(fvf)+",\"stride\":"+std::to_string(stride)+
                ",\"min_index\":"+std::to_string(min_index)+",\"start_index\":"+std::to_string(start)+
                ",\"vertices\":"+std::to_string(vertices)+",\"triangles\":"+std::to_string(count)+
                ",\"world_view_projection_current\":"+(current?"true":"false")+
                ",\"world_view_projection\":"+matrices.str()+
                ",\"matrix_hresults\":"+matrix_hr+
                ",\"model_owner_join_verified\":false,\"replacement_enabled\":false}");
            return;
        }
    }catch(...){}
}
} // namespace gfx2::frontendintegration
