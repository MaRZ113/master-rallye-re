#include "brake_glow.hpp"
#include "brake_glow_identity.hpp"
#include "provenance.hpp"
#include <algorithm>
#include <cstring>
namespace gfx2::ps2port {
bool terrano_glow_identity(const DrawSnapshot& g,std::string_view geometry,std::string_view expected_attributes)noexcept{try{
 if(!g.supported_build||!g.device_id||g.fvf!=0x112||g.stride!=32||g.vertex_count!=20||g.primitive_count!=20||g.vertex_byte_offset!=(uint64_t(g.base_vertex)+g.min_index)*32||g.vertex_bytes.size()!=640)return false;
 std::vector<std::string> attributes;DrawSnapshot normalized=g;normalized.fvf=0x152;normalized.stride=36;normalized.base_vertex=0;normalized.vertex_byte_offset=uint64_t(g.min_index)*36;normalized.vertex_bytes.resize(720);
 for(unsigned i=0;i<20;++i){const auto* v=g.vertex_bytes.data()+i*32;attributes.emplace_back(reinterpret_cast<const char*>(v),32);auto* out=normalized.vertex_bytes.data()+i*36;std::memcpy(out,v,24);uint32_t white=0xffffffff;std::memcpy(out+24,&white,4);std::memcpy(out+28,v+24,8);}
 auto fs=vehicle_face_hashes(normalized);if(fs.size()!=20)return false;std::sort(fs.begin(),fs.end());std::string joined;for(auto& h:fs)joined+=h;if(sha256_bytes(joined.data(),joined.size())!=geometry)return false;
 std::sort(attributes.begin(),attributes.end());joined.clear();for(auto& v:attributes)joined+=v;return sha256_bytes(joined.data(),joined.size())==expected_attributes;
 }catch(...){return false;}}
}
