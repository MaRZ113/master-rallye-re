#pragma once
#include "ps2_port_extension.hpp"
#include "state_tracker.hpp"
namespace gfx2::ps2port {
struct FrontendOp {bool render;DWORD stage,key;};
inline constexpr FrontendOp kFrontendOps[]={
 {true,0,D3DRS_ALPHATESTENABLE},{true,0,D3DRS_ALPHABLENDENABLE},{true,0,D3DRS_SRCBLEND},{true,0,D3DRS_DESTBLEND},{true,0,D3DRS_ZWRITEENABLE},{true,0,D3DRS_CULLMODE},
 {false,0,D3DTSS_COLOROP},{false,0,D3DTSS_COLORARG1},{false,0,D3DTSS_COLORARG2},{false,0,D3DTSS_ALPHAOP},{false,0,D3DTSS_ALPHAARG1},{false,0,D3DTSS_ALPHAARG2},{false,0,D3DTSS_TEXCOORDINDEX},{false,0,D3DTSS_TEXTURETRANSFORMFLAGS},{false,0,D3DTSS_ADDRESSU},{false,0,D3DTSS_ADDRESSV},{false,0,D3DTSS_MINFILTER},{false,0,D3DTSS_MAGFILTER},{false,0,D3DTSS_MIPFILTER},
 {false,1,D3DTSS_COLOROP},{false,1,D3DTSS_COLORARG1},{false,1,D3DTSS_COLORARG2},{false,1,D3DTSS_ALPHAOP},{false,1,D3DTSS_ALPHAARG1},{false,1,D3DTSS_ALPHAARG2},{false,1,D3DTSS_TEXCOORDINDEX},{false,1,D3DTSS_TEXTURETRANSFORMFLAGS},{false,1,D3DTSS_ADDRESSU},{false,1,D3DTSS_ADDRESSV},{false,1,D3DTSS_MINFILTER},{false,1,D3DTSS_MAGFILTER},{false,1,D3DTSS_MIPFILTER},{false,2,D3DTSS_COLOROP}};
class FrontendTransaction {
 std::array<DWORD,std::size(kFrontendOps)> values_{},current_{};IDirect3DBaseTexture8* current_textures_[2]{};DWORD current_vertex_=0,current_pixel_=0;D3DMATRIX current_matrix_{};IDirect3DBaseTexture8* textures_[2]{};IDirect3DVertexBuffer8* stream_=nullptr;UINT stride_=0;DWORD vertex_=0,pixel_=0;D3DMATRIX tex1_{};uint64_t pending_=0;bool captured_=false;
public:
 ~FrontendTransaction(){release();}bool pending()const noexcept{return pending_!=0;}
 void release()noexcept{for(auto*& p:textures_){if(p)p->Release();p=nullptr;}if(stream_)stream_->Release();stream_=nullptr;pending_=0;captured_=false;}
 HRESULT capture(IDirect3DDevice8& n)noexcept{if(pending())return E_FAIL;release();for(size_t i=0;i<std::size(kFrontendOps);++i){const auto& op=kFrontendOps[i];HRESULT hr=op.render?n.GetRenderState(static_cast<D3DRENDERSTATETYPE>(op.key),&values_[i]):n.GetTextureStageState(op.stage,static_cast<D3DTEXTURESTAGESTATETYPE>(op.key),&values_[i]);if(FAILED(hr)){release();return hr;}}HRESULT hr=n.GetTexture(0,&textures_[0]);if(SUCCEEDED(hr))hr=n.GetTexture(1,&textures_[1]);if(SUCCEEDED(hr))hr=n.GetStreamSource(0,&stream_,&stride_);if(SUCCEEDED(hr))hr=n.GetVertexShader(&vertex_);if(SUCCEEDED(hr))hr=n.GetPixelShader(&pixel_);if(SUCCEEDED(hr))hr=n.GetTransform(D3DTS_TEXTURE1,&tex1_);if(FAILED(hr)){release();return hr;}current_=values_;current_textures_[0]=textures_[0];current_textures_[1]=textures_[1];current_vertex_=vertex_;current_pixel_=pixel_;current_matrix_=tex1_;captured_=true;return S_OK;}
 template<class W>HRESULT material(IDirect3DDevice8& n,uint32_t mode,IDirect3DTexture8* primary,IDirect3DTexture8* secondary,const D3DMATRIX& env,W&& writer)noexcept{
  if(!captured_||!primary)return E_INVALIDARG;const bool glass=mode==20,shiny=mode==3&&secondary;
  const std::array<DWORD,std::size(kFrontendOps)> desired={FALSE,glass?DWORD(TRUE):DWORD(FALSE),D3DBLEND_SRCALPHA,D3DBLEND_INVSRCALPHA,glass?DWORD(FALSE):DWORD(TRUE),D3DCULL_NONE,
   D3DTOP_MODULATE,D3DTA_TEXTURE,D3DTA_DIFFUSE,D3DTOP_MODULATE,D3DTA_TEXTURE,D3DTA_DIFFUSE,0,D3DTTFF_DISABLE,D3DTADDRESS_CLAMP,D3DTADDRESS_CLAMP,D3DTEXF_LINEAR,D3DTEXF_LINEAR,D3DTEXF_NONE,
   shiny?DWORD(D3DTOP_MODULATEALPHA_ADDCOLOR):DWORD(D3DTOP_DISABLE),D3DTA_TEXTURE,D3DTA_CURRENT,D3DTOP_SELECTARG2,D3DTA_TEXTURE,D3DTA_CURRENT,D3DTSS_TCI_CAMERASPACENORMAL,D3DTTFF_COUNT2,D3DTADDRESS_CLAMP,D3DTADDRESS_CLAMP,D3DTEXF_LINEAR,D3DTEXF_LINEAR,D3DTEXF_NONE,D3DTOP_DISABLE};
  for(size_t i=0;i<desired.size();++i){if(desired[i]==current_[i])continue;pending_|=uint64_t(1)<<i;const auto& op=kFrontendOps[i];auto hr=op.render?n.SetRenderState(static_cast<D3DRENDERSTATETYPE>(op.key),desired[i]):n.SetTextureStageState(op.stage,static_cast<D3DTEXTURESTAGESTATETYPE>(op.key),desired[i]);if(op.render)writer(50,pack(op.key,desired[i]),hr);else writer(63,pack(op.stage,op.key,desired[i]),hr);if(FAILED(hr))return hr;current_[i]=desired[i];}
  for(unsigned i=0;i<2;++i){auto* t=i?secondary:primary;if(current_textures_[i]==t)continue;pending_|=uint64_t(1)<<(33+i);auto hr=n.SetTexture(i,t);writer(61,pack(i,t),hr);if(FAILED(hr))return hr;current_textures_[i]=t;}
  HRESULT hr=S_OK;if(current_vertex_!=0x152){pending_|=uint64_t(1)<<35;hr=n.SetVertexShader(0x152);writer(76,pack(DWORD(0x152)),hr);if(FAILED(hr))return hr;current_vertex_=0x152;}
  if(current_pixel_){pending_|=uint64_t(1)<<36;hr=n.SetPixelShader(0);writer(88,pack(DWORD(0)),hr);if(FAILED(hr))return hr;current_pixel_=0;}
  if(shiny&&std::memcmp(&current_matrix_,&env,64)){pending_|=uint64_t(1)<<37;hr=n.SetTransform(D3DTS_TEXTURE1,&env);writer(37,pack(D3DTS_TEXTURE1,&env),hr);if(SUCCEEDED(hr))current_matrix_=env;}return hr;
 }
 void before_up()noexcept{pending_|=uint64_t(1)<<38;}
 template<class W>HRESULT restore(IDirect3DDevice8& n,W&& writer)noexcept{HRESULT result=S_OK;for(int i=38;i>=0;--i){if(!(pending_&(uint64_t(1)<<i)))continue;HRESULT hr=E_FAIL;
  if(i==38){hr=n.SetStreamSource(0,stream_,stride_);writer(83,pack(0,stream_,stride_),hr);}else if(i==37){hr=n.SetTransform(D3DTS_TEXTURE1,&tex1_);writer(37,pack(D3DTS_TEXTURE1,&tex1_),hr);}else if(i==36){hr=n.SetPixelShader(pixel_);writer(88,pack(pixel_),hr);}else if(i==35){hr=n.SetVertexShader(vertex_);writer(76,pack(vertex_),hr);}else if(i>=33){const auto stage=i-33;hr=n.SetTexture(stage,textures_[stage]);writer(61,pack(stage,textures_[stage]),hr);}else{const auto& op=kFrontendOps[i];hr=op.render?n.SetRenderState(static_cast<D3DRENDERSTATETYPE>(op.key),values_[i]):n.SetTextureStageState(op.stage,static_cast<D3DTEXTURESTAGESTATETYPE>(op.key),values_[i]);if(op.render)writer(50,pack(op.key,values_[i]),hr);else writer(63,pack(op.stage,op.key,values_[i]),hr);}
  if(SUCCEEDED(hr))pending_&=~(uint64_t(1)<<i);else if(SUCCEEDED(result))result=hr;
 }if(!pending_)release();return result;}
};
}
