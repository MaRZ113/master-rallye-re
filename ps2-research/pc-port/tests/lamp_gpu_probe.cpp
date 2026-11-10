// Isolated system-D3D8 verification, never loads MRallye or a Proxy DLL.
#include "atmosphere_sun.hpp"
#include <fstream>
#include <iostream>
#include <filesystem>
using namespace gfx2;using namespace gfx2::atmosphere;
template<class T>struct Ref {T* p=nullptr;~Ref(){if(p)p->Release();}};
struct Vertex{float x,y,z,rhw;DWORD color;float u,v;};
static bool check(HRESULT hr,const char* what){if(FAILED(hr))std::cerr<<what<<" "<<std::hex<<DWORD(hr)<<std::dec<<"\n";return SUCCEEDED(hr);}
static bool pixels(IDirect3DDevice8& n,IDirect3DSurface8* back,std::vector<DWORD>& result){
    Ref<IDirect3DSurface8> image;D3DSURFACE_DESC d{};back->GetDesc(&d);
    if(!check(n.CreateImageSurface(d.Width,d.Height,d.Format,&image.p),"image")||!check(n.CopyRects(back,nullptr,0,image.p,nullptr),"back readback"))return false;
    D3DLOCKED_RECT lock{};if(!check(image.p->LockRect(&lock,nullptr,D3DLOCK_READONLY),"image lock"))return false;
    if(!lock.pBits||lock.Pitch<int(d.Width*4)){image.p->UnlockRect();return false;}
    result.resize(d.Width*d.Height);for(unsigned y=0;y<d.Height;++y)std::memcpy(result.data()+y*d.Width,static_cast<BYTE*>(lock.pBits)+y*lock.Pitch,d.Width*4);
    return check(image.p->UnlockRect(),"image unlock");
}
static void bitmap(const std::filesystem::path& path,const std::vector<DWORD>& p){
    BITMAPFILEHEADER f{};BITMAPINFOHEADER b{};f.bfType=0x4d42;f.bfOffBits=sizeof(f)+sizeof(b);f.bfSize=f.bfOffBits+unsigned(p.size()*4);
    b.biSize=sizeof(b);b.biWidth=512;b.biHeight=-384;b.biPlanes=1;b.biBitCount=32;b.biCompression=BI_RGB;
    std::ofstream out(path,std::ios::binary);out.write(reinterpret_cast<const char*>(&f),sizeof(f));out.write(reinterpret_cast<const char*>(&b),sizeof(b));out.write(reinterpret_cast<const char*>(p.data()),p.size()*4);
}
int wmain(int argc,wchar_t** argv){
    if(argc!=2&&argc!=3)return 2;const std::filesystem::path output=argv[1];std::filesystem::create_directories(output);
    const D3DFORMAT depth_format=argc==3?D3DFMT_D24X8:D3DFMT_D24S8;
    wchar_t system[MAX_PATH]{};GetSystemDirectoryW(system,MAX_PATH);auto dll=LoadLibraryW((std::wstring(system)+L"\\d3d8.dll").c_str());if(!dll)return 3;
    auto create=reinterpret_cast<IDirect3D8*(WINAPI*)(UINT)>(GetProcAddress(dll,"Direct3DCreate8"));if(!create)return 3;
    Ref<IDirect3D8> root;root.p=create(D3D_SDK_VERSION);if(!root.p)return 3;
    WNDCLASSW wc{};wc.lpfnWndProc=DefWindowProcW;wc.hInstance=GetModuleHandleW(nullptr);wc.lpszClassName=L"LampDepthProbe";RegisterClassW(&wc);
    auto window=CreateWindowW(wc.lpszClassName,L"Private lamp depth test",WS_POPUP,0,0,512,384,nullptr,nullptr,wc.hInstance,nullptr);if(!window)return 3;
    int failures=0;unsigned supported=0;std::ofstream report(output/L"results.jsonl");
    for(unsigned samples:{0u,2u,4u}){
        D3DPRESENT_PARAMETERS pp{};pp.BackBufferWidth=512;pp.BackBufferHeight=384;pp.BackBufferFormat=D3DFMT_X8R8G8B8;pp.BackBufferCount=1;
        pp.MultiSampleType=D3DMULTISAMPLE_TYPE(samples);pp.SwapEffect=D3DSWAPEFFECT_DISCARD;pp.hDeviceWindow=window;pp.Windowed=TRUE;pp.EnableAutoDepthStencil=TRUE;pp.AutoDepthStencilFormat=depth_format;
        Ref<IDirect3DDevice8> device;const auto created=root.p->CreateDevice(D3DADAPTER_DEFAULT,D3DDEVTYPE_HAL,window,D3DCREATE_SOFTWARE_VERTEXPROCESSING,&pp,&device.p);
        if(FAILED(created)){report<<"{\"msaa\":"<<samples<<",\"status\":\"device_unsupported\"}\n";continue;}
        ++supported;auto& n=*device.p;SunFx sun;std::vector<uint64_t> energy;
        Ref<IDirect3DTexture8> cutout;n.CreateTexture(8,8,1,0,D3DFMT_A8R8G8B8,D3DPOOL_MANAGED,&cutout.p);if(!cutout.p)return 3;
        D3DLOCKED_RECT texture{};cutout.p->LockRect(0,&texture,nullptr,0);
        for(unsigned y=0;y<8;++y)for(unsigned x=0;x<8;++x){DWORD c=(x&1)?0xff000000u:0;std::memcpy(static_cast<BYTE*>(texture.pBits)+y*texture.Pitch+x*4,&c,4);}cutout.p->UnlockRect(0);
        for(unsigned mode=0;mode<5;++mode){
            const bool block=mode==1||mode==4,partial=mode==2,leaves=false;
            if(!check(n.Clear(0,nullptr,D3DCLEAR_TARGET|D3DCLEAR_ZBUFFER,0xff000000,1,0),"clear")||!check(n.BeginScene(),"begin"))return 3;
            n.SetRenderState(D3DRS_ZENABLE,TRUE);n.SetRenderState(D3DRS_ZWRITEENABLE,TRUE);n.SetRenderState(D3DRS_ZFUNC,D3DCMP_LESSEQUAL);n.SetRenderState(D3DRS_LIGHTING,FALSE);
            n.SetRenderState(D3DRS_CULLMODE,D3DCULL_NONE);n.SetRenderState(D3DRS_ALPHABLENDENABLE,FALSE);n.SetRenderState(D3DRS_ALPHATESTENABLE,leaves?TRUE:FALSE);n.SetRenderState(D3DRS_ALPHAREF,127);n.SetRenderState(D3DRS_ALPHAFUNC,D3DCMP_GREATER);
            n.SetRenderState(D3DRS_COLORWRITEENABLE,15);n.SetTexture(0,leaves?cutout.p:nullptr);n.SetTextureStageState(0,D3DTSS_COLOROP,D3DTOP_SELECTARG1);n.SetTextureStageState(0,D3DTSS_COLORARG1,D3DTA_DIFFUSE);
            n.SetTextureStageState(0,D3DTSS_ALPHAOP,D3DTOP_SELECTARG1);n.SetTextureStageState(0,D3DTSS_ALPHAARG1,leaves?D3DTA_TEXTURE:D3DTA_DIFFUSE);
            n.SetTextureStageState(0,D3DTSS_TEXCOORDINDEX,0);n.SetTextureStageState(0,D3DTSS_TEXTURETRANSFORMFLAGS,D3DTTFF_DISABLE);n.SetTextureStageState(0,D3DTSS_MAGFILTER,D3DTEXF_POINT);n.SetTextureStageState(0,D3DTSS_MINFILTER,D3DTEXF_POINT);
            n.SetTextureStageState(1,D3DTSS_COLOROP,D3DTOP_DISABLE);n.SetVertexShader(D3DFVF_XYZRHW|D3DFVF_DIFFUSE|D3DFVF_TEX1);n.SetPixelShader(0);
            const float right=partial?260.f:512.f,z=mode==4?.9f:.3f;const float left=partial?252.f:0.f; const Vertex occluder[4]={{left-.5f,-.5f,z,1,0xff000000,0,0},{right-.5f,-.5f,z,1,0xff000000,1,0},{left-.5f,383.5f,z,1,0xff000000,0,1},{right-.5f,383.5f,z,1,0xff000000,1,1}};
            if(block||partial||leaves)if(!check(n.DrawPrimitiveUP(D3DPT_TRIANGLESTRIP,2,occluder,sizeof(Vertex)),"occluder"))return 3;
            sun.proof.clear();n.GetRenderTarget(&sun.proof.target);n.GetDepthStencilSurface(&sun.proof.depth);sun.proof.world=true;sun.proof.race=1;sun.proof.reset=1;
            DWORD before_shader=0;n.GetVertexShader(&before_shader);
            std::vector<SunVertex> glow,streak;
            auto quad=[&](float radius,std::vector<SunVertex>& out){
                SunVertex a{256-radius-.5f,192-radius-.5f,.5f,1,0xffffffffu,0,0,0,0},b=a,c=a,d=a;
                b.x=256+radius-.5f;b.u=1;c.y=192+radius-.5f;c.v=1;d=b;d.y=c.y;d.v=1;
                for(const auto& q:{a,b,c,c,b,d})out.push_back(q);
            };quad(40,glow);quad(90,streak);
            // Poison a higher stage; the lamp transaction must disable it and restore it.
            n.SetTextureStageState(2,D3DTSS_COLOROP,D3DTOP_ADD);
            n.SetTextureStageState(2,D3DTSS_COLORARG1,D3DTA_CURRENT);
            n.SetTextureStageState(2,D3DTSS_COLORARG2,D3DTA_DIFFUSE);
            const auto hr=sun.lamp_sprites(n,glow,streak,nullptr,nullptr);
            DWORD shader=0,zwrite=0,alpha=0;n.GetVertexShader(&shader);n.GetRenderState(D3DRS_ZWRITEENABLE,&zwrite);n.GetRenderState(D3DRS_ALPHATESTENABLE,&alpha);
            DWORD stage2=0;n.GetTextureStageState(2,D3DTSS_COLOROP,&stage2);
            Ref<IDirect3DSurface8> target,depth;n.GetRenderTarget(&target.p);n.GetDepthStencilSurface(&depth.p);
            D3DVIEWPORT8 vp{};n.GetViewport(&vp);
            bool restored=shader==before_shader&&zwrite==TRUE&&alpha==FALSE&&stage2==D3DTOP_ADD&&target.p==sun.proof.target&&depth.p==sun.proof.depth&&vp.Width==512&&vp.Height==384&&!sun.transaction.pending();
            if(!check(n.EndScene(),"end"))return 3;
            std::vector<DWORD> image;if(!pixels(n,sun.proof.target,image))return 3;uint64_t sum=0;for(auto c:image)sum+=(c&255)+((c>>8)&255)+((c>>16)&255);energy.push_back(sum);
            bitmap(output/(L"msaa-"+std::to_wstring(samples)+L"-case-"+std::to_wstring(mode)+L".bmp"),image);
            report<<"{\"msaa\":"<<samples<<",\"case\":"<<mode<<",\"lamp_hr\":"<<DWORD(hr)<<",\"reason\":\""<<sun.reason<<"\",\"rgb_energy\":"<<sum<<",\"state_restored\":"<<(restored?"true":"false")<<",\"evidence\":\"isolated_D3D8_not_gameplay\"}\n";
            if(!restored||FAILED(hr))++failures;
        }
        if(energy[0]==0||energy[1]!=0||energy[2]!=0||energy[3]!=energy[0]||energy[4]!=energy[0])++failures;
    }
    DestroyWindow(window);std::cout<<"supported modes="<<supported<<" failures="<<failures<<"; isolated system D3D8, NOT GAMEPLAY\n";return failures||!supported?1:0;
}
