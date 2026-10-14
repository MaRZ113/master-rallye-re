#pragma once
#include "reflection_native_integration.hpp"
#include "vehicle_partition.hpp"

namespace gfx2::vehicleintegration {
struct Result { bool handled=false; HRESULT hr=S_OK; };
inline Result draw(Device8& d,const DrawClassification& c,D3DPRIMITIVETYPE type,
                   UINT min_index,UINT vertices,UINT start,UINT count,uintptr_t pc) noexcept {
    auto* e=d.ps2_port();
    auto* p=e?e->vehicle_partitions():nullptr;
    auto* reflection=e?e->reflection():nullptr;
    if(!p || !p->requested() || !reflection || !reflection->active() || reflection->mode_value()!=4 ||
       !ps2port::vehicle_partition_layout(count,vertices) || !d.trace.scene_active ||
       GetCurrentThreadId()!=d.trace.render_thread_id() ||
       d.trace.shadow.recording || d.trace.effective_shadow.recording)return {};
    try {
        ps2port::DrawSnapshot g;ps2port::ReflectionSnapshot s;
        if(!ps2integration::snapshot(d,c,type,min_index,vertices,start,count,g,s,true))return {};
        const auto plan=p->classify(s,e->reset_generation());
        if(!plan.accepted)return {};
        // Allocate all identities before any native submission. No allocation
        // failure may trigger a whole-draw fallback after a subrange was drawn.
        std::vector<ps2port::ReflectionIdentity> identities(plan.runs.size());
        std::vector<HRESULT> results(plan.runs.size(),E_PENDING);
        std::vector<bool> applied(plan.runs.size(),false);
        for(auto& identity:identities) {
            identity.accepted=true;identity.source_material_authority=true;
            identity.vehicle=plan.material->vehicle;identity.geometry_sha256=plan.material->geometry_sha;
            identity.reason="verified_carshiny_subset_of_exact_current_native_geometry";
        }
        // Preflight the private source before suppressing any original submission.
        // Capture has its existing bounded once-per-frame cache and Reset ownership.
        auto& capture=reflection->mixed_capture();
        capture.set_writer(&d,[](void* owner,uint32_t slot,const Args& args,HRESULT hr) noexcept {
            auto& device=*static_cast<Device8*>(owner);
            device.trace.after(slot,args,static_cast<uint32_t>(hr),0,&args,256,false,true);
        });
        const HRESULT capture_hr=capture.capture(*d.native(),reflection->static_texture(),
            d.trace.frame_number(),false);
        if(capture.pending()) {
            const HRESULT repaired=ps2integration::repair(d);
            if(FAILED(repaired))return {true,repaired};
        }
        if(FAILED(capture_hr) || !capture.ready_texture(d.trace.frame_number()))return {};
        uint32_t submitted=0,shiny_submitted=0;size_t run_index=0;
        const HRESULT hr=ps2port::submit_partition(plan,start,
            [&](const ps2port::PartitionRun& run,UINT first) noexcept {
                const auto current=run_index++;
                const HRESULT safe=ps2integration::repair(d);
                if(FAILED(safe)){results[current]=safe;return safe;}
                if(!run.shiny) {
                    ++submitted;
                    results[current]=d.native()->DrawIndexedPrimitive(type,min_index,vertices,first,run.count);
                    return results[current];
                }
                ps2integration::Scope scope(d,s,std::move(identities[current]),pc);
                const HRESULT ready=scope.pre_draw_status();if(FAILED(ready)){results[current]=ready;return ready;}
                ++submitted;if(scope.applied())++shiny_submitted;
                applied[current]=scope.applied();
                const HRESULT result=d.native()->DrawIndexedPrimitive(type,min_index,vertices,first,run.count);
                results[current]=result;
                scope.draw_result(result);return result;
            });
        if(p->claim_diagnostic(plan.material))try {
            std::string runs="[";
            for(size_t i=0;i<plan.runs.size();++i) {
                const auto& run=plan.runs[i];if(i)runs+=',';
                runs+="{\"start_index\":"+std::to_string(start+3*run.first)+",\"triangles\":"+
                    std::to_string(run.count)+",\"policy\":"+quote(run.shiny?"PS2_MODE4_CARSHINY":"STOCK")+
                    ",\"override_applied\":"+(applied[i]?"true":"false")+
                    ",\"hresult\":"+(results[i]==E_PENDING?"null":std::to_string(static_cast<uint32_t>(results[i])))+"}";
            }
            runs+=']';
            session().write("{\"type\":\"ps2_vehicle_material_partition\",\"frame\":"+
                std::to_string(d.trace.frame_number())+",\"vehicle\":"+quote(plan.material->vehicle)+
                ",\"geometry_sha256\":"+quote(plan.material->geometry_sha)+
                ",\"vertex_generation\":"+std::to_string(g.vertex_generation)+
                ",\"index_generation\":"+std::to_string(g.index_generation)+
                ",\"vertex_revision\":"+std::to_string(g.vertex_revision)+
                ",\"index_revision\":"+std::to_string(g.index_revision)+
                ",\"reset_generation\":"+std::to_string(g.reset_generation)+
                ",\"native_subdraws\":"+std::to_string(submitted)+
                ",\"shiny_subdraws\":"+std::to_string(shiny_submitted)+
                ",\"hresult\":"+std::to_string(static_cast<uint32_t>(hr))+
                ",\"state_restore_pending\":"+(e->native_states_pending()?"true":"false")+
                ",\"source_order_preserved\":true,\"replay\":false,\"runs\":"+runs+"}");
        }catch(...){}
        return {true,hr};
    }catch(...){return {};}
}
} // namespace gfx2::vehicleintegration
