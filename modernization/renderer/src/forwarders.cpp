// Generated complete forwarders; COM plumbing is in wrappers.cpp.
#include "wrappers.hpp"
#include <intrin.h>
namespace gfx2 {
HRESULT STDMETHODCALLTYPE Root8::RegisterSoftwareDevice(void * pInitializeFunction) {
 return real_->RegisterSoftwareDevice(pInitializeFunction);
}
UINT STDMETHODCALLTYPE Root8::GetAdapterCount() {
 return real_->GetAdapterCount();
}
HRESULT STDMETHODCALLTYPE Root8::GetAdapterIdentifier(UINT Adapter, DWORD Flags, D3DADAPTER_IDENTIFIER8 * pIdentifier) {
 return real_->GetAdapterIdentifier(Adapter, Flags, pIdentifier);
}
UINT STDMETHODCALLTYPE Root8::GetAdapterModeCount(UINT Adapter) {
 return real_->GetAdapterModeCount(Adapter);
}
HRESULT STDMETHODCALLTYPE Root8::EnumAdapterModes(UINT Adapter, UINT Mode, D3DDISPLAYMODE * pMode) {
 return real_->EnumAdapterModes(Adapter, Mode, pMode);
}
HRESULT STDMETHODCALLTYPE Root8::GetAdapterDisplayMode(UINT Adapter, D3DDISPLAYMODE * pMode) {
 return real_->GetAdapterDisplayMode(Adapter, pMode);
}
HRESULT STDMETHODCALLTYPE Root8::CheckDeviceType(UINT Adapter, D3DDEVTYPE CheckType, D3DFORMAT DisplayFormat, D3DFORMAT BackBufferFormat, WINBOOL Windowed) {
 return real_->CheckDeviceType(Adapter, CheckType, DisplayFormat, BackBufferFormat, Windowed);
}
HRESULT STDMETHODCALLTYPE Root8::CheckDeviceFormat(UINT Adapter, D3DDEVTYPE DeviceType, D3DFORMAT AdapterFormat, DWORD Usage, D3DRESOURCETYPE RType, D3DFORMAT CheckFormat) {
 return real_->CheckDeviceFormat(Adapter, DeviceType, AdapterFormat, Usage, RType, CheckFormat);
}
HRESULT STDMETHODCALLTYPE Root8::CheckDeviceMultiSampleType(UINT Adapter, D3DDEVTYPE DeviceType, D3DFORMAT SurfaceFormat, WINBOOL Windowed, D3DMULTISAMPLE_TYPE MultiSampleType) {
 return real_->CheckDeviceMultiSampleType(Adapter, DeviceType, SurfaceFormat, Windowed, MultiSampleType);
}
HRESULT STDMETHODCALLTYPE Root8::CheckDepthStencilMatch(UINT Adapter, D3DDEVTYPE DeviceType, D3DFORMAT AdapterFormat, D3DFORMAT RenderTargetFormat, D3DFORMAT DepthStencilFormat) {
 return real_->CheckDepthStencilMatch(Adapter, DeviceType, AdapterFormat, RenderTargetFormat, DepthStencilFormat);
}
HRESULT STDMETHODCALLTYPE Root8::GetDeviceCaps(UINT Adapter, D3DDEVTYPE DeviceType, D3DCAPS8 * pCaps) {
 return real_->GetDeviceCaps(Adapter, DeviceType, pCaps);
}
HMONITOR STDMETHODCALLTYPE Root8::GetAdapterMonitor(UINT Adapter) {
 return real_->GetAdapterMonitor(Adapter);
}
HRESULT STDMETHODCALLTYPE Device8::TestCooperativeLevel() {
 auto guard = trace.guard();
 const auto args = pack();
 const auto pc = reinterpret_cast<uintptr_t>(_ReturnAddress());
 trace.before(3, args, pc);
 HRESULT result = real_->TestCooperativeLevel();
 trace.after(3, args, static_cast<uint32_t>(result), pc);
 return result;
}
UINT STDMETHODCALLTYPE Device8::GetAvailableTextureMem() {
 auto guard = trace.guard();
 const auto args = pack();
 const auto pc = reinterpret_cast<uintptr_t>(_ReturnAddress());
 trace.before(4, args, pc);
 UINT result = real_->GetAvailableTextureMem();
 trace.after(4, args, static_cast<uint32_t>(result), pc);
 return result;
}
HRESULT STDMETHODCALLTYPE Device8::ResourceManagerDiscardBytes(DWORD Bytes) {
 auto guard = trace.guard();
 const auto args = pack(Bytes);
 const auto pc = reinterpret_cast<uintptr_t>(_ReturnAddress());
 trace.before(5, args, pc);
 HRESULT result = real_->ResourceManagerDiscardBytes(Bytes);
 trace.after(5, args, static_cast<uint32_t>(result), pc);
 return result;
}
HRESULT STDMETHODCALLTYPE Device8::GetDeviceCaps(D3DCAPS8 * pCaps) {
 auto guard = trace.guard();
 const auto args = pack(pCaps);
 const auto pc = reinterpret_cast<uintptr_t>(_ReturnAddress());
 trace.before(7, args, pc);
 HRESULT result = real_->GetDeviceCaps(pCaps);
 trace.after(7, args, static_cast<uint32_t>(result), pc);
 return result;
}
HRESULT STDMETHODCALLTYPE Device8::GetDisplayMode(D3DDISPLAYMODE * pMode) {
 auto guard = trace.guard();
 const auto args = pack(pMode);
 const auto pc = reinterpret_cast<uintptr_t>(_ReturnAddress());
 trace.before(8, args, pc);
 HRESULT result = real_->GetDisplayMode(pMode);
 trace.after(8, args, static_cast<uint32_t>(result), pc);
 return result;
}
HRESULT STDMETHODCALLTYPE Device8::GetCreationParameters(D3DDEVICE_CREATION_PARAMETERS * pParameters) {
 auto guard = trace.guard();
 const auto args = pack(pParameters);
 const auto pc = reinterpret_cast<uintptr_t>(_ReturnAddress());
 trace.before(9, args, pc);
 HRESULT result = real_->GetCreationParameters(pParameters);
 trace.after(9, args, static_cast<uint32_t>(result), pc);
 return result;
}
HRESULT STDMETHODCALLTYPE Device8::SetCursorProperties(UINT XHotSpot, UINT YHotSpot, IDirect3DSurface8 * pCursorBitmap) {
 auto guard = trace.guard();
 const auto args = pack(XHotSpot, YHotSpot, pCursorBitmap);
 const auto pc = reinterpret_cast<uintptr_t>(_ReturnAddress());
 trace.before(10, args, pc);
 HRESULT result = real_->SetCursorProperties(XHotSpot, YHotSpot, pCursorBitmap);
 trace.after(10, args, static_cast<uint32_t>(result), pc);
 return result;
}
void STDMETHODCALLTYPE Device8::SetCursorPosition(UINT XScreenSpace, UINT YScreenSpace,DWORD Flags) {
 auto guard = trace.guard();
 const auto args = pack(XScreenSpace, YScreenSpace, Flags);
 const auto pc = reinterpret_cast<uintptr_t>(_ReturnAddress());
 trace.before(11, args, pc);
 real_->SetCursorPosition(XScreenSpace, YScreenSpace, Flags);
 trace.after(11, args, 0, pc);
}
WINBOOL STDMETHODCALLTYPE Device8::ShowCursor(WINBOOL bShow) {
 auto guard = trace.guard();
 const auto args = pack(bShow);
 const auto pc = reinterpret_cast<uintptr_t>(_ReturnAddress());
 trace.before(12, args, pc);
 WINBOOL result = real_->ShowCursor(bShow);
 trace.after(12, args, static_cast<uint32_t>(result), pc);
 return result;
}
HRESULT STDMETHODCALLTYPE Device8::CreateAdditionalSwapChain(D3DPRESENT_PARAMETERS * pPresentationParameters, IDirect3DSwapChain8 ** pSwapChain) {
 auto guard = trace.guard();
 const auto args = pack(pPresentationParameters, pSwapChain);
 const auto pc = reinterpret_cast<uintptr_t>(_ReturnAddress());
 trace.before(13, args, pc);
 HRESULT result = real_->CreateAdditionalSwapChain(pPresentationParameters, pSwapChain);
 trace.after(13, args, static_cast<uint32_t>(result), pc);
 return result;
}
HRESULT STDMETHODCALLTYPE Device8::Reset(D3DPRESENT_PARAMETERS * pPresentationParameters) {
 auto guard = trace.guard();
 const auto args = pack(pPresentationParameters);
 const auto pc = reinterpret_cast<uintptr_t>(_ReturnAddress());
 trace.before(14, args, pc);
 HRESULT result = real_->Reset(pPresentationParameters);
 trace.after(14, args, static_cast<uint32_t>(result), pc);
 return result;
}
HRESULT STDMETHODCALLTYPE Device8::Present(const RECT *src_rect, const RECT *dst_rect, HWND dst_window_override, const RGNDATA *dirty_region) {
 auto guard = trace.guard();
 const auto args = pack(src_rect, dst_rect, dst_window_override, dirty_region);
 const auto pc = reinterpret_cast<uintptr_t>(_ReturnAddress());
 trace.before(15, args, pc);
 HRESULT result = real_->Present(src_rect, dst_rect, dst_window_override, dirty_region);
 trace.after(15, args, static_cast<uint32_t>(result), pc);
 return result;
}
HRESULT STDMETHODCALLTYPE Device8::GetBackBuffer(UINT BackBuffer,D3DBACKBUFFER_TYPE Type,IDirect3DSurface8 ** ppBackBuffer) {
 auto guard = trace.guard();
 const auto args = pack(BackBuffer, Type, ppBackBuffer);
 const auto pc = reinterpret_cast<uintptr_t>(_ReturnAddress());
 trace.before(16, args, pc);
 HRESULT result = real_->GetBackBuffer(BackBuffer, Type, ppBackBuffer);
 trace.after(16, args, static_cast<uint32_t>(result), pc);
 return result;
}
HRESULT STDMETHODCALLTYPE Device8::GetRasterStatus(D3DRASTER_STATUS * pRasterStatus) {
 auto guard = trace.guard();
 const auto args = pack(pRasterStatus);
 const auto pc = reinterpret_cast<uintptr_t>(_ReturnAddress());
 trace.before(17, args, pc);
 HRESULT result = real_->GetRasterStatus(pRasterStatus);
 trace.after(17, args, static_cast<uint32_t>(result), pc);
 return result;
}
void STDMETHODCALLTYPE Device8::SetGammaRamp(DWORD flags, const D3DGAMMARAMP *ramp) {
 auto guard = trace.guard();
 const auto args = pack(flags, ramp);
 const auto pc = reinterpret_cast<uintptr_t>(_ReturnAddress());
 trace.before(18, args, pc);
 real_->SetGammaRamp(flags, ramp);
 trace.after(18, args, 0, pc);
}
void STDMETHODCALLTYPE Device8::GetGammaRamp(D3DGAMMARAMP * pRamp) {
 auto guard = trace.guard();
 const auto args = pack(pRamp);
 const auto pc = reinterpret_cast<uintptr_t>(_ReturnAddress());
 trace.before(19, args, pc);
 real_->GetGammaRamp(pRamp);
 trace.after(19, args, 0, pc);
}
HRESULT STDMETHODCALLTYPE Device8::CreateTexture(UINT Width,UINT Height,UINT Levels,DWORD Usage,D3DFORMAT Format,D3DPOOL Pool,IDirect3DTexture8 ** ppTexture) {
 auto guard = trace.guard();
 const auto args = pack(Width, Height, Levels, Usage, Format, Pool, ppTexture);
 const auto pc = reinterpret_cast<uintptr_t>(_ReturnAddress());
 trace.before(20, args, pc);
 HRESULT result = real_->CreateTexture(Width, Height, Levels, Usage, Format, Pool, ppTexture);
 trace.after(20, args, static_cast<uint32_t>(result), pc);
 return result;
}
HRESULT STDMETHODCALLTYPE Device8::CreateVolumeTexture(UINT Width,UINT Height,UINT Depth,UINT Levels,DWORD Usage,D3DFORMAT Format,D3DPOOL Pool,IDirect3DVolumeTexture8 ** ppVolumeTexture) {
 auto guard = trace.guard();
 const auto args = pack(Width, Height, Depth, Levels, Usage, Format, Pool, ppVolumeTexture);
 const auto pc = reinterpret_cast<uintptr_t>(_ReturnAddress());
 trace.before(21, args, pc);
 HRESULT result = real_->CreateVolumeTexture(Width, Height, Depth, Levels, Usage, Format, Pool, ppVolumeTexture);
 trace.after(21, args, static_cast<uint32_t>(result), pc);
 return result;
}
HRESULT STDMETHODCALLTYPE Device8::CreateCubeTexture(UINT EdgeLength,UINT Levels,DWORD Usage,D3DFORMAT Format,D3DPOOL Pool,IDirect3DCubeTexture8 ** ppCubeTexture) {
 auto guard = trace.guard();
 const auto args = pack(EdgeLength, Levels, Usage, Format, Pool, ppCubeTexture);
 const auto pc = reinterpret_cast<uintptr_t>(_ReturnAddress());
 trace.before(22, args, pc);
 HRESULT result = real_->CreateCubeTexture(EdgeLength, Levels, Usage, Format, Pool, ppCubeTexture);
 trace.after(22, args, static_cast<uint32_t>(result), pc);
 return result;
}
HRESULT STDMETHODCALLTYPE Device8::CreateVertexBuffer(UINT Length,DWORD Usage,DWORD FVF,D3DPOOL Pool,IDirect3DVertexBuffer8 ** ppVertexBuffer) {
 auto guard = trace.guard();
 const auto args = pack(Length, Usage, FVF, Pool, ppVertexBuffer);
 const auto pc = reinterpret_cast<uintptr_t>(_ReturnAddress());
 trace.before(23, args, pc);
 HRESULT result = real_->CreateVertexBuffer(Length, Usage, FVF, Pool, ppVertexBuffer);
 trace.after(23, args, static_cast<uint32_t>(result), pc);
 return result;
}
HRESULT STDMETHODCALLTYPE Device8::CreateIndexBuffer(UINT Length,DWORD Usage,D3DFORMAT Format,D3DPOOL Pool,IDirect3DIndexBuffer8 ** ppIndexBuffer) {
 auto guard = trace.guard();
 const auto args = pack(Length, Usage, Format, Pool, ppIndexBuffer);
 const auto pc = reinterpret_cast<uintptr_t>(_ReturnAddress());
 trace.before(24, args, pc);
 HRESULT result = real_->CreateIndexBuffer(Length, Usage, Format, Pool, ppIndexBuffer);
 trace.after(24, args, static_cast<uint32_t>(result), pc);
 return result;
}
HRESULT STDMETHODCALLTYPE Device8::CreateRenderTarget(UINT Width,UINT Height,D3DFORMAT Format,D3DMULTISAMPLE_TYPE MultiSample,WINBOOL Lockable,IDirect3DSurface8 ** ppSurface) {
 auto guard = trace.guard();
 const auto args = pack(Width, Height, Format, MultiSample, Lockable, ppSurface);
 const auto pc = reinterpret_cast<uintptr_t>(_ReturnAddress());
 trace.before(25, args, pc);
 HRESULT result = real_->CreateRenderTarget(Width, Height, Format, MultiSample, Lockable, ppSurface);
 trace.after(25, args, static_cast<uint32_t>(result), pc);
 return result;
}
HRESULT STDMETHODCALLTYPE Device8::CreateDepthStencilSurface(UINT Width,UINT Height,D3DFORMAT Format,D3DMULTISAMPLE_TYPE MultiSample,IDirect3DSurface8 ** ppSurface) {
 auto guard = trace.guard();
 const auto args = pack(Width, Height, Format, MultiSample, ppSurface);
 const auto pc = reinterpret_cast<uintptr_t>(_ReturnAddress());
 trace.before(26, args, pc);
 HRESULT result = real_->CreateDepthStencilSurface(Width, Height, Format, MultiSample, ppSurface);
 trace.after(26, args, static_cast<uint32_t>(result), pc);
 return result;
}
HRESULT STDMETHODCALLTYPE Device8::CreateImageSurface(UINT Width,UINT Height,D3DFORMAT Format,IDirect3DSurface8 ** ppSurface) {
 auto guard = trace.guard();
 const auto args = pack(Width, Height, Format, ppSurface);
 const auto pc = reinterpret_cast<uintptr_t>(_ReturnAddress());
 trace.before(27, args, pc);
 HRESULT result = real_->CreateImageSurface(Width, Height, Format, ppSurface);
 trace.after(27, args, static_cast<uint32_t>(result), pc);
 return result;
}
HRESULT STDMETHODCALLTYPE Device8::CopyRects(IDirect3DSurface8 *src_surface, const RECT *src_rects, UINT rect_count, IDirect3DSurface8 *dst_surface, const POINT *dst_points) {
 auto guard = trace.guard();
 const auto args = pack(src_surface, src_rects, rect_count, dst_surface, dst_points);
 const auto pc = reinterpret_cast<uintptr_t>(_ReturnAddress());
 trace.before(28, args, pc);
 HRESULT result = real_->CopyRects(src_surface, src_rects, rect_count, dst_surface, dst_points);
 trace.after(28, args, static_cast<uint32_t>(result), pc);
 return result;
}
HRESULT STDMETHODCALLTYPE Device8::UpdateTexture(IDirect3DBaseTexture8 * pSourceTexture,IDirect3DBaseTexture8 * pDestinationTexture) {
 auto guard = trace.guard();
 const auto args = pack(pSourceTexture, pDestinationTexture);
 const auto pc = reinterpret_cast<uintptr_t>(_ReturnAddress());
 trace.before(29, args, pc);
 HRESULT result = real_->UpdateTexture(pSourceTexture, pDestinationTexture);
 trace.after(29, args, static_cast<uint32_t>(result), pc);
 return result;
}
HRESULT STDMETHODCALLTYPE Device8::GetFrontBuffer(IDirect3DSurface8 * pDestSurface) {
 auto guard = trace.guard();
 const auto args = pack(pDestSurface);
 const auto pc = reinterpret_cast<uintptr_t>(_ReturnAddress());
 trace.before(30, args, pc);
 HRESULT result = real_->GetFrontBuffer(pDestSurface);
 trace.after(30, args, static_cast<uint32_t>(result), pc);
 return result;
}
HRESULT STDMETHODCALLTYPE Device8::SetRenderTarget(IDirect3DSurface8 * pRenderTarget,IDirect3DSurface8 * pNewZStencil) {
 auto guard = trace.guard();
 const auto args = pack(pRenderTarget, pNewZStencil);
 const auto pc = reinterpret_cast<uintptr_t>(_ReturnAddress());
 trace.before(31, args, pc);
 HRESULT result = real_->SetRenderTarget(pRenderTarget, pNewZStencil);
 trace.after(31, args, static_cast<uint32_t>(result), pc);
 return result;
}
HRESULT STDMETHODCALLTYPE Device8::GetRenderTarget(IDirect3DSurface8 ** ppRenderTarget) {
 auto guard = trace.guard();
 const auto args = pack(ppRenderTarget);
 const auto pc = reinterpret_cast<uintptr_t>(_ReturnAddress());
 trace.before(32, args, pc);
 HRESULT result = real_->GetRenderTarget(ppRenderTarget);
 trace.after(32, args, static_cast<uint32_t>(result), pc);
 return result;
}
HRESULT STDMETHODCALLTYPE Device8::GetDepthStencilSurface(IDirect3DSurface8 ** ppZStencilSurface) {
 auto guard = trace.guard();
 const auto args = pack(ppZStencilSurface);
 const auto pc = reinterpret_cast<uintptr_t>(_ReturnAddress());
 trace.before(33, args, pc);
 HRESULT result = real_->GetDepthStencilSurface(ppZStencilSurface);
 trace.after(33, args, static_cast<uint32_t>(result), pc);
 return result;
}
HRESULT STDMETHODCALLTYPE Device8::BeginScene() {
 auto guard = trace.guard();
 const auto args = pack();
 const auto pc = reinterpret_cast<uintptr_t>(_ReturnAddress());
 trace.before(34, args, pc);
 HRESULT result = real_->BeginScene();
 trace.after(34, args, static_cast<uint32_t>(result), pc);
 return result;
}
HRESULT STDMETHODCALLTYPE Device8::EndScene() {
 auto guard = trace.guard();
 const auto args = pack();
 const auto pc = reinterpret_cast<uintptr_t>(_ReturnAddress());
 trace.before(35, args, pc);
 HRESULT result = real_->EndScene();
 trace.after(35, args, static_cast<uint32_t>(result), pc);
 return result;
}
HRESULT STDMETHODCALLTYPE Device8::Clear(DWORD rect_count, const D3DRECT *rects, DWORD flags, D3DCOLOR color, float z, DWORD stencil) {
 auto guard = trace.guard();
 const auto args = pack(rect_count, rects, flags, color, z, stencil);
 const auto pc = reinterpret_cast<uintptr_t>(_ReturnAddress());
 trace.before(36, args, pc);
 HRESULT result = real_->Clear(rect_count, rects, flags, color, z, stencil);
 trace.after(36, args, static_cast<uint32_t>(result), pc);
 return result;
}
HRESULT STDMETHODCALLTYPE Device8::MultiplyTransform(D3DTRANSFORMSTATETYPE state, const D3DMATRIX *matrix) {
 auto guard = trace.guard();
 const auto args = pack(state, matrix);
 const auto pc = reinterpret_cast<uintptr_t>(_ReturnAddress());
 trace.before(39, args, pc);
 if(state==D3DTS_PROJECTION){HRESULT safe=stock_for_unmapped("MultiplyTransform_PROJECTION");if(FAILED(safe)){trace.after(39,args,static_cast<uint32_t>(safe),pc);return safe;}}
 HRESULT result = real_->MultiplyTransform(state, matrix);
 trace.after(39, args, static_cast<uint32_t>(result), pc);
 return result;
}
HRESULT STDMETHODCALLTYPE Device8::SetViewport(const D3DVIEWPORT8 *viewport) {
 auto guard = trace.guard();
 const auto args = pack(viewport);
 const auto pc = reinterpret_cast<uintptr_t>(_ReturnAddress());
 trace.before(40, args, pc);
 HRESULT result = real_->SetViewport(viewport);
 trace.after(40, args, static_cast<uint32_t>(result), pc);
 return result;
}
HRESULT STDMETHODCALLTYPE Device8::GetViewport(D3DVIEWPORT8 * pViewport) {
 auto guard = trace.guard();
 const auto args = pack(pViewport);
 const auto pc = reinterpret_cast<uintptr_t>(_ReturnAddress());
 trace.before(41, args, pc);
 HRESULT result = real_->GetViewport(pViewport);
 trace.after(41, args, static_cast<uint32_t>(result), pc);
 return result;
}
HRESULT STDMETHODCALLTYPE Device8::SetMaterial(const D3DMATERIAL8 *material) {
 auto guard = trace.guard();
 const auto args = pack(material);
 const auto pc = reinterpret_cast<uintptr_t>(_ReturnAddress());
 trace.before(42, args, pc);
 HRESULT result = real_->SetMaterial(material);
 trace.after(42, args, static_cast<uint32_t>(result), pc);
 return result;
}
HRESULT STDMETHODCALLTYPE Device8::GetMaterial(D3DMATERIAL8 *pMaterial) {
 auto guard = trace.guard();
 const auto args = pack(pMaterial);
 const auto pc = reinterpret_cast<uintptr_t>(_ReturnAddress());
 trace.before(43, args, pc);
 HRESULT result = real_->GetMaterial(pMaterial);
 trace.after(43, args, static_cast<uint32_t>(result), pc);
 return result;
}
HRESULT STDMETHODCALLTYPE Device8::SetLight(DWORD index, const D3DLIGHT8 *light) {
 auto guard = trace.guard();
 const auto args = pack(index, light);
 const auto pc = reinterpret_cast<uintptr_t>(_ReturnAddress());
 trace.before(44, args, pc);
 HRESULT result = real_->SetLight(index, light);
 trace.after(44, args, static_cast<uint32_t>(result), pc);
 return result;
}
HRESULT STDMETHODCALLTYPE Device8::GetLight(DWORD Index,D3DLIGHT8 * pLight) {
 auto guard = trace.guard();
 const auto args = pack(Index, pLight);
 const auto pc = reinterpret_cast<uintptr_t>(_ReturnAddress());
 trace.before(45, args, pc);
 HRESULT result = real_->GetLight(Index, pLight);
 trace.after(45, args, static_cast<uint32_t>(result), pc);
 return result;
}
HRESULT STDMETHODCALLTYPE Device8::LightEnable(DWORD Index,WINBOOL Enable) {
 auto guard = trace.guard();
 const auto args = pack(Index, Enable);
 const auto pc = reinterpret_cast<uintptr_t>(_ReturnAddress());
 trace.before(46, args, pc);
 HRESULT result = real_->LightEnable(Index, Enable);
 trace.after(46, args, static_cast<uint32_t>(result), pc);
 return result;
}
HRESULT STDMETHODCALLTYPE Device8::GetLightEnable(DWORD Index,WINBOOL * pEnable) {
 auto guard = trace.guard();
 const auto args = pack(Index, pEnable);
 const auto pc = reinterpret_cast<uintptr_t>(_ReturnAddress());
 trace.before(47, args, pc);
 HRESULT result = real_->GetLightEnable(Index, pEnable);
 trace.after(47, args, static_cast<uint32_t>(result), pc);
 return result;
}
HRESULT STDMETHODCALLTYPE Device8::SetClipPlane(DWORD index, const float *plane) {
 auto guard = trace.guard();
 const auto args = pack(index, plane);
 const auto pc = reinterpret_cast<uintptr_t>(_ReturnAddress());
 trace.before(48, args, pc);
 HRESULT result = real_->SetClipPlane(index, plane);
 trace.after(48, args, static_cast<uint32_t>(result), pc);
 return result;
}
HRESULT STDMETHODCALLTYPE Device8::GetClipPlane(DWORD Index,float * pPlane) {
 auto guard = trace.guard();
 const auto args = pack(Index, pPlane);
 const auto pc = reinterpret_cast<uintptr_t>(_ReturnAddress());
 trace.before(49, args, pc);
 HRESULT result = real_->GetClipPlane(Index, pPlane);
 trace.after(49, args, static_cast<uint32_t>(result), pc);
 return result;
}
HRESULT STDMETHODCALLTYPE Device8::SetRenderState(D3DRENDERSTATETYPE State,DWORD Value) {
 auto guard = trace.guard();
 const auto args = pack(State, Value);
 const auto pc = reinterpret_cast<uintptr_t>(_ReturnAddress());
 trace.before(50, args, pc);
 HRESULT result = real_->SetRenderState(State, Value);
 trace.after(50, args, static_cast<uint32_t>(result), pc);
 return result;
}
HRESULT STDMETHODCALLTYPE Device8::GetRenderState(D3DRENDERSTATETYPE State,DWORD * pValue) {
 auto guard = trace.guard();
 const auto args = pack(State, pValue);
 const auto pc = reinterpret_cast<uintptr_t>(_ReturnAddress());
 trace.before(51, args, pc);
 HRESULT result = real_->GetRenderState(State, pValue);
 trace.after(51, args, static_cast<uint32_t>(result), pc);
 return result;
}
HRESULT STDMETHODCALLTYPE Device8::BeginStateBlock() {
 auto guard = trace.guard();
 const auto args = pack();
 const auto pc = reinterpret_cast<uintptr_t>(_ReturnAddress());
 trace.before(52, args, pc);
 HRESULT safe = stock_for_unmapped("BeginStateBlock");
 if(FAILED(safe)){ trace.after(52, args, static_cast<uint32_t>(safe), pc); return safe; }
 HRESULT result = real_->BeginStateBlock();
 trace.after(52, args, static_cast<uint32_t>(result), pc);
 return result;
}
HRESULT STDMETHODCALLTYPE Device8::EndStateBlock(DWORD * pToken) {
 auto guard = trace.guard();
 const auto args = pack(pToken);
 const auto pc = reinterpret_cast<uintptr_t>(_ReturnAddress());
 trace.before(53, args, pc);
 HRESULT result = real_->EndStateBlock(pToken);
 trace.after(53, args, static_cast<uint32_t>(result), pc);
 return result;
}
HRESULT STDMETHODCALLTYPE Device8::ApplyStateBlock(DWORD Token) {
 auto guard = trace.guard();
 const auto args = pack(Token);
 const auto pc = reinterpret_cast<uintptr_t>(_ReturnAddress());
 trace.before(54, args, pc);
 HRESULT safe = stock_for_unmapped("ApplyStateBlock");
 if(FAILED(safe)){ trace.after(54, args, static_cast<uint32_t>(safe), pc); return safe; }
 HRESULT result = real_->ApplyStateBlock(Token);
 trace.after(54, args, static_cast<uint32_t>(result), pc);
 return result;
}
HRESULT STDMETHODCALLTYPE Device8::CaptureStateBlock(DWORD Token) {
 auto guard = trace.guard();
 const auto args = pack(Token);
 const auto pc = reinterpret_cast<uintptr_t>(_ReturnAddress());
 trace.before(55, args, pc);
 HRESULT safe = stock_for_unmapped("CaptureStateBlock");
 if(FAILED(safe)){ trace.after(55, args, static_cast<uint32_t>(safe), pc); return safe; }
 HRESULT result = real_->CaptureStateBlock(Token);
 trace.after(55, args, static_cast<uint32_t>(result), pc);
 return result;
}
HRESULT STDMETHODCALLTYPE Device8::DeleteStateBlock(DWORD Token) {
 auto guard = trace.guard();
 const auto args = pack(Token);
 const auto pc = reinterpret_cast<uintptr_t>(_ReturnAddress());
 trace.before(56, args, pc);
 HRESULT result = real_->DeleteStateBlock(Token);
 trace.after(56, args, static_cast<uint32_t>(result), pc);
 return result;
}
HRESULT STDMETHODCALLTYPE Device8::CreateStateBlock(D3DSTATEBLOCKTYPE Type,DWORD * pToken) {
 auto guard = trace.guard();
 const auto args = pack(Type, pToken);
 const auto pc = reinterpret_cast<uintptr_t>(_ReturnAddress());
 trace.before(57, args, pc);
 HRESULT safe = stock_for_unmapped("CreateStateBlock");
 if(FAILED(safe)){ trace.after(57, args, static_cast<uint32_t>(safe), pc); return safe; }
 HRESULT result = real_->CreateStateBlock(Type, pToken);
 trace.after(57, args, static_cast<uint32_t>(result), pc);
 return result;
}
HRESULT STDMETHODCALLTYPE Device8::SetClipStatus(const D3DCLIPSTATUS8 *clip_status) {
 auto guard = trace.guard();
 const auto args = pack(clip_status);
 const auto pc = reinterpret_cast<uintptr_t>(_ReturnAddress());
 trace.before(58, args, pc);
 HRESULT result = real_->SetClipStatus(clip_status);
 trace.after(58, args, static_cast<uint32_t>(result), pc);
 return result;
}
HRESULT STDMETHODCALLTYPE Device8::GetClipStatus(D3DCLIPSTATUS8 * pClipStatus) {
 auto guard = trace.guard();
 const auto args = pack(pClipStatus);
 const auto pc = reinterpret_cast<uintptr_t>(_ReturnAddress());
 trace.before(59, args, pc);
 HRESULT result = real_->GetClipStatus(pClipStatus);
 trace.after(59, args, static_cast<uint32_t>(result), pc);
 return result;
}
HRESULT STDMETHODCALLTYPE Device8::GetTexture(DWORD Stage,IDirect3DBaseTexture8 ** ppTexture) {
 auto guard = trace.guard();
 const auto args = pack(Stage, ppTexture);
 const auto pc = reinterpret_cast<uintptr_t>(_ReturnAddress());
 trace.before(60, args, pc);
 HRESULT result = real_->GetTexture(Stage, ppTexture);
 trace.after(60, args, static_cast<uint32_t>(result), pc);
 return result;
}
HRESULT STDMETHODCALLTYPE Device8::SetTexture(DWORD Stage,IDirect3DBaseTexture8 * pTexture) {
 auto guard = trace.guard();
 const auto args = pack(Stage, pTexture);
 const auto pc = reinterpret_cast<uintptr_t>(_ReturnAddress());
 trace.before(61, args, pc);
 HRESULT result = real_->SetTexture(Stage, pTexture);
 trace.after(61, args, static_cast<uint32_t>(result), pc);
 return result;
}
HRESULT STDMETHODCALLTYPE Device8::ValidateDevice(DWORD * pNumPasses) {
 auto guard = trace.guard();
 const auto args = pack(pNumPasses);
 const auto pc = reinterpret_cast<uintptr_t>(_ReturnAddress());
 trace.before(64, args, pc);
 HRESULT result = real_->ValidateDevice(pNumPasses);
 trace.after(64, args, static_cast<uint32_t>(result), pc);
 return result;
}
HRESULT STDMETHODCALLTYPE Device8::GetInfo(DWORD DevInfoID,void * pDevInfoStruct,DWORD DevInfoStructSize) {
 auto guard = trace.guard();
 const auto args = pack(DevInfoID, pDevInfoStruct, DevInfoStructSize);
 const auto pc = reinterpret_cast<uintptr_t>(_ReturnAddress());
 trace.before(65, args, pc);
 HRESULT result = real_->GetInfo(DevInfoID, pDevInfoStruct, DevInfoStructSize);
 trace.after(65, args, static_cast<uint32_t>(result), pc);
 return result;
}
HRESULT STDMETHODCALLTYPE Device8::SetPaletteEntries(UINT palette_idx, const PALETTEENTRY *entries) {
 auto guard = trace.guard();
 const auto args = pack(palette_idx, entries);
 const auto pc = reinterpret_cast<uintptr_t>(_ReturnAddress());
 trace.before(66, args, pc);
 HRESULT result = real_->SetPaletteEntries(palette_idx, entries);
 trace.after(66, args, static_cast<uint32_t>(result), pc);
 return result;
}
HRESULT STDMETHODCALLTYPE Device8::GetPaletteEntries(UINT PaletteNumber,PALETTEENTRY * pEntries) {
 auto guard = trace.guard();
 const auto args = pack(PaletteNumber, pEntries);
 const auto pc = reinterpret_cast<uintptr_t>(_ReturnAddress());
 trace.before(67, args, pc);
 HRESULT result = real_->GetPaletteEntries(PaletteNumber, pEntries);
 trace.after(67, args, static_cast<uint32_t>(result), pc);
 return result;
}
HRESULT STDMETHODCALLTYPE Device8::SetCurrentTexturePalette(UINT PaletteNumber) {
 auto guard = trace.guard();
 const auto args = pack(PaletteNumber);
 const auto pc = reinterpret_cast<uintptr_t>(_ReturnAddress());
 trace.before(68, args, pc);
 HRESULT result = real_->SetCurrentTexturePalette(PaletteNumber);
 trace.after(68, args, static_cast<uint32_t>(result), pc);
 return result;
}
HRESULT STDMETHODCALLTYPE Device8::GetCurrentTexturePalette(UINT * PaletteNumber) {
 auto guard = trace.guard();
 const auto args = pack(PaletteNumber);
 const auto pc = reinterpret_cast<uintptr_t>(_ReturnAddress());
 trace.before(69, args, pc);
 HRESULT result = real_->GetCurrentTexturePalette(PaletteNumber);
 trace.after(69, args, static_cast<uint32_t>(result), pc);
 return result;
}
HRESULT STDMETHODCALLTYPE Device8::DrawPrimitiveUP(D3DPRIMITIVETYPE primitive_type, UINT primitive_count, const void *data, UINT stride) {
 auto guard = trace.guard();
 const auto args = pack(primitive_type, primitive_count, data, stride);
 const auto pc = reinterpret_cast<uintptr_t>(_ReturnAddress());
 trace.before(72, args, pc);
 HRESULT repair=repair_reflection();
 if(FAILED(repair)){trace.after(72,args,static_cast<uint32_t>(repair),pc,nullptr,8,true);return repair;}
 HRESULT result = real_->DrawPrimitiveUP(primitive_type, primitive_count, data, stride);
 trace.after(72, args, static_cast<uint32_t>(result), pc);
 return result;
}
HRESULT STDMETHODCALLTYPE Device8::DrawIndexedPrimitiveUP(D3DPRIMITIVETYPE primitive_type, UINT min_vertex_idx, UINT vertex_count, UINT primitive_count, const void *index_data, D3DFORMAT index_format, const void *data, UINT stride) {
 auto guard = trace.guard();
 const auto args = pack(primitive_type, min_vertex_idx, vertex_count, primitive_count, index_data, index_format, data, stride);
 const auto pc = reinterpret_cast<uintptr_t>(_ReturnAddress());
 trace.before(73, args, pc);
 HRESULT repair=repair_reflection();
 if(FAILED(repair)){trace.after(73,args,static_cast<uint32_t>(repair),pc,nullptr,8,true);return repair;}
 HRESULT result = real_->DrawIndexedPrimitiveUP(primitive_type, min_vertex_idx, vertex_count, primitive_count, index_data, index_format, data, stride);
 trace.after(73, args, static_cast<uint32_t>(result), pc);
 return result;
}
HRESULT STDMETHODCALLTYPE Device8::ProcessVertices(UINT SrcStartIndex,UINT DestIndex,UINT VertexCount,IDirect3DVertexBuffer8 * pDestBuffer,DWORD Flags) {
 auto guard = trace.guard();
 const auto args = pack(SrcStartIndex, DestIndex, VertexCount, pDestBuffer, Flags);
 const auto pc = reinterpret_cast<uintptr_t>(_ReturnAddress());
 trace.before(74, args, pc);
 HRESULT result = real_->ProcessVertices(SrcStartIndex, DestIndex, VertexCount, pDestBuffer, Flags);
 trace.after(74, args, static_cast<uint32_t>(result), pc);
 return result;
}
HRESULT STDMETHODCALLTYPE Device8::CreateVertexShader(const DWORD *declaration, const DWORD *byte_code, DWORD *shader, DWORD usage) {
 auto guard = trace.guard();
 const auto args = pack(declaration, byte_code, shader, usage);
 const auto pc = reinterpret_cast<uintptr_t>(_ReturnAddress());
 trace.before(75, args, pc);
 HRESULT result = real_->CreateVertexShader(declaration, byte_code, shader, usage);
 trace.after(75, args, static_cast<uint32_t>(result), pc);
 return result;
}
HRESULT STDMETHODCALLTYPE Device8::SetVertexShader(DWORD Handle) {
 auto guard = trace.guard();
 const auto args = pack(Handle);
 const auto pc = reinterpret_cast<uintptr_t>(_ReturnAddress());
 trace.before(76, args, pc);
 HRESULT result = real_->SetVertexShader(Handle);
 trace.after(76, args, static_cast<uint32_t>(result), pc);
 return result;
}
HRESULT STDMETHODCALLTYPE Device8::GetVertexShader(DWORD * pHandle) {
 auto guard = trace.guard();
 const auto args = pack(pHandle);
 const auto pc = reinterpret_cast<uintptr_t>(_ReturnAddress());
 trace.before(77, args, pc);
 HRESULT result = real_->GetVertexShader(pHandle);
 trace.after(77, args, static_cast<uint32_t>(result), pc);
 return result;
}
HRESULT STDMETHODCALLTYPE Device8::DeleteVertexShader(DWORD Handle) {
 auto guard = trace.guard();
 const auto args = pack(Handle);
 const auto pc = reinterpret_cast<uintptr_t>(_ReturnAddress());
 trace.before(78, args, pc);
 HRESULT result = real_->DeleteVertexShader(Handle);
 trace.after(78, args, static_cast<uint32_t>(result), pc);
 return result;
}
HRESULT STDMETHODCALLTYPE Device8::SetVertexShaderConstant(DWORD reg_idx, const void *data, DWORD count) {
 auto guard = trace.guard();
 const auto args = pack(reg_idx, data, count);
 const auto pc = reinterpret_cast<uintptr_t>(_ReturnAddress());
 trace.before(79, args, pc);
 HRESULT result = real_->SetVertexShaderConstant(reg_idx, data, count);
 trace.after(79, args, static_cast<uint32_t>(result), pc);
 return result;
}
HRESULT STDMETHODCALLTYPE Device8::GetVertexShaderConstant(DWORD Register,void * pConstantData,DWORD ConstantCount) {
 auto guard = trace.guard();
 const auto args = pack(Register, pConstantData, ConstantCount);
 const auto pc = reinterpret_cast<uintptr_t>(_ReturnAddress());
 trace.before(80, args, pc);
 HRESULT result = real_->GetVertexShaderConstant(Register, pConstantData, ConstantCount);
 trace.after(80, args, static_cast<uint32_t>(result), pc);
 return result;
}
HRESULT STDMETHODCALLTYPE Device8::GetVertexShaderDeclaration(DWORD Handle,void * pData,DWORD * pSizeOfData) {
 auto guard = trace.guard();
 const auto args = pack(Handle, pData, pSizeOfData);
 const auto pc = reinterpret_cast<uintptr_t>(_ReturnAddress());
 trace.before(81, args, pc);
 HRESULT result = real_->GetVertexShaderDeclaration(Handle, pData, pSizeOfData);
 trace.after(81, args, static_cast<uint32_t>(result), pc);
 return result;
}
HRESULT STDMETHODCALLTYPE Device8::GetVertexShaderFunction(DWORD Handle,void * pData,DWORD * pSizeOfData) {
 auto guard = trace.guard();
 const auto args = pack(Handle, pData, pSizeOfData);
 const auto pc = reinterpret_cast<uintptr_t>(_ReturnAddress());
 trace.before(82, args, pc);
 HRESULT result = real_->GetVertexShaderFunction(Handle, pData, pSizeOfData);
 trace.after(82, args, static_cast<uint32_t>(result), pc);
 return result;
}
HRESULT STDMETHODCALLTYPE Device8::SetStreamSource(UINT StreamNumber,IDirect3DVertexBuffer8 * pStreamData,UINT Stride) {
 auto guard = trace.guard();
 const auto args = pack(StreamNumber, pStreamData, Stride);
 const auto pc = reinterpret_cast<uintptr_t>(_ReturnAddress());
 trace.before(83, args, pc);
 HRESULT result = real_->SetStreamSource(StreamNumber, pStreamData, Stride);
 trace.after(83, args, static_cast<uint32_t>(result), pc);
 return result;
}
HRESULT STDMETHODCALLTYPE Device8::GetStreamSource(UINT StreamNumber,IDirect3DVertexBuffer8 ** ppStreamData,UINT * pStride) {
 auto guard = trace.guard();
 const auto args = pack(StreamNumber, ppStreamData, pStride);
 const auto pc = reinterpret_cast<uintptr_t>(_ReturnAddress());
 trace.before(84, args, pc);
 HRESULT result = real_->GetStreamSource(StreamNumber, ppStreamData, pStride);
 trace.after(84, args, static_cast<uint32_t>(result), pc);
 return result;
}
HRESULT STDMETHODCALLTYPE Device8::SetIndices(IDirect3DIndexBuffer8 * pIndexData,UINT BaseVertexIndex) {
 auto guard = trace.guard();
 const auto args = pack(pIndexData, BaseVertexIndex);
 const auto pc = reinterpret_cast<uintptr_t>(_ReturnAddress());
 trace.before(85, args, pc);
 HRESULT result = real_->SetIndices(pIndexData, BaseVertexIndex);
 trace.after(85, args, static_cast<uint32_t>(result), pc);
 return result;
}
HRESULT STDMETHODCALLTYPE Device8::GetIndices(IDirect3DIndexBuffer8 ** ppIndexData,UINT * pBaseVertexIndex) {
 auto guard = trace.guard();
 const auto args = pack(ppIndexData, pBaseVertexIndex);
 const auto pc = reinterpret_cast<uintptr_t>(_ReturnAddress());
 trace.before(86, args, pc);
 HRESULT result = real_->GetIndices(ppIndexData, pBaseVertexIndex);
 trace.after(86, args, static_cast<uint32_t>(result), pc);
 return result;
}
HRESULT STDMETHODCALLTYPE Device8::CreatePixelShader(const DWORD *byte_code, DWORD *shader) {
 auto guard = trace.guard();
 const auto args = pack(byte_code, shader);
 const auto pc = reinterpret_cast<uintptr_t>(_ReturnAddress());
 trace.before(87, args, pc);
 HRESULT result = real_->CreatePixelShader(byte_code, shader);
 trace.after(87, args, static_cast<uint32_t>(result), pc);
 return result;
}
HRESULT STDMETHODCALLTYPE Device8::SetPixelShader(DWORD Handle) {
 auto guard = trace.guard();
 const auto args = pack(Handle);
 const auto pc = reinterpret_cast<uintptr_t>(_ReturnAddress());
 trace.before(88, args, pc);
 HRESULT result = real_->SetPixelShader(Handle);
 trace.after(88, args, static_cast<uint32_t>(result), pc);
 return result;
}
HRESULT STDMETHODCALLTYPE Device8::GetPixelShader(DWORD * pHandle) {
 auto guard = trace.guard();
 const auto args = pack(pHandle);
 const auto pc = reinterpret_cast<uintptr_t>(_ReturnAddress());
 trace.before(89, args, pc);
 HRESULT result = real_->GetPixelShader(pHandle);
 trace.after(89, args, static_cast<uint32_t>(result), pc);
 return result;
}
HRESULT STDMETHODCALLTYPE Device8::DeletePixelShader(DWORD Handle) {
 auto guard = trace.guard();
 const auto args = pack(Handle);
 const auto pc = reinterpret_cast<uintptr_t>(_ReturnAddress());
 trace.before(90, args, pc);
 HRESULT result = real_->DeletePixelShader(Handle);
 trace.after(90, args, static_cast<uint32_t>(result), pc);
 return result;
}
HRESULT STDMETHODCALLTYPE Device8::SetPixelShaderConstant(DWORD reg_idx, const void *data, DWORD count) {
 auto guard = trace.guard();
 const auto args = pack(reg_idx, data, count);
 const auto pc = reinterpret_cast<uintptr_t>(_ReturnAddress());
 trace.before(91, args, pc);
 HRESULT result = real_->SetPixelShaderConstant(reg_idx, data, count);
 trace.after(91, args, static_cast<uint32_t>(result), pc);
 return result;
}
HRESULT STDMETHODCALLTYPE Device8::GetPixelShaderConstant(DWORD Register,void * pConstantData,DWORD ConstantCount) {
 auto guard = trace.guard();
 const auto args = pack(Register, pConstantData, ConstantCount);
 const auto pc = reinterpret_cast<uintptr_t>(_ReturnAddress());
 trace.before(92, args, pc);
 HRESULT result = real_->GetPixelShaderConstant(Register, pConstantData, ConstantCount);
 trace.after(92, args, static_cast<uint32_t>(result), pc);
 return result;
}
HRESULT STDMETHODCALLTYPE Device8::GetPixelShaderFunction(DWORD Handle,void * pData,DWORD * pSizeOfData) {
 auto guard = trace.guard();
 const auto args = pack(Handle, pData, pSizeOfData);
 const auto pc = reinterpret_cast<uintptr_t>(_ReturnAddress());
 trace.before(93, args, pc);
 HRESULT result = real_->GetPixelShaderFunction(Handle, pData, pSizeOfData);
 trace.after(93, args, static_cast<uint32_t>(result), pc);
 return result;
}
HRESULT STDMETHODCALLTYPE Device8::DrawRectPatch(UINT handle, const float *segment_count, const D3DRECTPATCH_INFO *patch_info) {
 auto guard = trace.guard();
 const auto args = pack(handle, segment_count, patch_info);
 const auto pc = reinterpret_cast<uintptr_t>(_ReturnAddress());
 trace.before(94, args, pc);
 HRESULT result = real_->DrawRectPatch(handle, segment_count, patch_info);
 trace.after(94, args, static_cast<uint32_t>(result), pc);
 return result;
}
HRESULT STDMETHODCALLTYPE Device8::DrawTriPatch(UINT handle, const float *segment_count, const D3DTRIPATCH_INFO *patch_info) {
 auto guard = trace.guard();
 const auto args = pack(handle, segment_count, patch_info);
 const auto pc = reinterpret_cast<uintptr_t>(_ReturnAddress());
 trace.before(95, args, pc);
 HRESULT result = real_->DrawTriPatch(handle, segment_count, patch_info);
 trace.after(95, args, static_cast<uint32_t>(result), pc);
 return result;
}
HRESULT STDMETHODCALLTYPE Device8::DeletePatch(UINT Handle) {
 auto guard = trace.guard();
 const auto args = pack(Handle);
 const auto pc = reinterpret_cast<uintptr_t>(_ReturnAddress());
 trace.before(96, args, pc);
 HRESULT result = real_->DeletePatch(Handle);
 trace.after(96, args, static_cast<uint32_t>(result), pc);
 return result;
}
}
