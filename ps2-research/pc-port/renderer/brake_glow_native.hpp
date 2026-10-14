#pragma once
#include "xtrail_native_integration.hpp"
namespace gfx2::lampintegration {
inline xtrailintegration::Result draw(Device8& d,D3DPRIMITIVETYPE type,UINT min_index,UINT vertices,UINT start,UINT count,uintptr_t pc)noexcept{
 auto* e=d.ps2_port();auto* p=e&&e->xtrail()?e->xtrail()->brake():nullptr;
 if(!p||!p->requested()||!e->reflection()||!e->reflection()->active()||e->reflection()->mode_value()!=4||type!=D3DPT_TRIANGLELIST||count!=20||vertices!=20||!d.trace.scene_active||GetCurrentThreadId()!=d.trace.render_thread_id()||d.trace.shadow.recording||d.trace.effective_shadow.recording)return {};
 if(pc!=reinterpret_cast<uintptr_t>(GetModuleHandleW(nullptr))+SHARED_WORLD_RETURN_RVA)return {};
 bool committed=false;HRESULT submitted=E_FAIL;
 try{
  bool single=false;const auto certificate=courseintegration::certificate(single);if(!single||!certificate.valid)return {};
  auto& n=*d.native();ps2integration::Ref<IDirect3DVertexBuffer8> vb;ps2integration::Ref<IDirect3DIndexBuffer8> ib;ps2integration::Ref<IDirect3DBaseTexture8> texture;
  DWORD fvf=0,pixel=0;UINT stride=0,base=0;
  if(FAILED(n.GetVertexShader(&fvf))||fvf!=0x112||FAILED(n.GetPixelShader(&pixel))||pixel||FAILED(n.GetStreamSource(0,&vb.value,&stride))||!vb.value||stride!=32||FAILED(n.GetIndices(&ib.value,&base))||!ib.value||FAILED(n.GetTexture(0,&texture.value))||!texture.value||texture.value->GetType()!=D3DRTYPE_TEXTURE)return {};
  const auto& bindings=d.trace.effective_shadow.bindings;
  if(!bindings.vertex_shader.known||bindings.vertex_shader.value!=fvf||!bindings.pixel_shader.known||bindings.pixel_shader.value||!bindings.streams[0].known||bindings.streams[0].value.pointer!=reinterpret_cast<uintptr_t>(vb.value)||bindings.streams[0].value.stride!=32||!bindings.indices.known||bindings.indices.value.pointer!=reinterpret_cast<uintptr_t>(ib.value)||bindings.indices.value.base!=base)return {};
  const auto texid=reinterpret_cast<uintptr_t>(texture.value);const auto& tex=bindings.textures[0];if(!tex.known||tex.value!=texid||!d.trace.resources.generation(texid))return {};
  D3DMATRIX world{};const auto& tracked=d.trace.effective_shadow.matrices[D3DTS_WORLD];if(!tracked.known||FAILED(n.GetTransform(D3DTS_WORLD,&world))||!courseintegration::finite_matrix(world)||std::memcmp(&world,&tracked.value,64))return {};
  D3DVERTEXBUFFER_DESC vd{};D3DINDEXBUFFER_DESC id{};if(FAILED(vb.value->GetDesc(&vd))||FAILED(ib.value->GetDesc(&id)))return {};
  const UINT size=id.Format==D3DFMT_INDEX16?2u:id.Format==D3DFMT_INDEX32?4u:0;const uint64_t vo=(uint64_t(base)+min_index)*32,io=uint64_t(start)*size,is=uint64_t(count)*3*size;if(!size||vo>vd.Size||640>vd.Size-vo||io>id.Size||is>id.Size-io)return {};
  ps2port::DrawSnapshot g;g.supported_build=session().target;g.device_id=d.trace.device_id();g.reset_generation=e->reset_generation();g.primitive_type=type;g.primitive_count=count;g.vertex_count=vertices;g.fvf=fvf;g.stride=stride;g.min_index=min_index;g.base_vertex=base;g.start_index=start;g.index_format=id.Format;g.vertex_byte_offset=vo;g.vertex_resource=reinterpret_cast<uintptr_t>(vb.value);g.index_resource=reinterpret_cast<uintptr_t>(ib.value);g.vertex_generation=d.trace.resources.generation(g.vertex_resource);g.index_generation=d.trace.resources.generation(g.index_resource);
  if(!g.vertex_generation||!g.index_generation||!d.copy_buffer_shadow(vb.value,BufferKind::Vertex,g.vertex_generation,vo,640,g.vertex_bytes,g.vertex_revision)||!d.copy_buffer_shadow(ib.value,BufferKind::Index,g.index_generation,io,static_cast<size_t>(is),g.index_bytes,g.index_revision))return {};g.complete_mirror_coverage=true;
  const bool identity=ps2port::terrano_glow_identity(g);
  auto log=[&](bool success,HRESULT apply,HRESULT drawn,HRESULT restored)noexcept{if(!p->claim(success))return;try{session().write("{\"type\":\"ps2_brake_glow\",\"vehicle\":\"Terrano\",\"frame\":"+std::to_string(d.trace.frame_number())+",\"mode\":1,\"current_upload_verified\":"+(identity?"true":"false")+",\"override_applied\":"+(success?"true":"false")+",\"texture_source\":\"ORIGINAL_PC_UNCHANGED\",\"controller_reads_added\":0,\"apply_hresult\":"+std::to_string(static_cast<uint32_t>(apply))+",\"draw_hresult\":"+std::to_string(static_cast<uint32_t>(drawn))+",\"restore_hresult\":"+std::to_string(static_cast<uint32_t>(restored))+",\"restore_pending\":"+(p->transaction.pending()?"true":"false")+"}");}catch(...){}};
  if(!identity){log(false,E_PENDING,E_PENDING,E_PENDING);return {};}
  DWORD value=0;for(auto expected:std::array<std::pair<D3DRENDERSTATETYPE,DWORD>,6>{{{D3DRS_ALPHATESTENABLE,FALSE},{D3DRS_ALPHABLENDENABLE,TRUE},{D3DRS_SRCBLEND,D3DBLEND_SRCALPHA},{D3DRS_DESTBLEND,D3DBLEND_INVSRCALPHA},{D3DRS_ZWRITEENABLE,TRUE},{D3DRS_BLENDOP,D3DBLENDOP_ADD}}})if(FAILED(n.GetRenderState(expected.first,&value))||value!=expected.second)return {};
  if(!courseintegration::native_dependencies(n))return {};
  D3DCAPS8 caps{};if(FAILED(n.GetDeviceCaps(&caps))||!(caps.SrcBlendCaps&D3DPBLENDCAPS_ONE)||!(caps.DestBlendCaps&D3DPBLENDCAPS_ONE)||!(caps.TextureOpCaps&D3DTEXOPCAPS_SELECTARG1))return {};
  auto writer=[&](uint32_t slot,const Args& a,HRESULT h)noexcept{xtrailintegration::notify(d,slot,a,h);};auto& transaction=p->transaction;auto hr=transaction.capture(n);if(FAILED(hr))return {};
  const auto applied=transaction.emissive_pass(n,writer);if(FAILED(applied)){const auto restored=transaction.restore(n,writer);log(false,applied,E_PENDING,restored);if(FAILED(restored)){p->disable();return {true,restored};}return {};}
  committed=true;const auto drawn=n.DrawIndexedPrimitive(type,min_index,vertices,start,count);submitted=drawn;xtrailintegration::notify(d,71,pack(type,min_index,vertices,start,count),drawn);const auto restored=transaction.restore(n,writer);if(FAILED(restored))p->disable();log(SUCCEEDED(drawn)&&SUCCEEDED(restored),applied,drawn,restored);return {true,drawn};
 }catch(...){if(!committed)return {};xtrailintegration::repair(d);return {true,submitted};}
}
}
