// Standalone native API experiment: synthetic image, hidden own window, no game access.
#include "reflection_capture.hpp"
#include <iostream>
#include <cstring>
using namespace gfx2::ps2port;
template<class T> void drop(T*& p){if(p)p->Release();p=nullptr;}
int main(){
    wchar_t path[MAX_PATH]{};GetSystemDirectoryW(path,MAX_PATH);
    wcscat_s(path,L"\\d3d8.dll");HMODULE module=LoadLibraryW(path);
    auto create=module?reinterpret_cast<IDirect3D8*(WINAPI*)(UINT)>(GetProcAddress(module,"Direct3DCreate8")):nullptr;
    IDirect3D8* root=create?create(D3D_SDK_VERSION):nullptr;
    if(!root){std::cout<<"{\"status\":\"D3D8_UNAVAILABLE\"}\n";return 2;}
    HWND window=CreateWindowExW(0,L"STATIC",L"PS2 native API smoke",WS_OVERLAPPEDWINDOW,
        0,0,640,480,nullptr,nullptr,GetModuleHandleW(nullptr),nullptr);
    D3DDISPLAYMODE display{};root->GetAdapterDisplayMode(D3DADAPTER_DEFAULT,&display);
    for(UINT samples:{0u,2u,4u})for(bool precision:{false,true}){
        auto type=static_cast<D3DMULTISAMPLE_TYPE>(samples);
        HRESULT caps=root->CheckDeviceMultiSampleType(D3DADAPTER_DEFAULT,D3DDEVTYPE_HAL,display.Format,TRUE,type);
        D3DPRESENT_PARAMETERS p{};p.BackBufferWidth=640;p.BackBufferHeight=480;
        p.BackBufferFormat=display.Format;p.BackBufferCount=1;p.MultiSampleType=type;
        p.SwapEffect=D3DSWAPEFFECT_DISCARD;p.hDeviceWindow=window;p.Windowed=TRUE;
        IDirect3DDevice8* device=nullptr;
        HRESULT created=FAILED(caps)?caps:root->CreateDevice(D3DADAPTER_DEFAULT,D3DDEVTYPE_HAL,window,
            D3DCREATE_SOFTWARE_VERTEXPROCESSING,&p,&device);
        IDirect3DTexture8* env=nullptr;
        IDirect3DSurface8* output=nullptr;
        HRESULT uploaded=E_PENDING,begin=E_PENDING,end=E_PENDING,hr=E_PENDING,readback=E_PENDING;
        DWORD center_pixel=0;
        ReflectionCaptureStatus result;
        if(SUCCEEDED(created)&&device){
            uploaded=device->CreateTexture(64,64,1,0,D3DFMT_A8R8G8B8,D3DPOOL_MANAGED,&env);
            if(SUCCEEDED(uploaded)&&env){D3DLOCKED_RECT lock{};uploaded=env->LockRect(0,&lock,nullptr,0);
                if(SUCCEEDED(uploaded)){for(UINT y=0;y<64;++y)for(UINT x=0;x<64;++x)
                    reinterpret_cast<DWORD*>(static_cast<BYTE*>(lock.pBits)+y*lock.Pitch)[x]=0xff204060;
                    uploaded=env->UnlockRect(0);}}
            begin=device->BeginScene();
            if(SUCCEEDED(begin)&&SUCCEEDED(uploaded)){
                device->Clear(0,nullptr,D3DCLEAR_TARGET,0xff406020,1.f,0);
                MixedReflectionCapture capture;capture.prefer_16bit(precision);
                hr=capture.capture(*device,env,1,false);result=capture.last_status();
                if(SUCCEEDED(hr)&&capture.ready_texture(1))capture.ready_texture(1)->GetSurfaceLevel(0,&output);
                // A successful same-frame repeat must use the already composed texture.
                if(SUCCEEDED(hr)&&capture.capture(*device,env,1,false)!=S_OK)hr=E_FAIL;
                capture.release();
            }
            if(SUCCEEDED(begin))end=device->EndScene();
            if(output){
                D3DSURFACE_DESC desc{};IDirect3DSurface8* cpu=nullptr;
                readback=output->GetDesc(&desc);
                if(SUCCEEDED(readback))readback=device->CreateImageSurface(64,64,desc.Format,&cpu);
                if(SUCCEEDED(readback)&&cpu)readback=device->CopyRects(output,nullptr,0,cpu,nullptr);
                if(SUCCEEDED(readback)&&cpu){D3DLOCKED_RECT lock{};readback=cpu->LockRect(&lock,nullptr,D3DLOCK_READONLY);
                    if(SUCCEEDED(readback)){const UINT bytes=desc.Format==D3DFMT_A1R5G5B5?2:4;
                        std::memcpy(&center_pixel,static_cast<BYTE*>(lock.pBits)+32*lock.Pitch+32*bytes,bytes);
                        readback=cpu->UnlockRect();}}
                drop(cpu);
            }
        }
        std::cout<<"{\"samples\":"<<samples<<",\"precision16\":"<<(precision?"true":"false")
            <<",\"caps_hr\":"<<static_cast<unsigned long>(caps)<<",\"create_hr\":"<<static_cast<unsigned long>(created)
            <<",\"upload_hr\":"<<static_cast<unsigned long>(uploaded)<<",\"begin_hr\":"<<static_cast<unsigned long>(begin)
            <<",\"capture_hr\":"<<static_cast<unsigned long>(hr)<<",\"copy_hr\":"<<static_cast<unsigned long>(result.copy_hr)
            <<",\"restore_hr\":"<<static_cast<unsigned long>(result.restore_hr)<<",\"end_hr\":"<<static_cast<unsigned long>(end)
            <<",\"target_format\":"<<static_cast<UINT>(result.target_format)
            <<",\"actual_source_samples\":"<<static_cast<UINT>(result.source_multisample)
            <<",\"readback_hr\":"<<static_cast<unsigned long>(readback)<<",\"center_pixel_raw\":"<<center_pixel
            <<",\"reason\":\""<<result.reason<<"\",\"private_draws\":"<<result.private_draws<<"}\n";
        drop(output);drop(env);drop(device);
    }
    DestroyWindow(window);drop(root);FreeLibrary(module);return 0;
}
