#pragma once
#include "state_tracker.hpp"
#include <atomic>
#include <memory>
#include <mutex>
#include <string>
#include <vector>

namespace gfx2 {
class Device8;
enum class BufferKind { Vertex, Index };
struct BufferProxyDescription {UINT bytes=0;DWORD usage=0;D3DPOOL pool=D3DPOOL_DEFAULT;bool valid=false;};
struct BufferMirror {
 struct Range {uint32_t begin=0,end=0;};
 BufferKind kind=BufferKind::Vertex;uint64_t generation=0,revision=0;UINT bytes=0;DWORD usage=0;D3DPOOL pool=D3DPOOL_DEFAULT;bool available=false,poisoned=false;
 std::vector<BYTE> data;std::vector<Range> initialized;std::string poison_reason;std::mutex mutex;
};

// The COM proxy observes CPU writes only. It never reads a D3DUSAGE_WRITEONLY
// buffer through Lock and never reads GPU memory.
class BufferProxyCore {
public:
 BufferProxyCore(Device8* owner, IUnknown* raw, void* proxy, BufferKind kind,
                 uint64_t generation, BufferProxyDescription description) noexcept;
 ~BufferProxyCore();
 BufferProxyCore(const BufferProxyCore&)=delete;
 BufferProxyCore& operator=(const BufferProxyCore&)=delete;
 IUnknown* raw_unknown() const noexcept { return static_cast<IUnknown*>(raw_); }
 void* raw_pointer() const noexcept { return raw_pointer_; }
 void* proxy_pointer() const noexcept { return proxy_; }
 bool registered() const noexcept { return registered_; }
 uint64_t generation() const noexcept { return generation_; }
 ULONG add_ref() noexcept;
 ULONG release() noexcept;
 HRESULT query(REFIID iid,void** out) noexcept;
 HRESULT get_device(IDirect3DDevice8** out) noexcept;
 HRESULT set_private(REFGUID guid,const void* data,DWORD size,DWORD flags) noexcept;
 HRESULT get_private(REFGUID guid,void* data,DWORD* size) noexcept;
 HRESULT free_private(REFGUID guid) noexcept;
 DWORD set_priority(DWORD priority) noexcept;
 DWORD get_priority() noexcept;
 void preload() noexcept;
 D3DRESOURCETYPE get_type() noexcept;
 HRESULT lock(UINT offset,UINT size,BYTE** out,DWORD flags) noexcept;
 HRESULT unlock() noexcept;
 void invalidate(const char* reason) noexcept;
 BufferKind kind() const noexcept { return kind_; }
private:
 struct PendingLock {BYTE* data=nullptr;uint32_t begin=0,end=0,flags=0;bool valid=false,readonly=false;};
 bool merge_range(uint32_t begin,uint32_t end) noexcept;
 void remove_range(uint32_t begin,uint32_t end) noexcept;
 void clear_ranges_locked() noexcept;
 void poison_locked(const char* reason) noexcept;
 Device8* owner_=nullptr;IDirect3DResource8* raw_=nullptr;void* raw_pointer_=nullptr;void* proxy_=nullptr;
 BufferKind kind_=BufferKind::Vertex;uint64_t generation_=0;UINT bytes_=0;DWORD usage_=0;D3DPOOL pool_=D3DPOOL_DEFAULT;
 std::shared_ptr<BufferMirror> mirror_;PendingLock lock_{};
 bool registered_=false;mutable std::mutex mutex_;std::atomic<ULONG> refs_{1};
};

class VertexBufferProxy final : public IDirect3DVertexBuffer8 {
public:
 VertexBufferProxy(Device8* owner,IDirect3DVertexBuffer8* raw,uint64_t generation) noexcept;
 BufferProxyCore& core() noexcept { return core_; }
 HRESULT STDMETHODCALLTYPE QueryInterface(REFIID,void**) override;
 ULONG STDMETHODCALLTYPE AddRef() override; ULONG STDMETHODCALLTYPE Release() override;
 HRESULT STDMETHODCALLTYPE GetDevice(IDirect3DDevice8**) override;
 HRESULT STDMETHODCALLTYPE SetPrivateData(REFGUID,const void*,DWORD,DWORD) override;
 HRESULT STDMETHODCALLTYPE GetPrivateData(REFGUID,void*,DWORD*) override;
 HRESULT STDMETHODCALLTYPE FreePrivateData(REFGUID) override;
 DWORD STDMETHODCALLTYPE SetPriority(DWORD) override; DWORD STDMETHODCALLTYPE GetPriority() override;
 void STDMETHODCALLTYPE PreLoad() override; D3DRESOURCETYPE STDMETHODCALLTYPE GetType() override;
 HRESULT STDMETHODCALLTYPE Lock(UINT,UINT,BYTE**,DWORD) override;
 HRESULT STDMETHODCALLTYPE Unlock() override; HRESULT STDMETHODCALLTYPE GetDesc(D3DVERTEXBUFFER_DESC*) override;
 IDirect3DVertexBuffer8* raw() const noexcept;
private: BufferProxyCore core_;
};

class IndexBufferProxy final : public IDirect3DIndexBuffer8 {
public:
 IndexBufferProxy(Device8* owner,IDirect3DIndexBuffer8* raw,uint64_t generation) noexcept;
 BufferProxyCore& core() noexcept { return core_; }
 HRESULT STDMETHODCALLTYPE QueryInterface(REFIID,void**) override;
 ULONG STDMETHODCALLTYPE AddRef() override; ULONG STDMETHODCALLTYPE Release() override;
 HRESULT STDMETHODCALLTYPE GetDevice(IDirect3DDevice8**) override;
 HRESULT STDMETHODCALLTYPE SetPrivateData(REFGUID,const void*,DWORD,DWORD) override;
 HRESULT STDMETHODCALLTYPE GetPrivateData(REFGUID,void*,DWORD*) override;
 HRESULT STDMETHODCALLTYPE FreePrivateData(REFGUID) override;
 DWORD STDMETHODCALLTYPE SetPriority(DWORD) override; DWORD STDMETHODCALLTYPE GetPriority() override;
 void STDMETHODCALLTYPE PreLoad() override; D3DRESOURCETYPE STDMETHODCALLTYPE GetType() override;
 HRESULT STDMETHODCALLTYPE Lock(UINT,UINT,BYTE**,DWORD) override;
 HRESULT STDMETHODCALLTYPE Unlock() override; HRESULT STDMETHODCALLTYPE GetDesc(D3DINDEXBUFFER_DESC*) override;
 IDirect3DIndexBuffer8* raw() const noexcept;
private: BufferProxyCore core_;
};

}
