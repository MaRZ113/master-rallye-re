#pragma once
#include "frontend_model.hpp"
#include "fleet_private_off_registry.hpp"
namespace gfx2::ps2port {
inline bool private_off_vertices(const off_followup::Profile& p,const std::vector<std::array<float,3>>& current,const std::vector<std::array<float,3>>& reference,const FrontendAsset& asset,const std::vector<FrontendVertex>& original,std::vector<FrontendVertex>& out){
 if(current.size()!=p.nativeVertices||reference.size()!=current.size()||asset.meshes.size()!=1||p.mappingCount!=asset.vertices.size())return false;const auto& mesh=asset.meshes[0];if(mesh.count!=original.size()||mesh.first>asset.indices.size()||mesh.count>asset.indices.size()-mesh.first)return false;auto next=original;
 for(unsigned i=0;i<next.size();++i){const auto vertex=asset.indices[mesh.first+i];if(vertex>=p.mappingCount)return false;const auto& map=p.mapping[vertex];if(!map.count||map.first>p.candidateCount||map.count>p.candidateCount-map.first)return false;std::array<float,3> delta{};for(unsigned k=0;k<map.count;++k){const auto source=p.candidates[map.first+k];if(source>=current.size())return false;for(unsigned axis=0;axis<3;++axis){const auto value=current[source][axis]-reference[source][axis];if(!std::isfinite(value)||(k&&std::fabs(value-delta[axis])>1e-6f))return false;if(!k)delta[axis]=value;}}for(unsigned axis=0;axis<3;++axis){next[i].xyz[axis]+=delta[axis];if(!std::isfinite(next[i].xyz[axis]))return false;}}
 out=std::move(next);return true;
}
}
