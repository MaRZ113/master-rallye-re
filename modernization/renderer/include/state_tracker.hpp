#pragma once
#include "sdk.hpp"
#include <array>
#include <cstring>
#include <cstdint>
#include <type_traits>
#include <unordered_map>
namespace gfx2 {
bool safe_copy(void* dst, const void* src, size_t bytes) noexcept;
template<class T> struct Known { bool known=false; T value{};
 void set(T v) noexcept { value=v;known=true; }
 void read(const T* p) noexcept { known=p && safe_copy(&value,p,sizeof(T)); }
};
struct Stream { uintptr_t pointer=0; uint32_t stride=0; };
struct Indices { uintptr_t pointer=0; uint32_t base=0; };
struct Args { std::array<uintptr_t,8> a{}; };
template<class T> uintptr_t word(T v) noexcept {
 if constexpr(std::is_null_pointer_v<T>) return 0;
 else if constexpr(std::is_pointer_v<T>) return reinterpret_cast<uintptr_t>(v);
 else if constexpr(std::is_floating_point_v<T>) {uint32_t b;std::memcpy(&b,&v,4);return b;}
 else return static_cast<uintptr_t>(v);
}
template<class... T> Args pack(T... v) noexcept { static_assert(sizeof...(v)<=8);return {{word(v)...}}; }
inline constexpr uint32_t RS_KEYS[]={7,14,23,15,24,25,27,19,20,22,28,34,35,140,36,37,38,137,139,29,143,141,136,142};
inline constexpr uint32_t MATRIX_KEYS[]={256,2,3,16,17};
struct Snapshot {
 std::array<Known<uint32_t>,24> rs{};
 std::array<std::array<Known<uint32_t>,32>,8> tss{};
 std::array<Known<D3DMATRIX>,5> matrices{};
 Known<D3DVIEWPORT8> viewport;
 Known<uint32_t> vertex_shader,pixel_shader;
 std::array<Known<uintptr_t>,8> textures{};
 std::array<Known<Stream>,16> streams{};
 Known<Indices> indices;
 Known<uintptr_t> target,depth;
};
struct Shadow {
 std::array<Known<uint32_t>,256> rs{};
 std::array<std::array<Known<uint32_t>,64>,8> tss{};
 std::array<Known<D3DMATRIX>,512> matrices{};
 Snapshot bindings;
 bool recording=false;
 void invalidate() noexcept;
 void update(uint32_t slot,const Args& args,uint32_t result) noexcept;
 Snapshot snapshot() const noexcept;
};
struct CaptureControl {
 bool key_down=false,pending=false,active=false,boundary=false;
 void poll(bool down) noexcept { if(down&&!key_down)pending=true;key_down=down; }
 void finish_present() noexcept {boundary=true;active=pending;pending=false;}
 void abort() noexcept {active=false;pending=false;}
};
struct Resource {uint64_t serial=0; uint32_t method=0; uintptr_t creation_caller=0; Args args;
 Known<uint32_t> pool;bool reset_survivor=false;};
struct ResourceRegistry {
 uint64_t next_serial=0; std::unordered_map<uintptr_t,Resource> items;
 Resource add(uintptr_t pointer,uint32_t method,const Args& args,uintptr_t creation_caller=0);
 uint64_t generation(uintptr_t pointer) const noexcept;
 size_t successful_reset() noexcept;
};
}
