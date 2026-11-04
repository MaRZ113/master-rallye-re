// Optional isolated D3D8 probe. Never loads the game or installs native hooks.
#include "atmosphere.hpp"
#include <iostream>
#include <fstream>
#include <filesystem>
#include <vector>
using namespace gfx2;
template<class T>struct Ref {T* p=nullptr;~Ref(){if(p)p->Release();}};
struct Input {float x,y,z;DWORD color;float u,v;};
struct Vertex {float x,y,z,rhw;DWORD color;float u,v;};
static_assert(sizeof(Input)==24&&sizeof(Vertex)==28);
bool okay(HRESULT hr,const char* step){if(FAILED(hr))std::cerr<<step<<" failed 0x"<<std::hex<<static_cast<unsigned long>(hr)<<"\n";return SUCCEEDED(hr);}
bool save(IDirect3DDevice8& n,const std::filesystem::path& path,std::string& hash){
    Ref<IDirect3DSurface8> back;if(!okay(n.GetBackBuffer(0,D3DBACKBUFFER_TYPE_MONO,&back.p),"backbuffer"))return false;
    D3DSURFACE_DESC d{};if(!okay(back.p->GetDesc(&d),"desc")||(d.Format!=D3DFMT_X8R8G8B8&&d.Format!=D3DFMT_A8R8G8B8))return false;
    D3DLOCKED_RECT lock{};if(!okay(back.p->LockRect(&lock,nullptr,D3DLOCK_READONLY),"readback"))return false;
    std::vector<BYTE> pixels(size_t(d.Width)*d.Height*4);
    bool valid=lock.pBits&&lock.Pitch>=INT(d.Width*4);
    if(valid)for(UINT y=0;y<d.Height;++y)std::memcpy(pixels.data()+size_t(d.Height-1-y)*d.Width*4,static_cast<BYTE*>(lock.pBits)+size_t(y)*lock.Pitch,d.Width*4);
    const HRESULT unlocked=back.p->UnlockRect();if(!valid||FAILED(unlocked))return false;
    for(size_t i=3;i<pixels.size();i+=4)pixels[i]=255;
    hash=sha256_bytes(pixels.data(),pixels.size());
    BITMAPFILEHEADER f{};BITMAPINFOHEADER b{};f.bfType=0x4d42;f.bfOffBits=sizeof(f)+sizeof(b);f.bfSize=f.bfOffBits+static_cast<DWORD>(pixels.size());
    b.biSize=sizeof(b);b.biWidth=d.Width;b.biHeight=d.Height;b.biPlanes=1;b.biBitCount=32;b.biCompression=BI_RGB;
    std::ofstream out(path,std::ios::binary);out.write(reinterpret_cast<char*>(&f),sizeof(f));out.write(reinterpret_cast<char*>(&b),sizeof(b));out.write(reinterpret_cast<char*>(pixels.data()),pixels.size());return bool(out);
}
int wmain(int argc,wchar_t** argv){
    if(argc!=3){std::cerr<<"usage: atmosphere_gpu_probe road.bin output-dir\n";return 2;}
    std::ifstream file(argv[1],std::ios::binary);char magic[4]{};uint32_t count=0,w=0,h=0;file.read(magic,4);file.read(reinterpret_cast<char*>(&count),4);file.read(reinterpret_cast<char*>(&w),4);file.read(reinterpret_cast<char*>(&h),4);
    if(std::memcmp(magic,"ATL1",4)||count==0||count%3||count>30000||!w||!h||w>2048||h>2048)return 2;
    std::vector<Input> source(count);std::vector<DWORD> pixels(size_t(w)*h);file.read(reinterpret_cast<char*>(source.data()),count*sizeof(Input));file.read(reinterpret_cast<char*>(pixels.data()),pixels.size()*4);if(!file||file.peek()!=EOF)return 2;
    for(const auto& v:source)if(!std::isfinite(v.x)||!std::isfinite(v.y)||!std::isfinite(v.z)||!std::isfinite(v.u)||!std::isfinite(v.v))return 2;
    const std::filesystem::path output(argv[2]);std::filesystem::create_directories(output);
    wchar_t system[MAX_PATH]{};GetSystemDirectoryW(system,MAX_PATH);HMODULE dll=LoadLibraryW((std::wstring(system)+L"\\d3d8.dll").c_str());if(!dll)return 3;
    auto create=reinterpret_cast<IDirect3D8*(WINAPI*)(UINT)>(GetProcAddress(dll,"Direct3DCreate8"));if(!create)return 3;
    Ref<IDirect3D8> root;root.p=create(D3D_SDK_VERSION);if(!root.p)return 3;
    WNDCLASSW wc{};wc.lpfnWndProc=DefWindowProcW;wc.hInstance=GetModuleHandleW(nullptr);wc.lpszClassName=L"AtmospherePrivateGpuProbe";RegisterClassW(&wc);
    HWND window=CreateWindowW(wc.lpszClassName,L"Atmosphere private offscreen probe",WS_POPUP,0,0,512,512,nullptr,nullptr,wc.hInstance,nullptr);if(!window)return 3;
    D3DDISPLAYMODE mode{};root.p->GetAdapterDisplayMode(0,&mode);D3DPRESENT_PARAMETERS pp{};pp.Windowed=TRUE;pp.hDeviceWindow=window;pp.SwapEffect=D3DSWAPEFFECT_DISCARD;pp.BackBufferWidth=512;pp.BackBufferHeight=512;pp.BackBufferFormat=mode.Format;pp.Flags=D3DPRESENTFLAG_LOCKABLE_BACKBUFFER;
    Ref<IDirect3DDevice8> device;if(!okay(root.p->CreateDevice(0,D3DDEVTYPE_HAL,window,D3DCREATE_SOFTWARE_VERTEXPROCESSING,&pp,&device.p),"CreateDevice")){DestroyWindow(window);return 3;}
    auto& n=*device.p;Ref<IDirect3DTexture8> texture;if(!okay(n.CreateTexture(w,h,1,0,D3DFMT_A8R8G8B8,D3DPOOL_MANAGED,&texture.p),"CreateTexture"))return 3;
    D3DLOCKED_RECT lock{};if(!okay(texture.p->LockRect(0,&lock,nullptr,0),"LockTexture")||!lock.pBits||lock.Pitch<INT(w*4))return 3;
    for(UINT y=0;y<h;++y)std::memcpy(static_cast<BYTE*>(lock.pBits)+size_t(y)*lock.Pitch,pixels.data()+size_t(y)*w,w*4);if(!okay(texture.p->UnlockRect(0),"UnlockTexture"))return 3;
    float xmin=source[0].x,xmax=xmin,zmin=source[0].z,zmax=zmin;
    for(const auto& v:source){xmin=std::min(xmin,v.x);xmax=std::max(xmax,v.x);zmin=std::min(zmin,v.z);zmax=std::max(zmax,v.z);}
    const float extent=std::max(xmax-xmin,zmax-zmin);if(extent<1)return 2;
    const float radius=std::min(100.f,extent/5);
    n.SetRenderState(D3DRS_ZENABLE,FALSE);n.SetRenderState(D3DRS_LIGHTING,FALSE);n.SetRenderState(D3DRS_CULLMODE,D3DCULL_NONE);n.SetRenderState(D3DRS_FOGENABLE,FALSE);n.SetRenderState(D3DRS_ALPHABLENDENABLE,FALSE);
    n.SetTexture(0,texture.p);n.SetTextureStageState(0,D3DTSS_COLOROP,D3DTOP_MODULATE);n.SetTextureStageState(0,D3DTSS_COLORARG1,D3DTA_TEXTURE);n.SetTextureStageState(0,D3DTSS_COLORARG2,D3DTA_DIFFUSE);n.SetTextureStageState(1,D3DTSS_COLOROP,D3DTOP_DISABLE);
    n.SetVertexShader(D3DFVF_XYZRHW|D3DFVF_DIFFUSE|D3DFVF_TEX1);
    std::vector<std::string> hashes;std::vector<size_t> lit;std::vector<Vertex> vertices(count);
    for(unsigned frame=0;frame<3;++frame){
        const auto& lamp=source[frame==1?count/4:count*3/4];size_t illuminated=0;
        for(size_t i=0;i<count;++i){const auto& v=source[i];float light=frame?atmosphere::point_light(v.x,v.y,v.z,lamp.x,lamp.y,lamp.z,radius):0;
            if(light>0)++illuminated;vertices[i]={32+(v.x-xmin)/extent*448,256-(v.z-(zmin+zmax)/2)/extent*448,.5f,1,atmosphere::tint(v.color,1,.86f,.68f,light),v.u,v.v};}
        if(!okay(n.Clear(0,nullptr,D3DCLEAR_TARGET,0xff20232a,1,0),"Clear")||!okay(n.BeginScene(),"BeginScene"))return 3;
        const auto drawn=n.DrawPrimitiveUP(D3DPT_TRIANGLELIST,count/3,vertices.data(),sizeof(Vertex));const auto ended=n.EndScene();if(!okay(drawn,"Draw")||!okay(ended,"EndScene"))return 3;
        std::string hash;if(!save(n,output/(L"road-"+std::to_wstring(frame)+L".bmp"),hash))return 3;hashes.push_back(hash);lit.push_back(illuminated);
    }
    std::ofstream report(output/L"gpu-report.json");report<<"{\"status\":\"D3D8_OFFSCREEN_VALIDATED_NOT_GAMEPLAY\",\"input\":\"one original France1 road draw\",\"triangles\":"<<count/3<<",\"radius\":"<<radius<<",\"image_sha256_bgra_bottom_up\":[";
    for(size_t i=0;i<3;++i)report<<(i?",":"")<<'"'<<hashes[i]<<'"';report<<"],\"lit_vertex_submissions\":["<<lit[0]<<','<<lit[1]<<','<<lit[2]<<"],\"limitations\":\"top-down diagnostic projection, no engine, fog, PS2 effects or shadows\"}\n";
    DestroyWindow(window);if(hashes[0]==hashes[1]||hashes[1]==hashes[2]||!lit[1]||!lit[2])return 1;
    std::cout<<"D3D8 road moving-light probe passed; NOT GAMEPLAY\n";return 0;
}
