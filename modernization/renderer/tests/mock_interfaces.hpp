// Generated ABI-wide mock methods and invocation tests.
#pragma once
#include "wrappers.hpp"
namespace gfx2 {
class MockRootBase : public IDirect3D8 {
public:
 uint32_t last=UINT32_MAX; Args observed{};
 HRESULT hr=static_cast<HRESULT>(0x88761234u);
 HRESULT STDMETHODCALLTYPE QueryInterface(REFIID riid, void** ppvObject) override { last=0;return hr; }
 ULONG STDMETHODCALLTYPE AddRef() override { last=1;observed=pack();return 0x12345678; }
 ULONG STDMETHODCALLTYPE Release() override { last=2;observed=pack();return 0x12345678; }
 HRESULT STDMETHODCALLTYPE RegisterSoftwareDevice(void * pInitializeFunction) override { last=3;observed=pack(pInitializeFunction);return hr; }
 UINT STDMETHODCALLTYPE GetAdapterCount() override { last=4;observed=pack();return 0x12345678; }
 HRESULT STDMETHODCALLTYPE GetAdapterIdentifier(UINT Adapter, DWORD Flags, D3DADAPTER_IDENTIFIER8 * pIdentifier) override { last=5;observed=pack(Adapter, Flags, pIdentifier);return hr; }
 UINT STDMETHODCALLTYPE GetAdapterModeCount(UINT Adapter) override { last=6;observed=pack(Adapter);return 0x12345678; }
 HRESULT STDMETHODCALLTYPE EnumAdapterModes(UINT Adapter, UINT Mode, D3DDISPLAYMODE * pMode) override { last=7;observed=pack(Adapter, Mode, pMode);return hr; }
 HRESULT STDMETHODCALLTYPE GetAdapterDisplayMode(UINT Adapter, D3DDISPLAYMODE * pMode) override { last=8;observed=pack(Adapter, pMode);return hr; }
 HRESULT STDMETHODCALLTYPE CheckDeviceType(UINT Adapter, D3DDEVTYPE CheckType, D3DFORMAT DisplayFormat, D3DFORMAT BackBufferFormat, WINBOOL Windowed) override { last=9;observed=pack(Adapter, CheckType, DisplayFormat, BackBufferFormat, Windowed);return hr; }
 HRESULT STDMETHODCALLTYPE CheckDeviceFormat(UINT Adapter, D3DDEVTYPE DeviceType, D3DFORMAT AdapterFormat, DWORD Usage, D3DRESOURCETYPE RType, D3DFORMAT CheckFormat) override { last=10;observed=pack(Adapter, DeviceType, AdapterFormat, Usage, RType, CheckFormat);return hr; }
 HRESULT STDMETHODCALLTYPE CheckDeviceMultiSampleType(UINT Adapter, D3DDEVTYPE DeviceType, D3DFORMAT SurfaceFormat, WINBOOL Windowed, D3DMULTISAMPLE_TYPE MultiSampleType) override { last=11;observed=pack(Adapter, DeviceType, SurfaceFormat, Windowed, MultiSampleType);return hr; }
 HRESULT STDMETHODCALLTYPE CheckDepthStencilMatch(UINT Adapter, D3DDEVTYPE DeviceType, D3DFORMAT AdapterFormat, D3DFORMAT RenderTargetFormat, D3DFORMAT DepthStencilFormat) override { last=12;observed=pack(Adapter, DeviceType, AdapterFormat, RenderTargetFormat, DepthStencilFormat);return hr; }
 HRESULT STDMETHODCALLTYPE GetDeviceCaps(UINT Adapter, D3DDEVTYPE DeviceType, D3DCAPS8 * pCaps) override { last=13;observed=pack(Adapter, DeviceType, pCaps);return hr; }
 HMONITOR STDMETHODCALLTYPE GetAdapterMonitor(UINT Adapter) override { last=14;observed=pack(Adapter);return reinterpret_cast<HMONITOR>(0x12345678); }
 HRESULT STDMETHODCALLTYPE CreateDevice(UINT Adapter, D3DDEVTYPE DeviceType,HWND hFocusWindow, DWORD BehaviorFlags, D3DPRESENT_PARAMETERS * pPresentationParameters, struct IDirect3DDevice8 ** ppReturnedDeviceInterface) override { last=15;observed=pack(Adapter, DeviceType, hFocusWindow, BehaviorFlags, pPresentationParameters, ppReturnedDeviceInterface);return hr; }
};
class MockDeviceBase : public IDirect3DDevice8 {
public:
 uint32_t last=UINT32_MAX; Args observed{};
 HRESULT hr=static_cast<HRESULT>(0x88761234u);
 HRESULT STDMETHODCALLTYPE QueryInterface(REFIID riid, void** ppvObject) override { last=0;return hr; }
 ULONG STDMETHODCALLTYPE AddRef() override { last=1;observed=pack();return 0x12345678; }
 ULONG STDMETHODCALLTYPE Release() override { last=2;observed=pack();return 0x12345678; }
 HRESULT STDMETHODCALLTYPE TestCooperativeLevel() override { last=3;observed=pack();return hr; }
 UINT STDMETHODCALLTYPE GetAvailableTextureMem() override { last=4;observed=pack();return 0x12345678; }
 HRESULT STDMETHODCALLTYPE ResourceManagerDiscardBytes(DWORD Bytes) override { last=5;observed=pack(Bytes);return hr; }
 HRESULT STDMETHODCALLTYPE GetDirect3D(IDirect3D8 ** ppD3D8) override { last=6;observed=pack(ppD3D8);return hr; }
 HRESULT STDMETHODCALLTYPE GetDeviceCaps(D3DCAPS8 * pCaps) override { last=7;observed=pack(pCaps);return hr; }
 HRESULT STDMETHODCALLTYPE GetDisplayMode(D3DDISPLAYMODE * pMode) override { last=8;observed=pack(pMode);return hr; }
 HRESULT STDMETHODCALLTYPE GetCreationParameters(D3DDEVICE_CREATION_PARAMETERS * pParameters) override { last=9;observed=pack(pParameters);return hr; }
 HRESULT STDMETHODCALLTYPE SetCursorProperties(UINT XHotSpot, UINT YHotSpot, IDirect3DSurface8 * pCursorBitmap) override { last=10;observed=pack(XHotSpot, YHotSpot, pCursorBitmap);return hr; }
 void STDMETHODCALLTYPE SetCursorPosition(UINT XScreenSpace, UINT YScreenSpace,DWORD Flags) override { last=11;observed=pack(XScreenSpace, YScreenSpace, Flags); }
 WINBOOL STDMETHODCALLTYPE ShowCursor(WINBOOL bShow) override { last=12;observed=pack(bShow);return 0x12345678; }
 HRESULT STDMETHODCALLTYPE CreateAdditionalSwapChain(D3DPRESENT_PARAMETERS * pPresentationParameters, IDirect3DSwapChain8 ** pSwapChain) override { last=13;observed=pack(pPresentationParameters, pSwapChain);return hr; }
 HRESULT STDMETHODCALLTYPE Reset(D3DPRESENT_PARAMETERS * pPresentationParameters) override { last=14;observed=pack(pPresentationParameters);return hr; }
 HRESULT STDMETHODCALLTYPE Present(const RECT *src_rect, const RECT *dst_rect, HWND dst_window_override, const RGNDATA *dirty_region) override { last=15;observed=pack(src_rect, dst_rect, dst_window_override, dirty_region);return hr; }
 HRESULT STDMETHODCALLTYPE GetBackBuffer(UINT BackBuffer,D3DBACKBUFFER_TYPE Type,IDirect3DSurface8 ** ppBackBuffer) override { last=16;observed=pack(BackBuffer, Type, ppBackBuffer);return hr; }
 HRESULT STDMETHODCALLTYPE GetRasterStatus(D3DRASTER_STATUS * pRasterStatus) override { last=17;observed=pack(pRasterStatus);return hr; }
 void STDMETHODCALLTYPE SetGammaRamp(DWORD flags, const D3DGAMMARAMP *ramp) override { last=18;observed=pack(flags, ramp); }
 void STDMETHODCALLTYPE GetGammaRamp(D3DGAMMARAMP * pRamp) override { last=19;observed=pack(pRamp); }
 HRESULT STDMETHODCALLTYPE CreateTexture(UINT Width,UINT Height,UINT Levels,DWORD Usage,D3DFORMAT Format,D3DPOOL Pool,IDirect3DTexture8 ** ppTexture) override { last=20;observed=pack(Width, Height, Levels, Usage, Format, Pool, ppTexture);return hr; }
 HRESULT STDMETHODCALLTYPE CreateVolumeTexture(UINT Width,UINT Height,UINT Depth,UINT Levels,DWORD Usage,D3DFORMAT Format,D3DPOOL Pool,IDirect3DVolumeTexture8 ** ppVolumeTexture) override { last=21;observed=pack(Width, Height, Depth, Levels, Usage, Format, Pool, ppVolumeTexture);return hr; }
 HRESULT STDMETHODCALLTYPE CreateCubeTexture(UINT EdgeLength,UINT Levels,DWORD Usage,D3DFORMAT Format,D3DPOOL Pool,IDirect3DCubeTexture8 ** ppCubeTexture) override { last=22;observed=pack(EdgeLength, Levels, Usage, Format, Pool, ppCubeTexture);return hr; }
 HRESULT STDMETHODCALLTYPE CreateVertexBuffer(UINT Length,DWORD Usage,DWORD FVF,D3DPOOL Pool,IDirect3DVertexBuffer8 ** ppVertexBuffer) override { last=23;observed=pack(Length, Usage, FVF, Pool, ppVertexBuffer);return hr; }
 HRESULT STDMETHODCALLTYPE CreateIndexBuffer(UINT Length,DWORD Usage,D3DFORMAT Format,D3DPOOL Pool,IDirect3DIndexBuffer8 ** ppIndexBuffer) override { last=24;observed=pack(Length, Usage, Format, Pool, ppIndexBuffer);return hr; }
 HRESULT STDMETHODCALLTYPE CreateRenderTarget(UINT Width,UINT Height,D3DFORMAT Format,D3DMULTISAMPLE_TYPE MultiSample,WINBOOL Lockable,IDirect3DSurface8 ** ppSurface) override { last=25;observed=pack(Width, Height, Format, MultiSample, Lockable, ppSurface);return hr; }
 HRESULT STDMETHODCALLTYPE CreateDepthStencilSurface(UINT Width,UINT Height,D3DFORMAT Format,D3DMULTISAMPLE_TYPE MultiSample,IDirect3DSurface8 ** ppSurface) override { last=26;observed=pack(Width, Height, Format, MultiSample, ppSurface);return hr; }
 HRESULT STDMETHODCALLTYPE CreateImageSurface(UINT Width,UINT Height,D3DFORMAT Format,IDirect3DSurface8 ** ppSurface) override { last=27;observed=pack(Width, Height, Format, ppSurface);return hr; }
 HRESULT STDMETHODCALLTYPE CopyRects(IDirect3DSurface8 *src_surface, const RECT *src_rects, UINT rect_count, IDirect3DSurface8 *dst_surface, const POINT *dst_points) override { last=28;observed=pack(src_surface, src_rects, rect_count, dst_surface, dst_points);return hr; }
 HRESULT STDMETHODCALLTYPE UpdateTexture(IDirect3DBaseTexture8 * pSourceTexture,IDirect3DBaseTexture8 * pDestinationTexture) override { last=29;observed=pack(pSourceTexture, pDestinationTexture);return hr; }
 HRESULT STDMETHODCALLTYPE GetFrontBuffer(IDirect3DSurface8 * pDestSurface) override { last=30;observed=pack(pDestSurface);return hr; }
 HRESULT STDMETHODCALLTYPE SetRenderTarget(IDirect3DSurface8 * pRenderTarget,IDirect3DSurface8 * pNewZStencil) override { last=31;observed=pack(pRenderTarget, pNewZStencil);return hr; }
 HRESULT STDMETHODCALLTYPE GetRenderTarget(IDirect3DSurface8 ** ppRenderTarget) override { last=32;observed=pack(ppRenderTarget);return hr; }
 HRESULT STDMETHODCALLTYPE GetDepthStencilSurface(IDirect3DSurface8 ** ppZStencilSurface) override { last=33;observed=pack(ppZStencilSurface);return hr; }
 HRESULT STDMETHODCALLTYPE BeginScene() override { last=34;observed=pack();return hr; }
 HRESULT STDMETHODCALLTYPE EndScene() override { last=35;observed=pack();return hr; }
 HRESULT STDMETHODCALLTYPE Clear(DWORD rect_count, const D3DRECT *rects, DWORD flags, D3DCOLOR color, float z, DWORD stencil) override { last=36;observed=pack(rect_count, rects, flags, color, z, stencil);return hr; }
 HRESULT STDMETHODCALLTYPE SetTransform(D3DTRANSFORMSTATETYPE state, const D3DMATRIX *matrix) override { last=37;observed=pack(state, matrix);return hr; }
 HRESULT STDMETHODCALLTYPE GetTransform(D3DTRANSFORMSTATETYPE State,D3DMATRIX * pMatrix) override { last=38;observed=pack(State, pMatrix);return hr; }
 HRESULT STDMETHODCALLTYPE MultiplyTransform(D3DTRANSFORMSTATETYPE state, const D3DMATRIX *matrix) override { last=39;observed=pack(state, matrix);return hr; }
 HRESULT STDMETHODCALLTYPE SetViewport(const D3DVIEWPORT8 *viewport) override { last=40;observed=pack(viewport);return hr; }
 HRESULT STDMETHODCALLTYPE GetViewport(D3DVIEWPORT8 * pViewport) override { last=41;observed=pack(pViewport);return hr; }
 HRESULT STDMETHODCALLTYPE SetMaterial(const D3DMATERIAL8 *material) override { last=42;observed=pack(material);return hr; }
 HRESULT STDMETHODCALLTYPE GetMaterial(D3DMATERIAL8 *pMaterial) override { last=43;observed=pack(pMaterial);return hr; }
 HRESULT STDMETHODCALLTYPE SetLight(DWORD index, const D3DLIGHT8 *light) override { last=44;observed=pack(index, light);return hr; }
 HRESULT STDMETHODCALLTYPE GetLight(DWORD Index,D3DLIGHT8 * pLight) override { last=45;observed=pack(Index, pLight);return hr; }
 HRESULT STDMETHODCALLTYPE LightEnable(DWORD Index,WINBOOL Enable) override { last=46;observed=pack(Index, Enable);return hr; }
 HRESULT STDMETHODCALLTYPE GetLightEnable(DWORD Index,WINBOOL * pEnable) override { last=47;observed=pack(Index, pEnable);return hr; }
 HRESULT STDMETHODCALLTYPE SetClipPlane(DWORD index, const float *plane) override { last=48;observed=pack(index, plane);return hr; }
 HRESULT STDMETHODCALLTYPE GetClipPlane(DWORD Index,float * pPlane) override { last=49;observed=pack(Index, pPlane);return hr; }
 HRESULT STDMETHODCALLTYPE SetRenderState(D3DRENDERSTATETYPE State,DWORD Value) override { last=50;observed=pack(State, Value);return hr; }
 HRESULT STDMETHODCALLTYPE GetRenderState(D3DRENDERSTATETYPE State,DWORD * pValue) override { last=51;observed=pack(State, pValue);return hr; }
 HRESULT STDMETHODCALLTYPE BeginStateBlock() override { last=52;observed=pack();return hr; }
 HRESULT STDMETHODCALLTYPE EndStateBlock(DWORD * pToken) override { last=53;observed=pack(pToken);return hr; }
 HRESULT STDMETHODCALLTYPE ApplyStateBlock(DWORD Token) override { last=54;observed=pack(Token);return hr; }
 HRESULT STDMETHODCALLTYPE CaptureStateBlock(DWORD Token) override { last=55;observed=pack(Token);return hr; }
 HRESULT STDMETHODCALLTYPE DeleteStateBlock(DWORD Token) override { last=56;observed=pack(Token);return hr; }
 HRESULT STDMETHODCALLTYPE CreateStateBlock(D3DSTATEBLOCKTYPE Type,DWORD * pToken) override { last=57;observed=pack(Type, pToken);return hr; }
 HRESULT STDMETHODCALLTYPE SetClipStatus(const D3DCLIPSTATUS8 *clip_status) override { last=58;observed=pack(clip_status);return hr; }
 HRESULT STDMETHODCALLTYPE GetClipStatus(D3DCLIPSTATUS8 * pClipStatus) override { last=59;observed=pack(pClipStatus);return hr; }
 HRESULT STDMETHODCALLTYPE GetTexture(DWORD Stage,IDirect3DBaseTexture8 ** ppTexture) override { last=60;observed=pack(Stage, ppTexture);return hr; }
 HRESULT STDMETHODCALLTYPE SetTexture(DWORD Stage,IDirect3DBaseTexture8 * pTexture) override { last=61;observed=pack(Stage, pTexture);return hr; }
 HRESULT STDMETHODCALLTYPE GetTextureStageState(DWORD Stage,D3DTEXTURESTAGESTATETYPE Type,DWORD * pValue) override { last=62;observed=pack(Stage, Type, pValue);return hr; }
 HRESULT STDMETHODCALLTYPE SetTextureStageState(DWORD Stage,D3DTEXTURESTAGESTATETYPE Type,DWORD Value) override { last=63;observed=pack(Stage, Type, Value);return hr; }
 HRESULT STDMETHODCALLTYPE ValidateDevice(DWORD * pNumPasses) override { last=64;observed=pack(pNumPasses);return hr; }
 HRESULT STDMETHODCALLTYPE GetInfo(DWORD DevInfoID,void * pDevInfoStruct,DWORD DevInfoStructSize) override { last=65;observed=pack(DevInfoID, pDevInfoStruct, DevInfoStructSize);return hr; }
 HRESULT STDMETHODCALLTYPE SetPaletteEntries(UINT palette_idx, const PALETTEENTRY *entries) override { last=66;observed=pack(palette_idx, entries);return hr; }
 HRESULT STDMETHODCALLTYPE GetPaletteEntries(UINT PaletteNumber,PALETTEENTRY * pEntries) override { last=67;observed=pack(PaletteNumber, pEntries);return hr; }
 HRESULT STDMETHODCALLTYPE SetCurrentTexturePalette(UINT PaletteNumber) override { last=68;observed=pack(PaletteNumber);return hr; }
 HRESULT STDMETHODCALLTYPE GetCurrentTexturePalette(UINT * PaletteNumber) override { last=69;observed=pack(PaletteNumber);return hr; }
 HRESULT STDMETHODCALLTYPE DrawPrimitive(D3DPRIMITIVETYPE PrimitiveType,UINT StartVertex,UINT PrimitiveCount) override { last=70;observed=pack(PrimitiveType, StartVertex, PrimitiveCount);return hr; }
 HRESULT STDMETHODCALLTYPE DrawIndexedPrimitive(D3DPRIMITIVETYPE PrimitiveType,UINT minIndex,UINT NumVertices,UINT startIndex,UINT primCount) override { last=71;observed=pack(PrimitiveType, minIndex, NumVertices, startIndex, primCount);return hr; }
 HRESULT STDMETHODCALLTYPE DrawPrimitiveUP(D3DPRIMITIVETYPE primitive_type, UINT primitive_count, const void *data, UINT stride) override { last=72;observed=pack(primitive_type, primitive_count, data, stride);return hr; }
 HRESULT STDMETHODCALLTYPE DrawIndexedPrimitiveUP(D3DPRIMITIVETYPE primitive_type, UINT min_vertex_idx, UINT vertex_count, UINT primitive_count, const void *index_data, D3DFORMAT index_format, const void *data, UINT stride) override { last=73;observed=pack(primitive_type, min_vertex_idx, vertex_count, primitive_count, index_data, index_format, data, stride);return hr; }
 HRESULT STDMETHODCALLTYPE ProcessVertices(UINT SrcStartIndex,UINT DestIndex,UINT VertexCount,IDirect3DVertexBuffer8 * pDestBuffer,DWORD Flags) override { last=74;observed=pack(SrcStartIndex, DestIndex, VertexCount, pDestBuffer, Flags);return hr; }
 HRESULT STDMETHODCALLTYPE CreateVertexShader(const DWORD *declaration, const DWORD *byte_code, DWORD *shader, DWORD usage) override { last=75;observed=pack(declaration, byte_code, shader, usage);return hr; }
 HRESULT STDMETHODCALLTYPE SetVertexShader(DWORD Handle) override { last=76;observed=pack(Handle);return hr; }
 HRESULT STDMETHODCALLTYPE GetVertexShader(DWORD * pHandle) override { last=77;observed=pack(pHandle);return hr; }
 HRESULT STDMETHODCALLTYPE DeleteVertexShader(DWORD Handle) override { last=78;observed=pack(Handle);return hr; }
 HRESULT STDMETHODCALLTYPE SetVertexShaderConstant(DWORD reg_idx, const void *data, DWORD count) override { last=79;observed=pack(reg_idx, data, count);return hr; }
 HRESULT STDMETHODCALLTYPE GetVertexShaderConstant(DWORD Register,void * pConstantData,DWORD ConstantCount) override { last=80;observed=pack(Register, pConstantData, ConstantCount);return hr; }
 HRESULT STDMETHODCALLTYPE GetVertexShaderDeclaration(DWORD Handle,void * pData,DWORD * pSizeOfData) override { last=81;observed=pack(Handle, pData, pSizeOfData);return hr; }
 HRESULT STDMETHODCALLTYPE GetVertexShaderFunction(DWORD Handle,void * pData,DWORD * pSizeOfData) override { last=82;observed=pack(Handle, pData, pSizeOfData);return hr; }
 HRESULT STDMETHODCALLTYPE SetStreamSource(UINT StreamNumber,IDirect3DVertexBuffer8 * pStreamData,UINT Stride) override { last=83;observed=pack(StreamNumber, pStreamData, Stride);return hr; }
 HRESULT STDMETHODCALLTYPE GetStreamSource(UINT StreamNumber,IDirect3DVertexBuffer8 ** ppStreamData,UINT * pStride) override { last=84;observed=pack(StreamNumber, ppStreamData, pStride);return hr; }
 HRESULT STDMETHODCALLTYPE SetIndices(IDirect3DIndexBuffer8 * pIndexData,UINT BaseVertexIndex) override { last=85;observed=pack(pIndexData, BaseVertexIndex);return hr; }
 HRESULT STDMETHODCALLTYPE GetIndices(IDirect3DIndexBuffer8 ** ppIndexData,UINT * pBaseVertexIndex) override { last=86;observed=pack(ppIndexData, pBaseVertexIndex);return hr; }
 HRESULT STDMETHODCALLTYPE CreatePixelShader(const DWORD *byte_code, DWORD *shader) override { last=87;observed=pack(byte_code, shader);return hr; }
 HRESULT STDMETHODCALLTYPE SetPixelShader(DWORD Handle) override { last=88;observed=pack(Handle);return hr; }
 HRESULT STDMETHODCALLTYPE GetPixelShader(DWORD * pHandle) override { last=89;observed=pack(pHandle);return hr; }
 HRESULT STDMETHODCALLTYPE DeletePixelShader(DWORD Handle) override { last=90;observed=pack(Handle);return hr; }
 HRESULT STDMETHODCALLTYPE SetPixelShaderConstant(DWORD reg_idx, const void *data, DWORD count) override { last=91;observed=pack(reg_idx, data, count);return hr; }
 HRESULT STDMETHODCALLTYPE GetPixelShaderConstant(DWORD Register,void * pConstantData,DWORD ConstantCount) override { last=92;observed=pack(Register, pConstantData, ConstantCount);return hr; }
 HRESULT STDMETHODCALLTYPE GetPixelShaderFunction(DWORD Handle,void * pData,DWORD * pSizeOfData) override { last=93;observed=pack(Handle, pData, pSizeOfData);return hr; }
 HRESULT STDMETHODCALLTYPE DrawRectPatch(UINT handle, const float *segment_count, const D3DRECTPATCH_INFO *patch_info) override { last=94;observed=pack(handle, segment_count, patch_info);return hr; }
 HRESULT STDMETHODCALLTYPE DrawTriPatch(UINT handle, const float *segment_count, const D3DTRIPATCH_INFO *patch_info) override { last=95;observed=pack(handle, segment_count, patch_info);return hr; }
 HRESULT STDMETHODCALLTYPE DeletePatch(UINT Handle) override { last=96;observed=pack(Handle);return hr; }
};
inline void test_all_MockRootBase(IDirect3D8* w, MockRootBase& m) {
 { m.last=UINT32_MAX;
 auto result = w->RegisterSoftwareDevice(reinterpret_cast<void *>(uintptr_t(4096)));
 CHECK(m.last==3);
 CHECK(m.observed.a==pack(reinterpret_cast<void *>(uintptr_t(4096))).a);
 CHECK(result==m.hr);
 }
 { m.last=UINT32_MAX;
 auto result = w->GetAdapterCount();
 CHECK(m.last==4);
 CHECK(m.observed.a==pack().a);
 CHECK(result==0x12345678);
 }
 { m.last=UINT32_MAX;
 auto result = w->GetAdapterIdentifier(static_cast<UINT>(1), static_cast<DWORD>(2), reinterpret_cast<D3DADAPTER_IDENTIFIER8 *>(uintptr_t(4128)));
 CHECK(m.last==5);
 CHECK(m.observed.a==pack(static_cast<UINT>(1), static_cast<DWORD>(2), reinterpret_cast<D3DADAPTER_IDENTIFIER8 *>(uintptr_t(4128))).a);
 CHECK(result==m.hr);
 }
 { m.last=UINT32_MAX;
 auto result = w->GetAdapterModeCount(static_cast<UINT>(1));
 CHECK(m.last==6);
 CHECK(m.observed.a==pack(static_cast<UINT>(1)).a);
 CHECK(result==0x12345678);
 }
 { m.last=UINT32_MAX;
 auto result = w->EnumAdapterModes(static_cast<UINT>(1), static_cast<UINT>(2), reinterpret_cast<D3DDISPLAYMODE *>(uintptr_t(4128)));
 CHECK(m.last==7);
 CHECK(m.observed.a==pack(static_cast<UINT>(1), static_cast<UINT>(2), reinterpret_cast<D3DDISPLAYMODE *>(uintptr_t(4128))).a);
 CHECK(result==m.hr);
 }
 { m.last=UINT32_MAX;
 auto result = w->GetAdapterDisplayMode(static_cast<UINT>(1), reinterpret_cast<D3DDISPLAYMODE *>(uintptr_t(4112)));
 CHECK(m.last==8);
 CHECK(m.observed.a==pack(static_cast<UINT>(1), reinterpret_cast<D3DDISPLAYMODE *>(uintptr_t(4112))).a);
 CHECK(result==m.hr);
 }
 { m.last=UINT32_MAX;
 auto result = w->CheckDeviceType(static_cast<UINT>(1), static_cast<D3DDEVTYPE>(2), static_cast<D3DFORMAT>(3), static_cast<D3DFORMAT>(4), static_cast<WINBOOL>(5));
 CHECK(m.last==9);
 CHECK(m.observed.a==pack(static_cast<UINT>(1), static_cast<D3DDEVTYPE>(2), static_cast<D3DFORMAT>(3), static_cast<D3DFORMAT>(4), static_cast<WINBOOL>(5)).a);
 CHECK(result==m.hr);
 }
 { m.last=UINT32_MAX;
 auto result = w->CheckDeviceFormat(static_cast<UINT>(1), static_cast<D3DDEVTYPE>(2), static_cast<D3DFORMAT>(3), static_cast<DWORD>(4), static_cast<D3DRESOURCETYPE>(5), static_cast<D3DFORMAT>(6));
 CHECK(m.last==10);
 CHECK(m.observed.a==pack(static_cast<UINT>(1), static_cast<D3DDEVTYPE>(2), static_cast<D3DFORMAT>(3), static_cast<DWORD>(4), static_cast<D3DRESOURCETYPE>(5), static_cast<D3DFORMAT>(6)).a);
 CHECK(result==m.hr);
 }
 { m.last=UINT32_MAX;
 auto result = w->CheckDeviceMultiSampleType(static_cast<UINT>(1), static_cast<D3DDEVTYPE>(2), static_cast<D3DFORMAT>(3), static_cast<WINBOOL>(4), static_cast<D3DMULTISAMPLE_TYPE>(5));
 CHECK(m.last==11);
 CHECK(m.observed.a==pack(static_cast<UINT>(1), static_cast<D3DDEVTYPE>(2), static_cast<D3DFORMAT>(3), static_cast<WINBOOL>(4), static_cast<D3DMULTISAMPLE_TYPE>(5)).a);
 CHECK(result==m.hr);
 }
 { m.last=UINT32_MAX;
 auto result = w->CheckDepthStencilMatch(static_cast<UINT>(1), static_cast<D3DDEVTYPE>(2), static_cast<D3DFORMAT>(3), static_cast<D3DFORMAT>(4), static_cast<D3DFORMAT>(5));
 CHECK(m.last==12);
 CHECK(m.observed.a==pack(static_cast<UINT>(1), static_cast<D3DDEVTYPE>(2), static_cast<D3DFORMAT>(3), static_cast<D3DFORMAT>(4), static_cast<D3DFORMAT>(5)).a);
 CHECK(result==m.hr);
 }
 { m.last=UINT32_MAX;
 auto result = w->GetDeviceCaps(static_cast<UINT>(1), static_cast<D3DDEVTYPE>(2), reinterpret_cast<D3DCAPS8 *>(uintptr_t(4128)));
 CHECK(m.last==13);
 CHECK(m.observed.a==pack(static_cast<UINT>(1), static_cast<D3DDEVTYPE>(2), reinterpret_cast<D3DCAPS8 *>(uintptr_t(4128))).a);
 CHECK(result==m.hr);
 }
 { m.last=UINT32_MAX;
 auto result = w->GetAdapterMonitor(static_cast<UINT>(1));
 CHECK(m.last==14);
 CHECK(m.observed.a==pack(static_cast<UINT>(1)).a);
 CHECK(result==reinterpret_cast<HMONITOR>(0x12345678));
 }
}
inline void test_all_MockDeviceBase(IDirect3DDevice8* w, MockDeviceBase& m) {
 { m.last=UINT32_MAX;
 auto result = w->TestCooperativeLevel();
 CHECK(m.last==3);
 CHECK(m.observed.a==pack().a);
 CHECK(result==m.hr);
 }
 { m.last=UINT32_MAX;
 auto result = w->GetAvailableTextureMem();
 CHECK(m.last==4);
 CHECK(m.observed.a==pack().a);
 CHECK(result==0x12345678);
 }
 { m.last=UINT32_MAX;
 auto result = w->ResourceManagerDiscardBytes(static_cast<DWORD>(1));
 CHECK(m.last==5);
 CHECK(m.observed.a==pack(static_cast<DWORD>(1)).a);
 CHECK(result==m.hr);
 }
 { m.last=UINT32_MAX;
 auto result = w->GetDeviceCaps(reinterpret_cast<D3DCAPS8 *>(uintptr_t(4096)));
 CHECK(m.last==7);
 CHECK(m.observed.a==pack(reinterpret_cast<D3DCAPS8 *>(uintptr_t(4096))).a);
 CHECK(result==m.hr);
 }
 { m.last=UINT32_MAX;
 auto result = w->GetDisplayMode(reinterpret_cast<D3DDISPLAYMODE *>(uintptr_t(4096)));
 CHECK(m.last==8);
 CHECK(m.observed.a==pack(reinterpret_cast<D3DDISPLAYMODE *>(uintptr_t(4096))).a);
 CHECK(result==m.hr);
 }
 { m.last=UINT32_MAX;
 auto result = w->GetCreationParameters(reinterpret_cast<D3DDEVICE_CREATION_PARAMETERS *>(uintptr_t(4096)));
 CHECK(m.last==9);
 CHECK(m.observed.a==pack(reinterpret_cast<D3DDEVICE_CREATION_PARAMETERS *>(uintptr_t(4096))).a);
 CHECK(result==m.hr);
 }
 { m.last=UINT32_MAX;
 auto result = w->SetCursorProperties(static_cast<UINT>(1), static_cast<UINT>(2), reinterpret_cast<IDirect3DSurface8 *>(uintptr_t(4128)));
 CHECK(m.last==10);
 CHECK(m.observed.a==pack(static_cast<UINT>(1), static_cast<UINT>(2), reinterpret_cast<IDirect3DSurface8 *>(uintptr_t(4128))).a);
 CHECK(result==m.hr);
 }
 { m.last=UINT32_MAX;
 w->SetCursorPosition(static_cast<UINT>(1), static_cast<UINT>(2), static_cast<DWORD>(3));
 CHECK(m.last==11);
 CHECK(m.observed.a==pack(static_cast<UINT>(1), static_cast<UINT>(2), static_cast<DWORD>(3)).a);
 }
 { m.last=UINT32_MAX;
 auto result = w->ShowCursor(static_cast<WINBOOL>(1));
 CHECK(m.last==12);
 CHECK(m.observed.a==pack(static_cast<WINBOOL>(1)).a);
 CHECK(result==0x12345678);
 }
 { m.last=UINT32_MAX;
 auto result = w->CreateAdditionalSwapChain(reinterpret_cast<D3DPRESENT_PARAMETERS *>(uintptr_t(4096)), reinterpret_cast<IDirect3DSwapChain8 **>(uintptr_t(4112)));
 CHECK(m.last==13);
 CHECK(m.observed.a==pack(reinterpret_cast<D3DPRESENT_PARAMETERS *>(uintptr_t(4096)), reinterpret_cast<IDirect3DSwapChain8 **>(uintptr_t(4112))).a);
 CHECK(result==m.hr);
 }
 { m.last=UINT32_MAX;
 auto result = w->Reset(reinterpret_cast<D3DPRESENT_PARAMETERS *>(uintptr_t(4096)));
 CHECK(m.last==14);
 CHECK(m.observed.a==pack(reinterpret_cast<D3DPRESENT_PARAMETERS *>(uintptr_t(4096))).a);
 CHECK(result==m.hr);
 }
 { m.last=UINT32_MAX;
 auto result = w->Present(reinterpret_cast<const RECT *>(uintptr_t(4096)), reinterpret_cast<const RECT *>(uintptr_t(4112)), reinterpret_cast<HWND>(uintptr_t(4128)), reinterpret_cast<const RGNDATA *>(uintptr_t(4144)));
 CHECK(m.last==15);
 CHECK(m.observed.a==pack(reinterpret_cast<const RECT *>(uintptr_t(4096)), reinterpret_cast<const RECT *>(uintptr_t(4112)), reinterpret_cast<HWND>(uintptr_t(4128)), reinterpret_cast<const RGNDATA *>(uintptr_t(4144))).a);
 CHECK(result==m.hr);
 }
 { m.last=UINT32_MAX;
 auto result = w->GetBackBuffer(static_cast<UINT>(1), static_cast<D3DBACKBUFFER_TYPE>(2), reinterpret_cast<IDirect3DSurface8 **>(uintptr_t(4128)));
 CHECK(m.last==16);
 CHECK(m.observed.a==pack(static_cast<UINT>(1), static_cast<D3DBACKBUFFER_TYPE>(2), reinterpret_cast<IDirect3DSurface8 **>(uintptr_t(4128))).a);
 CHECK(result==m.hr);
 }
 { m.last=UINT32_MAX;
 auto result = w->GetRasterStatus(reinterpret_cast<D3DRASTER_STATUS *>(uintptr_t(4096)));
 CHECK(m.last==17);
 CHECK(m.observed.a==pack(reinterpret_cast<D3DRASTER_STATUS *>(uintptr_t(4096))).a);
 CHECK(result==m.hr);
 }
 { m.last=UINT32_MAX;
 w->SetGammaRamp(static_cast<DWORD>(1), reinterpret_cast<const D3DGAMMARAMP *>(uintptr_t(4112)));
 CHECK(m.last==18);
 CHECK(m.observed.a==pack(static_cast<DWORD>(1), reinterpret_cast<const D3DGAMMARAMP *>(uintptr_t(4112))).a);
 }
 { m.last=UINT32_MAX;
 w->GetGammaRamp(reinterpret_cast<D3DGAMMARAMP *>(uintptr_t(4096)));
 CHECK(m.last==19);
 CHECK(m.observed.a==pack(reinterpret_cast<D3DGAMMARAMP *>(uintptr_t(4096))).a);
 }
 { m.last=UINT32_MAX;
 auto result = w->CreateTexture(static_cast<UINT>(1), static_cast<UINT>(2), static_cast<UINT>(3), static_cast<DWORD>(4), static_cast<D3DFORMAT>(5), static_cast<D3DPOOL>(6), reinterpret_cast<IDirect3DTexture8 **>(uintptr_t(4192)));
 CHECK(m.last==20);
 CHECK(m.observed.a==pack(static_cast<UINT>(1), static_cast<UINT>(2), static_cast<UINT>(3), static_cast<DWORD>(4), static_cast<D3DFORMAT>(5), static_cast<D3DPOOL>(6), reinterpret_cast<IDirect3DTexture8 **>(uintptr_t(4192))).a);
 CHECK(result==m.hr);
 }
 { m.last=UINT32_MAX;
 auto result = w->CreateVolumeTexture(static_cast<UINT>(1), static_cast<UINT>(2), static_cast<UINT>(3), static_cast<UINT>(4), static_cast<DWORD>(5), static_cast<D3DFORMAT>(6), static_cast<D3DPOOL>(7), reinterpret_cast<IDirect3DVolumeTexture8 **>(uintptr_t(4208)));
 CHECK(m.last==21);
 CHECK(m.observed.a==pack(static_cast<UINT>(1), static_cast<UINT>(2), static_cast<UINT>(3), static_cast<UINT>(4), static_cast<DWORD>(5), static_cast<D3DFORMAT>(6), static_cast<D3DPOOL>(7), reinterpret_cast<IDirect3DVolumeTexture8 **>(uintptr_t(4208))).a);
 CHECK(result==m.hr);
 }
 { m.last=UINT32_MAX;
 auto result = w->CreateCubeTexture(static_cast<UINT>(1), static_cast<UINT>(2), static_cast<DWORD>(3), static_cast<D3DFORMAT>(4), static_cast<D3DPOOL>(5), reinterpret_cast<IDirect3DCubeTexture8 **>(uintptr_t(4176)));
 CHECK(m.last==22);
 CHECK(m.observed.a==pack(static_cast<UINT>(1), static_cast<UINT>(2), static_cast<DWORD>(3), static_cast<D3DFORMAT>(4), static_cast<D3DPOOL>(5), reinterpret_cast<IDirect3DCubeTexture8 **>(uintptr_t(4176))).a);
 CHECK(result==m.hr);
 }
 { m.last=UINT32_MAX;
 auto result = w->CreateVertexBuffer(static_cast<UINT>(1), static_cast<DWORD>(2), static_cast<DWORD>(3), static_cast<D3DPOOL>(4), reinterpret_cast<IDirect3DVertexBuffer8 **>(uintptr_t(4160)));
 CHECK(m.last==23);
 CHECK(m.observed.a==pack(static_cast<UINT>(1), static_cast<DWORD>(2), static_cast<DWORD>(3), static_cast<D3DPOOL>(4), reinterpret_cast<IDirect3DVertexBuffer8 **>(uintptr_t(4160))).a);
 CHECK(result==m.hr);
 }
 { m.last=UINT32_MAX;
 auto result = w->CreateIndexBuffer(static_cast<UINT>(1), static_cast<DWORD>(2), static_cast<D3DFORMAT>(3), static_cast<D3DPOOL>(4), reinterpret_cast<IDirect3DIndexBuffer8 **>(uintptr_t(4160)));
 CHECK(m.last==24);
 CHECK(m.observed.a==pack(static_cast<UINT>(1), static_cast<DWORD>(2), static_cast<D3DFORMAT>(3), static_cast<D3DPOOL>(4), reinterpret_cast<IDirect3DIndexBuffer8 **>(uintptr_t(4160))).a);
 CHECK(result==m.hr);
 }
 { m.last=UINT32_MAX;
 auto result = w->CreateRenderTarget(static_cast<UINT>(1), static_cast<UINT>(2), static_cast<D3DFORMAT>(3), static_cast<D3DMULTISAMPLE_TYPE>(4), static_cast<WINBOOL>(5), reinterpret_cast<IDirect3DSurface8 **>(uintptr_t(4176)));
 CHECK(m.last==25);
 CHECK(m.observed.a==pack(static_cast<UINT>(1), static_cast<UINT>(2), static_cast<D3DFORMAT>(3), static_cast<D3DMULTISAMPLE_TYPE>(4), static_cast<WINBOOL>(5), reinterpret_cast<IDirect3DSurface8 **>(uintptr_t(4176))).a);
 CHECK(result==m.hr);
 }
 { m.last=UINT32_MAX;
 auto result = w->CreateDepthStencilSurface(static_cast<UINT>(1), static_cast<UINT>(2), static_cast<D3DFORMAT>(3), static_cast<D3DMULTISAMPLE_TYPE>(4), reinterpret_cast<IDirect3DSurface8 **>(uintptr_t(4160)));
 CHECK(m.last==26);
 CHECK(m.observed.a==pack(static_cast<UINT>(1), static_cast<UINT>(2), static_cast<D3DFORMAT>(3), static_cast<D3DMULTISAMPLE_TYPE>(4), reinterpret_cast<IDirect3DSurface8 **>(uintptr_t(4160))).a);
 CHECK(result==m.hr);
 }
 { m.last=UINT32_MAX;
 auto result = w->CreateImageSurface(static_cast<UINT>(1), static_cast<UINT>(2), static_cast<D3DFORMAT>(3), reinterpret_cast<IDirect3DSurface8 **>(uintptr_t(4144)));
 CHECK(m.last==27);
 CHECK(m.observed.a==pack(static_cast<UINT>(1), static_cast<UINT>(2), static_cast<D3DFORMAT>(3), reinterpret_cast<IDirect3DSurface8 **>(uintptr_t(4144))).a);
 CHECK(result==m.hr);
 }
 { m.last=UINT32_MAX;
 auto result = w->CopyRects(reinterpret_cast<IDirect3DSurface8 *>(uintptr_t(4096)), reinterpret_cast<const RECT *>(uintptr_t(4112)), static_cast<UINT>(3), reinterpret_cast<IDirect3DSurface8 *>(uintptr_t(4144)), reinterpret_cast<const POINT *>(uintptr_t(4160)));
 CHECK(m.last==28);
 CHECK(m.observed.a==pack(reinterpret_cast<IDirect3DSurface8 *>(uintptr_t(4096)), reinterpret_cast<const RECT *>(uintptr_t(4112)), static_cast<UINT>(3), reinterpret_cast<IDirect3DSurface8 *>(uintptr_t(4144)), reinterpret_cast<const POINT *>(uintptr_t(4160))).a);
 CHECK(result==m.hr);
 }
 { m.last=UINT32_MAX;
 auto result = w->UpdateTexture(reinterpret_cast<IDirect3DBaseTexture8 *>(uintptr_t(4096)), reinterpret_cast<IDirect3DBaseTexture8 *>(uintptr_t(4112)));
 CHECK(m.last==29);
 CHECK(m.observed.a==pack(reinterpret_cast<IDirect3DBaseTexture8 *>(uintptr_t(4096)), reinterpret_cast<IDirect3DBaseTexture8 *>(uintptr_t(4112))).a);
 CHECK(result==m.hr);
 }
 { m.last=UINT32_MAX;
 auto result = w->GetFrontBuffer(reinterpret_cast<IDirect3DSurface8 *>(uintptr_t(4096)));
 CHECK(m.last==30);
 CHECK(m.observed.a==pack(reinterpret_cast<IDirect3DSurface8 *>(uintptr_t(4096))).a);
 CHECK(result==m.hr);
 }
 { m.last=UINT32_MAX;
 auto result = w->SetRenderTarget(reinterpret_cast<IDirect3DSurface8 *>(uintptr_t(4096)), reinterpret_cast<IDirect3DSurface8 *>(uintptr_t(4112)));
 CHECK(m.last==31);
 CHECK(m.observed.a==pack(reinterpret_cast<IDirect3DSurface8 *>(uintptr_t(4096)), reinterpret_cast<IDirect3DSurface8 *>(uintptr_t(4112))).a);
 CHECK(result==m.hr);
 }
 { m.last=UINT32_MAX;
 auto result = w->GetRenderTarget(reinterpret_cast<IDirect3DSurface8 **>(uintptr_t(4096)));
 CHECK(m.last==32);
 CHECK(m.observed.a==pack(reinterpret_cast<IDirect3DSurface8 **>(uintptr_t(4096))).a);
 CHECK(result==m.hr);
 }
 { m.last=UINT32_MAX;
 auto result = w->GetDepthStencilSurface(reinterpret_cast<IDirect3DSurface8 **>(uintptr_t(4096)));
 CHECK(m.last==33);
 CHECK(m.observed.a==pack(reinterpret_cast<IDirect3DSurface8 **>(uintptr_t(4096))).a);
 CHECK(result==m.hr);
 }
 { m.last=UINT32_MAX;
 auto result = w->BeginScene();
 CHECK(m.last==34);
 CHECK(m.observed.a==pack().a);
 CHECK(result==m.hr);
 }
 { m.last=UINT32_MAX;
 auto result = w->EndScene();
 CHECK(m.last==35);
 CHECK(m.observed.a==pack().a);
 CHECK(result==m.hr);
 }
 { m.last=UINT32_MAX;
 auto result = w->Clear(static_cast<DWORD>(1), reinterpret_cast<const D3DRECT *>(uintptr_t(4112)), static_cast<DWORD>(3), static_cast<D3DCOLOR>(4), static_cast<float>(5), static_cast<DWORD>(6));
 CHECK(m.last==36);
 CHECK(m.observed.a==pack(static_cast<DWORD>(1), reinterpret_cast<const D3DRECT *>(uintptr_t(4112)), static_cast<DWORD>(3), static_cast<D3DCOLOR>(4), static_cast<float>(5), static_cast<DWORD>(6)).a);
 CHECK(result==m.hr);
 }
 { m.last=UINT32_MAX;
 auto result = w->SetTransform(static_cast<D3DTRANSFORMSTATETYPE>(1), reinterpret_cast<const D3DMATRIX *>(uintptr_t(4112)));
 CHECK(m.last==37);
 CHECK(m.observed.a==pack(static_cast<D3DTRANSFORMSTATETYPE>(1), reinterpret_cast<const D3DMATRIX *>(uintptr_t(4112))).a);
 CHECK(result==m.hr);
 }
 { m.last=UINT32_MAX;
 auto result = w->GetTransform(static_cast<D3DTRANSFORMSTATETYPE>(1), reinterpret_cast<D3DMATRIX *>(uintptr_t(4112)));
 CHECK(m.last==38);
 CHECK(m.observed.a==pack(static_cast<D3DTRANSFORMSTATETYPE>(1), reinterpret_cast<D3DMATRIX *>(uintptr_t(4112))).a);
 CHECK(result==m.hr);
 }
 { m.last=UINT32_MAX;
 auto result = w->MultiplyTransform(static_cast<D3DTRANSFORMSTATETYPE>(1), reinterpret_cast<const D3DMATRIX *>(uintptr_t(4112)));
 CHECK(m.last==39);
 CHECK(m.observed.a==pack(static_cast<D3DTRANSFORMSTATETYPE>(1), reinterpret_cast<const D3DMATRIX *>(uintptr_t(4112))).a);
 CHECK(result==m.hr);
 }
 { m.last=UINT32_MAX;
 auto result = w->SetViewport(reinterpret_cast<const D3DVIEWPORT8 *>(uintptr_t(4096)));
 CHECK(m.last==40);
 CHECK(m.observed.a==pack(reinterpret_cast<const D3DVIEWPORT8 *>(uintptr_t(4096))).a);
 CHECK(result==m.hr);
 }
 { m.last=UINT32_MAX;
 auto result = w->GetViewport(reinterpret_cast<D3DVIEWPORT8 *>(uintptr_t(4096)));
 CHECK(m.last==41);
 CHECK(m.observed.a==pack(reinterpret_cast<D3DVIEWPORT8 *>(uintptr_t(4096))).a);
 CHECK(result==m.hr);
 }
 { m.last=UINT32_MAX;
 auto result = w->SetMaterial(reinterpret_cast<const D3DMATERIAL8 *>(uintptr_t(4096)));
 CHECK(m.last==42);
 CHECK(m.observed.a==pack(reinterpret_cast<const D3DMATERIAL8 *>(uintptr_t(4096))).a);
 CHECK(result==m.hr);
 }
 { m.last=UINT32_MAX;
 auto result = w->GetMaterial(reinterpret_cast<D3DMATERIAL8 *>(uintptr_t(4096)));
 CHECK(m.last==43);
 CHECK(m.observed.a==pack(reinterpret_cast<D3DMATERIAL8 *>(uintptr_t(4096))).a);
 CHECK(result==m.hr);
 }
 { m.last=UINT32_MAX;
 auto result = w->SetLight(static_cast<DWORD>(1), reinterpret_cast<const D3DLIGHT8 *>(uintptr_t(4112)));
 CHECK(m.last==44);
 CHECK(m.observed.a==pack(static_cast<DWORD>(1), reinterpret_cast<const D3DLIGHT8 *>(uintptr_t(4112))).a);
 CHECK(result==m.hr);
 }
 { m.last=UINT32_MAX;
 auto result = w->GetLight(static_cast<DWORD>(1), reinterpret_cast<D3DLIGHT8 *>(uintptr_t(4112)));
 CHECK(m.last==45);
 CHECK(m.observed.a==pack(static_cast<DWORD>(1), reinterpret_cast<D3DLIGHT8 *>(uintptr_t(4112))).a);
 CHECK(result==m.hr);
 }
 { m.last=UINT32_MAX;
 auto result = w->LightEnable(static_cast<DWORD>(1), static_cast<WINBOOL>(2));
 CHECK(m.last==46);
 CHECK(m.observed.a==pack(static_cast<DWORD>(1), static_cast<WINBOOL>(2)).a);
 CHECK(result==m.hr);
 }
 { m.last=UINT32_MAX;
 auto result = w->GetLightEnable(static_cast<DWORD>(1), reinterpret_cast<WINBOOL *>(uintptr_t(4112)));
 CHECK(m.last==47);
 CHECK(m.observed.a==pack(static_cast<DWORD>(1), reinterpret_cast<WINBOOL *>(uintptr_t(4112))).a);
 CHECK(result==m.hr);
 }
 { m.last=UINT32_MAX;
 auto result = w->SetClipPlane(static_cast<DWORD>(1), reinterpret_cast<const float *>(uintptr_t(4112)));
 CHECK(m.last==48);
 CHECK(m.observed.a==pack(static_cast<DWORD>(1), reinterpret_cast<const float *>(uintptr_t(4112))).a);
 CHECK(result==m.hr);
 }
 { m.last=UINT32_MAX;
 auto result = w->GetClipPlane(static_cast<DWORD>(1), reinterpret_cast<float *>(uintptr_t(4112)));
 CHECK(m.last==49);
 CHECK(m.observed.a==pack(static_cast<DWORD>(1), reinterpret_cast<float *>(uintptr_t(4112))).a);
 CHECK(result==m.hr);
 }
 { m.last=UINT32_MAX;
 auto result = w->SetRenderState(static_cast<D3DRENDERSTATETYPE>(1), static_cast<DWORD>(2));
 CHECK(m.last==50);
 CHECK(m.observed.a==pack(static_cast<D3DRENDERSTATETYPE>(1), static_cast<DWORD>(2)).a);
 CHECK(result==m.hr);
 }
 { m.last=UINT32_MAX;
 auto result = w->GetRenderState(static_cast<D3DRENDERSTATETYPE>(1), reinterpret_cast<DWORD *>(uintptr_t(4112)));
 CHECK(m.last==51);
 CHECK(m.observed.a==pack(static_cast<D3DRENDERSTATETYPE>(1), reinterpret_cast<DWORD *>(uintptr_t(4112))).a);
 CHECK(result==m.hr);
 }
 { m.last=UINT32_MAX;
 auto result = w->BeginStateBlock();
 CHECK(m.last==52);
 CHECK(m.observed.a==pack().a);
 CHECK(result==m.hr);
 }
 { m.last=UINT32_MAX;
 auto result = w->EndStateBlock(reinterpret_cast<DWORD *>(uintptr_t(4096)));
 CHECK(m.last==53);
 CHECK(m.observed.a==pack(reinterpret_cast<DWORD *>(uintptr_t(4096))).a);
 CHECK(result==m.hr);
 }
 { m.last=UINT32_MAX;
 auto result = w->ApplyStateBlock(static_cast<DWORD>(1));
 CHECK(m.last==54);
 CHECK(m.observed.a==pack(static_cast<DWORD>(1)).a);
 CHECK(result==m.hr);
 }
 { m.last=UINT32_MAX;
 auto result = w->CaptureStateBlock(static_cast<DWORD>(1));
 CHECK(m.last==55);
 CHECK(m.observed.a==pack(static_cast<DWORD>(1)).a);
 CHECK(result==m.hr);
 }
 { m.last=UINT32_MAX;
 auto result = w->DeleteStateBlock(static_cast<DWORD>(1));
 CHECK(m.last==56);
 CHECK(m.observed.a==pack(static_cast<DWORD>(1)).a);
 CHECK(result==m.hr);
 }
 { m.last=UINT32_MAX;
 auto result = w->CreateStateBlock(static_cast<D3DSTATEBLOCKTYPE>(1), reinterpret_cast<DWORD *>(uintptr_t(4112)));
 CHECK(m.last==57);
 CHECK(m.observed.a==pack(static_cast<D3DSTATEBLOCKTYPE>(1), reinterpret_cast<DWORD *>(uintptr_t(4112))).a);
 CHECK(result==m.hr);
 }
 { m.last=UINT32_MAX;
 auto result = w->SetClipStatus(reinterpret_cast<const D3DCLIPSTATUS8 *>(uintptr_t(4096)));
 CHECK(m.last==58);
 CHECK(m.observed.a==pack(reinterpret_cast<const D3DCLIPSTATUS8 *>(uintptr_t(4096))).a);
 CHECK(result==m.hr);
 }
 { m.last=UINT32_MAX;
 auto result = w->GetClipStatus(reinterpret_cast<D3DCLIPSTATUS8 *>(uintptr_t(4096)));
 CHECK(m.last==59);
 CHECK(m.observed.a==pack(reinterpret_cast<D3DCLIPSTATUS8 *>(uintptr_t(4096))).a);
 CHECK(result==m.hr);
 }
 { m.last=UINT32_MAX;
 auto result = w->GetTexture(static_cast<DWORD>(1), reinterpret_cast<IDirect3DBaseTexture8 **>(uintptr_t(4112)));
 CHECK(m.last==60);
 CHECK(m.observed.a==pack(static_cast<DWORD>(1), reinterpret_cast<IDirect3DBaseTexture8 **>(uintptr_t(4112))).a);
 CHECK(result==m.hr);
 }
 { m.last=UINT32_MAX;
 auto result = w->SetTexture(static_cast<DWORD>(1), reinterpret_cast<IDirect3DBaseTexture8 *>(uintptr_t(4112)));
 CHECK(m.last==61);
 CHECK(m.observed.a==pack(static_cast<DWORD>(1), reinterpret_cast<IDirect3DBaseTexture8 *>(uintptr_t(4112))).a);
 CHECK(result==m.hr);
 }
 { m.last=UINT32_MAX;
 auto result = w->GetTextureStageState(static_cast<DWORD>(1), static_cast<D3DTEXTURESTAGESTATETYPE>(2), reinterpret_cast<DWORD *>(uintptr_t(4128)));
 CHECK(m.last==62);
 CHECK(m.observed.a==pack(static_cast<DWORD>(1), static_cast<D3DTEXTURESTAGESTATETYPE>(2), reinterpret_cast<DWORD *>(uintptr_t(4128))).a);
 CHECK(result==m.hr);
 }
 { m.last=UINT32_MAX;
 auto result = w->SetTextureStageState(static_cast<DWORD>(1), static_cast<D3DTEXTURESTAGESTATETYPE>(2), static_cast<DWORD>(3));
 CHECK(m.last==63);
 CHECK(m.observed.a==pack(static_cast<DWORD>(1), static_cast<D3DTEXTURESTAGESTATETYPE>(2), static_cast<DWORD>(3)).a);
 CHECK(result==m.hr);
 }
 { m.last=UINT32_MAX;
 auto result = w->ValidateDevice(reinterpret_cast<DWORD *>(uintptr_t(4096)));
 CHECK(m.last==64);
 CHECK(m.observed.a==pack(reinterpret_cast<DWORD *>(uintptr_t(4096))).a);
 CHECK(result==m.hr);
 }
 { m.last=UINT32_MAX;
 auto result = w->GetInfo(static_cast<DWORD>(1), reinterpret_cast<void *>(uintptr_t(4112)), static_cast<DWORD>(3));
 CHECK(m.last==65);
 CHECK(m.observed.a==pack(static_cast<DWORD>(1), reinterpret_cast<void *>(uintptr_t(4112)), static_cast<DWORD>(3)).a);
 CHECK(result==m.hr);
 }
 { m.last=UINT32_MAX;
 auto result = w->SetPaletteEntries(static_cast<UINT>(1), reinterpret_cast<const PALETTEENTRY *>(uintptr_t(4112)));
 CHECK(m.last==66);
 CHECK(m.observed.a==pack(static_cast<UINT>(1), reinterpret_cast<const PALETTEENTRY *>(uintptr_t(4112))).a);
 CHECK(result==m.hr);
 }
 { m.last=UINT32_MAX;
 auto result = w->GetPaletteEntries(static_cast<UINT>(1), reinterpret_cast<PALETTEENTRY *>(uintptr_t(4112)));
 CHECK(m.last==67);
 CHECK(m.observed.a==pack(static_cast<UINT>(1), reinterpret_cast<PALETTEENTRY *>(uintptr_t(4112))).a);
 CHECK(result==m.hr);
 }
 { m.last=UINT32_MAX;
 auto result = w->SetCurrentTexturePalette(static_cast<UINT>(1));
 CHECK(m.last==68);
 CHECK(m.observed.a==pack(static_cast<UINT>(1)).a);
 CHECK(result==m.hr);
 }
 { m.last=UINT32_MAX;
 auto result = w->GetCurrentTexturePalette(reinterpret_cast<UINT *>(uintptr_t(4096)));
 CHECK(m.last==69);
 CHECK(m.observed.a==pack(reinterpret_cast<UINT *>(uintptr_t(4096))).a);
 CHECK(result==m.hr);
 }
 { m.last=UINT32_MAX;
 auto result = w->DrawPrimitive(static_cast<D3DPRIMITIVETYPE>(1), static_cast<UINT>(2), static_cast<UINT>(3));
 CHECK(m.last==70);
 CHECK(m.observed.a==pack(static_cast<D3DPRIMITIVETYPE>(1), static_cast<UINT>(2), static_cast<UINT>(3)).a);
 CHECK(result==m.hr);
 }
 { m.last=UINT32_MAX;
 auto result = w->DrawIndexedPrimitive(static_cast<D3DPRIMITIVETYPE>(1), static_cast<UINT>(2), static_cast<UINT>(3), static_cast<UINT>(4), static_cast<UINT>(5));
 CHECK(m.last==71);
 CHECK(m.observed.a==pack(static_cast<D3DPRIMITIVETYPE>(1), static_cast<UINT>(2), static_cast<UINT>(3), static_cast<UINT>(4), static_cast<UINT>(5)).a);
 CHECK(result==m.hr);
 }
 { m.last=UINT32_MAX;
 auto result = w->DrawPrimitiveUP(static_cast<D3DPRIMITIVETYPE>(1), static_cast<UINT>(2), reinterpret_cast<const void *>(uintptr_t(4128)), static_cast<UINT>(4));
 CHECK(m.last==72);
 CHECK(m.observed.a==pack(static_cast<D3DPRIMITIVETYPE>(1), static_cast<UINT>(2), reinterpret_cast<const void *>(uintptr_t(4128)), static_cast<UINT>(4)).a);
 CHECK(result==m.hr);
 }
 { m.last=UINT32_MAX;
 auto result = w->DrawIndexedPrimitiveUP(static_cast<D3DPRIMITIVETYPE>(1), static_cast<UINT>(2), static_cast<UINT>(3), static_cast<UINT>(4), reinterpret_cast<const void *>(uintptr_t(4160)), static_cast<D3DFORMAT>(6), reinterpret_cast<const void *>(uintptr_t(4192)), static_cast<UINT>(8));
 CHECK(m.last==73);
 CHECK(m.observed.a==pack(static_cast<D3DPRIMITIVETYPE>(1), static_cast<UINT>(2), static_cast<UINT>(3), static_cast<UINT>(4), reinterpret_cast<const void *>(uintptr_t(4160)), static_cast<D3DFORMAT>(6), reinterpret_cast<const void *>(uintptr_t(4192)), static_cast<UINT>(8)).a);
 CHECK(result==m.hr);
 }
 { m.last=UINT32_MAX;
 auto result = w->ProcessVertices(static_cast<UINT>(1), static_cast<UINT>(2), static_cast<UINT>(3), reinterpret_cast<IDirect3DVertexBuffer8 *>(uintptr_t(4144)), static_cast<DWORD>(5));
 CHECK(m.last==74);
 CHECK(m.observed.a==pack(static_cast<UINT>(1), static_cast<UINT>(2), static_cast<UINT>(3), reinterpret_cast<IDirect3DVertexBuffer8 *>(uintptr_t(4144)), static_cast<DWORD>(5)).a);
 CHECK(result==m.hr);
 }
 { m.last=UINT32_MAX;
 auto result = w->CreateVertexShader(reinterpret_cast<const DWORD *>(uintptr_t(4096)), reinterpret_cast<const DWORD *>(uintptr_t(4112)), reinterpret_cast<DWORD *>(uintptr_t(4128)), static_cast<DWORD>(4));
 CHECK(m.last==75);
 CHECK(m.observed.a==pack(reinterpret_cast<const DWORD *>(uintptr_t(4096)), reinterpret_cast<const DWORD *>(uintptr_t(4112)), reinterpret_cast<DWORD *>(uintptr_t(4128)), static_cast<DWORD>(4)).a);
 CHECK(result==m.hr);
 }
 { m.last=UINT32_MAX;
 auto result = w->SetVertexShader(static_cast<DWORD>(1));
 CHECK(m.last==76);
 CHECK(m.observed.a==pack(static_cast<DWORD>(1)).a);
 CHECK(result==m.hr);
 }
 { m.last=UINT32_MAX;
 auto result = w->GetVertexShader(reinterpret_cast<DWORD *>(uintptr_t(4096)));
 CHECK(m.last==77);
 CHECK(m.observed.a==pack(reinterpret_cast<DWORD *>(uintptr_t(4096))).a);
 CHECK(result==m.hr);
 }
 { m.last=UINT32_MAX;
 auto result = w->DeleteVertexShader(static_cast<DWORD>(1));
 CHECK(m.last==78);
 CHECK(m.observed.a==pack(static_cast<DWORD>(1)).a);
 CHECK(result==m.hr);
 }
 { m.last=UINT32_MAX;
 auto result = w->SetVertexShaderConstant(static_cast<DWORD>(1), reinterpret_cast<const void *>(uintptr_t(4112)), static_cast<DWORD>(3));
 CHECK(m.last==79);
 CHECK(m.observed.a==pack(static_cast<DWORD>(1), reinterpret_cast<const void *>(uintptr_t(4112)), static_cast<DWORD>(3)).a);
 CHECK(result==m.hr);
 }
 { m.last=UINT32_MAX;
 auto result = w->GetVertexShaderConstant(static_cast<DWORD>(1), reinterpret_cast<void *>(uintptr_t(4112)), static_cast<DWORD>(3));
 CHECK(m.last==80);
 CHECK(m.observed.a==pack(static_cast<DWORD>(1), reinterpret_cast<void *>(uintptr_t(4112)), static_cast<DWORD>(3)).a);
 CHECK(result==m.hr);
 }
 { m.last=UINT32_MAX;
 auto result = w->GetVertexShaderDeclaration(static_cast<DWORD>(1), reinterpret_cast<void *>(uintptr_t(4112)), reinterpret_cast<DWORD *>(uintptr_t(4128)));
 CHECK(m.last==81);
 CHECK(m.observed.a==pack(static_cast<DWORD>(1), reinterpret_cast<void *>(uintptr_t(4112)), reinterpret_cast<DWORD *>(uintptr_t(4128))).a);
 CHECK(result==m.hr);
 }
 { m.last=UINT32_MAX;
 auto result = w->GetVertexShaderFunction(static_cast<DWORD>(1), reinterpret_cast<void *>(uintptr_t(4112)), reinterpret_cast<DWORD *>(uintptr_t(4128)));
 CHECK(m.last==82);
 CHECK(m.observed.a==pack(static_cast<DWORD>(1), reinterpret_cast<void *>(uintptr_t(4112)), reinterpret_cast<DWORD *>(uintptr_t(4128))).a);
 CHECK(result==m.hr);
 }
 { m.last=UINT32_MAX;
 auto result = w->SetStreamSource(static_cast<UINT>(1), reinterpret_cast<IDirect3DVertexBuffer8 *>(uintptr_t(4112)), static_cast<UINT>(3));
 CHECK(m.last==83);
 CHECK(m.observed.a==pack(static_cast<UINT>(1), reinterpret_cast<IDirect3DVertexBuffer8 *>(uintptr_t(4112)), static_cast<UINT>(3)).a);
 CHECK(result==m.hr);
 }
 { m.last=UINT32_MAX;
 auto result = w->GetStreamSource(static_cast<UINT>(1), reinterpret_cast<IDirect3DVertexBuffer8 **>(uintptr_t(4112)), reinterpret_cast<UINT *>(uintptr_t(4128)));
 CHECK(m.last==84);
 CHECK(m.observed.a==pack(static_cast<UINT>(1), reinterpret_cast<IDirect3DVertexBuffer8 **>(uintptr_t(4112)), reinterpret_cast<UINT *>(uintptr_t(4128))).a);
 CHECK(result==m.hr);
 }
 { m.last=UINT32_MAX;
 auto result = w->SetIndices(reinterpret_cast<IDirect3DIndexBuffer8 *>(uintptr_t(4096)), static_cast<UINT>(2));
 CHECK(m.last==85);
 CHECK(m.observed.a==pack(reinterpret_cast<IDirect3DIndexBuffer8 *>(uintptr_t(4096)), static_cast<UINT>(2)).a);
 CHECK(result==m.hr);
 }
 { m.last=UINT32_MAX;
 auto result = w->GetIndices(reinterpret_cast<IDirect3DIndexBuffer8 **>(uintptr_t(4096)), reinterpret_cast<UINT *>(uintptr_t(4112)));
 CHECK(m.last==86);
 CHECK(m.observed.a==pack(reinterpret_cast<IDirect3DIndexBuffer8 **>(uintptr_t(4096)), reinterpret_cast<UINT *>(uintptr_t(4112))).a);
 CHECK(result==m.hr);
 }
 { m.last=UINT32_MAX;
 auto result = w->CreatePixelShader(reinterpret_cast<const DWORD *>(uintptr_t(4096)), reinterpret_cast<DWORD *>(uintptr_t(4112)));
 CHECK(m.last==87);
 CHECK(m.observed.a==pack(reinterpret_cast<const DWORD *>(uintptr_t(4096)), reinterpret_cast<DWORD *>(uintptr_t(4112))).a);
 CHECK(result==m.hr);
 }
 { m.last=UINT32_MAX;
 auto result = w->SetPixelShader(static_cast<DWORD>(1));
 CHECK(m.last==88);
 CHECK(m.observed.a==pack(static_cast<DWORD>(1)).a);
 CHECK(result==m.hr);
 }
 { m.last=UINT32_MAX;
 auto result = w->GetPixelShader(reinterpret_cast<DWORD *>(uintptr_t(4096)));
 CHECK(m.last==89);
 CHECK(m.observed.a==pack(reinterpret_cast<DWORD *>(uintptr_t(4096))).a);
 CHECK(result==m.hr);
 }
 { m.last=UINT32_MAX;
 auto result = w->DeletePixelShader(static_cast<DWORD>(1));
 CHECK(m.last==90);
 CHECK(m.observed.a==pack(static_cast<DWORD>(1)).a);
 CHECK(result==m.hr);
 }
 { m.last=UINT32_MAX;
 auto result = w->SetPixelShaderConstant(static_cast<DWORD>(1), reinterpret_cast<const void *>(uintptr_t(4112)), static_cast<DWORD>(3));
 CHECK(m.last==91);
 CHECK(m.observed.a==pack(static_cast<DWORD>(1), reinterpret_cast<const void *>(uintptr_t(4112)), static_cast<DWORD>(3)).a);
 CHECK(result==m.hr);
 }
 { m.last=UINT32_MAX;
 auto result = w->GetPixelShaderConstant(static_cast<DWORD>(1), reinterpret_cast<void *>(uintptr_t(4112)), static_cast<DWORD>(3));
 CHECK(m.last==92);
 CHECK(m.observed.a==pack(static_cast<DWORD>(1), reinterpret_cast<void *>(uintptr_t(4112)), static_cast<DWORD>(3)).a);
 CHECK(result==m.hr);
 }
 { m.last=UINT32_MAX;
 auto result = w->GetPixelShaderFunction(static_cast<DWORD>(1), reinterpret_cast<void *>(uintptr_t(4112)), reinterpret_cast<DWORD *>(uintptr_t(4128)));
 CHECK(m.last==93);
 CHECK(m.observed.a==pack(static_cast<DWORD>(1), reinterpret_cast<void *>(uintptr_t(4112)), reinterpret_cast<DWORD *>(uintptr_t(4128))).a);
 CHECK(result==m.hr);
 }
 { m.last=UINT32_MAX;
 auto result = w->DrawRectPatch(static_cast<UINT>(1), reinterpret_cast<const float *>(uintptr_t(4112)), reinterpret_cast<const D3DRECTPATCH_INFO *>(uintptr_t(4128)));
 CHECK(m.last==94);
 CHECK(m.observed.a==pack(static_cast<UINT>(1), reinterpret_cast<const float *>(uintptr_t(4112)), reinterpret_cast<const D3DRECTPATCH_INFO *>(uintptr_t(4128))).a);
 CHECK(result==m.hr);
 }
 { m.last=UINT32_MAX;
 auto result = w->DrawTriPatch(static_cast<UINT>(1), reinterpret_cast<const float *>(uintptr_t(4112)), reinterpret_cast<const D3DTRIPATCH_INFO *>(uintptr_t(4128)));
 CHECK(m.last==95);
 CHECK(m.observed.a==pack(static_cast<UINT>(1), reinterpret_cast<const float *>(uintptr_t(4112)), reinterpret_cast<const D3DTRIPATCH_INFO *>(uintptr_t(4128))).a);
 CHECK(result==m.hr);
 }
 { m.last=UINT32_MAX;
 auto result = w->DeletePatch(static_cast<UINT>(1));
 CHECK(m.last==96);
 CHECK(m.observed.a==pack(static_cast<UINT>(1)).a);
 CHECK(result==m.hr);
 }
}
}
