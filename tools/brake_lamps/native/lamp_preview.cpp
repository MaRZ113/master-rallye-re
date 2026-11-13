// Brake Glow-ON native preview: renders an MRLP scene through Direct3D 9 fixed function with the
// per-draw states of the PS2 Port renderer and captures a 32-bit BMP. No game process is involved.
//
// The Python side (tools/brake_lamps/preview.py) stages the scene and chooses the states:
//   BrakeGlow=0 (PC): native lamp draws, core opaque MODULATE, halo SRCALPHA/INVSRCALPHA with ZWRITE on
//                     (the states fleet_lamp_native.hpp requires before it touches a lamp draw);
//   BrakeGlow=1 (PS2): core SELECTARG1 texture PS2BrakeOn, halo ONE/ONE ZWRITE off SELECTARG1 PS2BrakeGlow
//                     (LampTransaction::brake_on_pass / emissive_pass). ZENABLE/ZFUNC stay native (TRUE/LESSEQUAL).
//
// usage: mr-lamp-preview.exe <scene.mrlp> <capture.bmp>
#define WIN32_LEAN_AND_MEAN
#include <windows.h>
#include <d3d9.h>
#include <cmath>
#include <cstdint>
#include <cstdio>
#include <cstring>
#include <fstream>
#include <stdexcept>
#include <string>
#include <vector>
#pragma comment(lib, "d3d9.lib")
#pragma comment(lib, "user32.lib")

namespace {
struct Reader {
    std::vector<char> d; size_t p = 0;
    template <class T> T get() { if (p + sizeof(T) > d.size()) throw std::runtime_error("truncated scene"); T v; std::memcpy(&v, d.data() + p, sizeof v); p += sizeof v; return v; }
    void read(void* out, size_t n) { if (p + n > d.size()) throw std::runtime_error("truncated scene"); std::memcpy(out, d.data() + p, n); p += n; }
};
struct Vertex { float x, y, z; uint32_t color; float u, v; };
struct Texture { uint32_t w = 0, h = 0; std::vector<uint32_t> px; IDirect3DTexture9* gpu = nullptr; };
struct Draw { int32_t texture; uint32_t blend, zwrite, zenable, cull, colorop, alphatest; std::vector<Vertex> v; std::vector<uint32_t> i; };
struct V3 { float x, y, z; };
V3 sub(V3 a, V3 b) { return {a.x - b.x, a.y - b.y, a.z - b.z}; }
V3 cross(V3 a, V3 b) { return {a.y * b.z - a.z * b.y, a.z * b.x - a.x * b.z, a.x * b.y - a.y * b.x}; }
float dot(V3 a, V3 b) { return a.x * b.x + a.y * b.y + a.z * b.z; }
V3 norm(V3 a) { float l = std::sqrt(dot(a, a)); return {a.x / l, a.y / l, a.z / l}; }
void check(HRESULT hr, const char* what) { if (FAILED(hr)) { char b[160]; std::snprintf(b, sizeof b, "%s failed 0x%08lx", what, (unsigned long)hr); throw std::runtime_error(b); } }
D3DMATRIX identity() { D3DMATRIX m{}; m._11 = m._22 = m._33 = m._44 = 1; return m; }
}  // namespace

int main(int argc, char** argv) {
    try {
        if (argc != 3) throw std::runtime_error("usage: mr-lamp-preview <scene.mrlp> <capture.bmp>");
        Reader r; { std::ifstream f(argv[1], std::ios::binary); r.d.assign(std::istreambuf_iterator<char>(f), {}); }
        if (r.get<uint32_t>() != 0x504c524d) throw std::runtime_error("bad MRLP magic");
        if (r.get<uint32_t>() != 1) throw std::runtime_error("unsupported MRLP version");
        const uint32_t width = r.get<uint32_t>(), height = r.get<uint32_t>();
        if (width < 16 || height < 16 || width > 4096 || height > 4096) throw std::runtime_error("capture size budget");
        V3 eye = r.get<V3>(), target = r.get<V3>(), up = r.get<V3>();
        const float fov = r.get<float>(), znear = r.get<float>(), zfar = r.get<float>();
        const uint32_t clear = r.get<uint32_t>(), nt = r.get<uint32_t>(), nd = r.get<uint32_t>();
        if (nt > 256 || nd > 4096) throw std::runtime_error("scene count budget");
        std::vector<Texture> textures(nt);
        for (auto& t : textures) { t.w = r.get<uint32_t>(); t.h = r.get<uint32_t>(); if (!t.w || !t.h || t.w > 4096 || t.h > 4096) throw std::runtime_error("texture size"); t.px.resize(size_t(t.w) * t.h); r.read(t.px.data(), t.px.size() * 4); }
        std::vector<Draw> draws(nd);
        for (auto& d : draws) {
            d.texture = r.get<int32_t>(); d.blend = r.get<uint32_t>(); d.zwrite = r.get<uint32_t>(); d.zenable = r.get<uint32_t>();
            d.cull = r.get<uint32_t>(); d.colorop = r.get<uint32_t>(); d.alphatest = r.get<uint32_t>();
            const uint32_t nv = r.get<uint32_t>(), ni = r.get<uint32_t>();
            if (d.texture < -1 || d.texture >= int32_t(nt) || d.blend > 2 || d.cull < 1 || d.cull > 3 || d.colorop > 2 || nv > 1000000 || ni % 3 || ni > 3000000) throw std::runtime_error("invalid draw");
            d.v.resize(nv); d.i.resize(ni); r.read(d.v.data(), size_t(nv) * sizeof(Vertex)); r.read(d.i.data(), size_t(ni) * 4);
            for (auto i : d.i) if (i >= nv) throw std::runtime_error("index outside draw");
        }
        if (r.p != r.d.size()) throw std::runtime_error("trailing scene data");

        WNDCLASSA wc{}; wc.lpfnWndProc = DefWindowProcA; wc.hInstance = GetModuleHandleA(nullptr); wc.lpszClassName = "MRLampPreview"; RegisterClassA(&wc);
        HWND window = CreateWindowA(wc.lpszClassName, "MR lamp preview", WS_OVERLAPPEDWINDOW, 0, 0, int(width), int(height), nullptr, nullptr, wc.hInstance, nullptr);
        IDirect3D9* d3d = Direct3DCreate9(D3D_SDK_VERSION); if (!d3d) throw std::runtime_error("Direct3DCreate9");
        D3DPRESENT_PARAMETERS pp{}; pp.Windowed = TRUE; pp.SwapEffect = D3DSWAPEFFECT_DISCARD; pp.BackBufferFormat = D3DFMT_A8R8G8B8; pp.BackBufferWidth = width; pp.BackBufferHeight = height;
        pp.EnableAutoDepthStencil = TRUE; pp.AutoDepthStencilFormat = D3DFMT_D24S8; pp.hDeviceWindow = window;
        IDirect3DDevice9* dev = nullptr;
        check(d3d->CreateDevice(D3DADAPTER_DEFAULT, D3DDEVTYPE_HAL, window, D3DCREATE_SOFTWARE_VERTEXPROCESSING | D3DCREATE_FPU_PRESERVE, &pp, &dev), "CreateDevice");
        for (auto& t : textures) {
            check(dev->CreateTexture(t.w, t.h, 1, 0, D3DFMT_A8R8G8B8, D3DPOOL_MANAGED, &t.gpu, nullptr), "CreateTexture");
            D3DLOCKED_RECT lr; check(t.gpu->LockRect(0, &lr, nullptr, 0), "LockRect");
            for (uint32_t y = 0; y < t.h; ++y) std::memcpy(static_cast<char*>(lr.pBits) + size_t(y) * lr.Pitch, t.px.data() + size_t(y) * t.w, size_t(t.w) * 4);
            t.gpu->UnlockRect(0);
        }
        // Left-handed look-at / perspective, the native D3D convention of the game.
        V3 z = norm(sub(target, eye)), x = norm(cross(up, z)), y = cross(z, x);
        D3DMATRIX view = identity();
        view._11 = x.x; view._21 = x.y; view._31 = x.z; view._41 = -dot(x, eye);
        view._12 = y.x; view._22 = y.y; view._32 = y.z; view._42 = -dot(y, eye);
        view._13 = z.x; view._23 = z.y; view._33 = z.z; view._43 = -dot(z, eye);
        const float ys = 1.f / std::tan(fov * 3.14159265f / 360.f), xs = ys * float(height) / float(width);
        D3DMATRIX proj{}; proj._11 = xs; proj._22 = ys; proj._33 = zfar / (zfar - znear); proj._34 = 1; proj._43 = -znear * zfar / (zfar - znear);
        D3DMATRIX world = identity();
        check(dev->Clear(0, nullptr, D3DCLEAR_TARGET | D3DCLEAR_ZBUFFER, clear, 1.f, 0), "Clear");
        check(dev->BeginScene(), "BeginScene");
        dev->SetTransform(D3DTS_WORLD, &world); dev->SetTransform(D3DTS_VIEW, &view); dev->SetTransform(D3DTS_PROJECTION, &proj);
        dev->SetFVF(D3DFVF_XYZ | D3DFVF_DIFFUSE | D3DFVF_TEX1);
        dev->SetRenderState(D3DRS_LIGHTING, FALSE); dev->SetRenderState(D3DRS_ZFUNC, D3DCMP_LESSEQUAL); dev->SetRenderState(D3DRS_FOGENABLE, FALSE);
        dev->SetRenderState(D3DRS_ALPHAREF, 0x80); dev->SetRenderState(D3DRS_ALPHAFUNC, D3DCMP_GREATEREQUAL);
        for (unsigned s = 0; s < 2; ++s) { dev->SetSamplerState(s, D3DSAMP_MINFILTER, D3DTEXF_LINEAR); dev->SetSamplerState(s, D3DSAMP_MAGFILTER, D3DTEXF_LINEAR); dev->SetSamplerState(s, D3DSAMP_ADDRESSU, D3DTADDRESS_WRAP); dev->SetSamplerState(s, D3DSAMP_ADDRESSV, D3DTADDRESS_WRAP); }
        dev->SetTextureStageState(1, D3DTSS_COLOROP, D3DTOP_DISABLE); dev->SetTextureStageState(1, D3DTSS_ALPHAOP, D3DTOP_DISABLE);
        for (const auto& d : draws) {
            if (d.i.empty()) continue;
            dev->SetRenderState(D3DRS_ZENABLE, d.zenable ? D3DZB_TRUE : D3DZB_FALSE);
            dev->SetRenderState(D3DRS_ZWRITEENABLE, d.zwrite ? TRUE : FALSE);
            dev->SetRenderState(D3DRS_CULLMODE, d.cull);
            dev->SetRenderState(D3DRS_ALPHATESTENABLE, d.alphatest ? TRUE : FALSE);
            dev->SetRenderState(D3DRS_ALPHABLENDENABLE, d.blend ? TRUE : FALSE);
            dev->SetRenderState(D3DRS_SRCBLEND, d.blend == 2 ? D3DBLEND_ONE : D3DBLEND_SRCALPHA);
            dev->SetRenderState(D3DRS_DESTBLEND, d.blend == 2 ? D3DBLEND_ONE : D3DBLEND_INVSRCALPHA);
            dev->SetTexture(0, d.texture >= 0 ? textures[d.texture].gpu : nullptr);
            const DWORD op = d.texture < 0 || d.colorop == 2 ? D3DTOP_SELECTARG2 : d.colorop == 1 ? D3DTOP_SELECTARG1 : D3DTOP_MODULATE;
            dev->SetTextureStageState(0, D3DTSS_COLOROP, op); dev->SetTextureStageState(0, D3DTSS_COLORARG1, D3DTA_TEXTURE); dev->SetTextureStageState(0, D3DTSS_COLORARG2, D3DTA_DIFFUSE);
            dev->SetTextureStageState(0, D3DTSS_ALPHAOP, op); dev->SetTextureStageState(0, D3DTSS_ALPHAARG1, D3DTA_TEXTURE); dev->SetTextureStageState(0, D3DTSS_ALPHAARG2, D3DTA_DIFFUSE);
            check(dev->DrawIndexedPrimitiveUP(D3DPT_TRIANGLELIST, 0, UINT(d.v.size()), UINT(d.i.size() / 3), d.i.data(), D3DFMT_INDEX32, d.v.data(), sizeof(Vertex)), "Draw");
        }
        check(dev->EndScene(), "EndScene");
        IDirect3DSurface9 *rt = nullptr, *sys = nullptr;
        check(dev->GetRenderTarget(0, &rt), "GetRenderTarget");
        check(dev->CreateOffscreenPlainSurface(width, height, D3DFMT_A8R8G8B8, D3DPOOL_SYSTEMMEM, &sys, nullptr), "Offscreen");
        check(dev->GetRenderTargetData(rt, sys), "GetRenderTargetData");
        D3DLOCKED_RECT lr; check(sys->LockRect(&lr, nullptr, D3DLOCK_READONLY), "LockRect capture");
        std::ofstream out(argv[2], std::ios::binary);
        BITMAPFILEHEADER fh{}; BITMAPINFOHEADER ih{};
        ih.biSize = sizeof ih; ih.biWidth = LONG(width); ih.biHeight = -LONG(height); ih.biPlanes = 1; ih.biBitCount = 32; ih.biCompression = BI_RGB;
        fh.bfType = 0x4d42; fh.bfOffBits = sizeof fh + sizeof ih; fh.bfSize = fh.bfOffBits + width * height * 4;
        out.write(reinterpret_cast<char*>(&fh), sizeof fh); out.write(reinterpret_cast<char*>(&ih), sizeof ih);
        for (uint32_t row = 0; row < height; ++row) out.write(static_cast<char*>(lr.pBits) + size_t(row) * lr.Pitch, std::streamsize(width) * 4);
        sys->UnlockRect(); sys->Release(); rt->Release();
        for (auto& t : textures) if (t.gpu) t.gpu->Release();
        dev->Release(); d3d->Release(); DestroyWindow(window);
        if (!out) throw std::runtime_error("capture write failed");
        return 0;
    } catch (const std::exception& e) { std::fprintf(stderr, "mr-lamp-preview: %s\n", e.what()); return 1; }
}
