#pragma once
#include <algorithm>
#include <functional>
#include "frontend_model.hpp"
#include "fleet_private_off_registry.hpp"
namespace gfx2::ps2port {
// Interchangeable identical blocks (UFO: five 17-vertex lamp domes with one UV layout) may be submitted
// in another block order than car.dx. Only block permutations among contiguous components of equal size
// and identical UV bytes are tried (at most 720), and only one whose ordered positions hash exactly to the
// pinned source order is returned: order[source_vertex] = runtime_vertex. Empty means no exact order.
inline std::vector<unsigned> block_source_order(const DrawSnapshot& g,const std::vector<std::array<float,3>>& points,const char* orderedXyz){
 std::vector<unsigned> none;try{
  const unsigned uv=g.fvf==0x142?16:g.fvf==0x152?28:g.fvf==0x112?24:0,width=g.index_format==D3DFMT_INDEX16?2:g.index_format==D3DFMT_INDEX32?4:0;const unsigned n=g.vertex_count;
  if(!uv||!width||!orderedXyz||points.size()!=n||g.vertex_bytes.size()!=uint64_t(n)*g.stride||g.index_bytes.size()!=uint64_t(g.primitive_count)*3*width)return none;
  std::vector<unsigned> parent(n);for(unsigned i=0;i<n;++i)parent[i]=i;
  auto find=[&](unsigned i){while(parent[i]!=i){parent[i]=parent[parent[i]];i=parent[i];}return i;};
  std::vector<unsigned> ids(g.primitive_count*3);for(size_t k=0;k<ids.size();++k){uint32_t v=0;std::memcpy(&v,g.index_bytes.data()+k*width,width);if(v<g.min_index||v-g.min_index>=n)return none;ids[k]=v-g.min_index;}
  for(size_t k=0;k<ids.size();k+=3){parent[find(ids[k])]=find(ids[k+1]);parent[find(ids[k+1])]=find(ids[k+2]);}
  struct Block{unsigned first,count;std::string uv;};std::vector<Block> blocks;
  for(unsigned i=0;i<n;){const unsigned root=find(i);unsigned j=i;while(j<n&&find(j)==root)++j;for(unsigned k=j;k<n;++k)if(find(k)==root)return none;
   Block b{i,j-i,{}};for(unsigned k=i;k<j;++k)b.uv.append(reinterpret_cast<const char*>(g.vertex_bytes.data()+uint64_t(k)*g.stride+uv),8);blocks.push_back(std::move(b));i=j;}
  std::vector<std::vector<unsigned>> groups;std::vector<bool> grouped(blocks.size());uint64_t combinations=1;
  for(unsigned a=0;a<blocks.size();++a){if(grouped[a])continue;std::vector<unsigned> group{a};for(unsigned b=a+1;b<blocks.size();++b)if(!grouped[b]&&blocks[b].count==blocks[a].count&&blocks[b].uv==blocks[a].uv){group.push_back(b);grouped[b]=true;}
   if(group.size()>1){for(unsigned k=2;k<=group.size();++k)combinations*=k;if(combinations>720)return none;groups.push_back(group);}}
  if(groups.empty())return none;
  std::vector<std::vector<unsigned>> current=groups;for(auto& gr:current)std::sort(gr.begin(),gr.end());
  std::vector<unsigned> found;unsigned matches=0;
  auto evaluate=[&](){std::vector<unsigned> slot(blocks.size());for(unsigned b=0;b<blocks.size();++b)slot[b]=b;for(size_t k=0;k<groups.size();++k)for(size_t m=0;m<groups[k].size();++m)slot[groups[k][m]]=current[k][m];
   std::vector<unsigned> order(n);std::string bytes;bytes.reserve(size_t(n)*12);for(unsigned b=0;b<blocks.size();++b){const auto& src=blocks[slot[b]];for(unsigned k=0;k<blocks[b].count;++k)order[blocks[b].first+k]=src.first+k;}
   for(unsigned v=0;v<n;++v)bytes.append(reinterpret_cast<const char*>(points[order[v]].data()),12);
   if(sha256_bytes(bytes.data(),bytes.size())==orderedXyz){++matches;found=order;}};
  std::function<void(size_t)> walk=[&](size_t k){if(k==current.size()){evaluate();return;}do walk(k+1);while(std::next_permutation(current[k].begin(),current[k].end()));};
  walk(0);return matches==1?found:none;
 }catch(...){return none;}
}
inline std::vector<std::array<float,3>> source_ordered(const std::vector<std::array<float,3>>& points,const std::vector<unsigned>& order){
 if(order.empty())return points;std::vector<std::array<float,3>> out(order.size());for(size_t i=0;i<order.size();++i)out[i]=points.at(order[i]);return out;
}
inline bool private_off_vertices(const off_followup::Profile& p,const std::vector<std::array<float,3>>& current,const std::vector<std::array<float,3>>& reference,const FrontendAsset& asset,const std::vector<FrontendVertex>& original,std::vector<FrontendVertex>& out){
 if(current.size()!=p.nativeVertices||reference.size()!=current.size()||asset.meshes.size()!=1||p.mappingCount!=asset.vertices.size())return false;const auto& mesh=asset.meshes[0];if(mesh.count!=original.size()||mesh.first>asset.indices.size()||mesh.count>asset.indices.size()-mesh.first)return false;auto next=original;
 for(unsigned i=0;i<next.size();++i){const auto vertex=asset.indices[mesh.first+i];if(vertex>=p.mappingCount)return false;const auto& map=p.mapping[vertex];if(!map.count||map.first>p.candidateCount||map.count>p.candidateCount-map.first)return false;std::array<float,3> delta{};for(unsigned k=0;k<map.count;++k){const auto source=p.candidates[map.first+k];if(source>=current.size())return false;for(unsigned axis=0;axis<3;++axis){const auto value=current[source][axis]-reference[source][axis];if(!std::isfinite(value)||(k&&std::fabs(value-delta[axis])>1e-6f))return false;if(!k)delta[axis]=value;}}for(unsigned axis=0;axis<3;++axis){next[i].xyz[axis]+=delta[axis];if(!std::isfinite(next[i].xyz[axis]))return false;}}
 out=std::move(next);return true;
}
}
