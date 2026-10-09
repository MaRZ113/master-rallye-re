#include "buffer_provenance.hpp"
#include "wrappers.hpp"

#include <algorithm>
#include <cstring>

namespace gfx2 {
namespace {
constexpr UINT MAX_BUFFER_SHADOW = 8u * 1024u * 1024u;
constexpr DWORD KNOWN_WRITE_FLAGS = D3DLOCK_NOSYSLOCK | D3DLOCK_NOOVERWRITE |
                                    D3DLOCK_DISCARD;
constexpr size_t MAX_INITIALIZED_RANGES = 4096;

BufferProxyDescription describe(IDirect3DVertexBuffer8* raw) noexcept {
    D3DVERTEXBUFFER_DESC desc{};
    if (!raw || FAILED(raw->GetDesc(&desc))) return {};
    return {desc.Size, desc.Usage, desc.Pool, true};
}

BufferProxyDescription describe(IDirect3DIndexBuffer8* raw) noexcept {
    D3DINDEXBUFFER_DESC desc{};
    if (!raw || FAILED(raw->GetDesc(&desc))) return {};
    return {desc.Size, desc.Usage, desc.Pool, true};
}
}

BufferProxyCore::BufferProxyCore(Device8* owner, IUnknown* raw, void* proxy,
                                 BufferKind kind, uint64_t generation,
                                 BufferProxyDescription description) noexcept
    : owner_(owner), raw_(static_cast<IDirect3DResource8*>(raw)), raw_pointer_(raw), proxy_(proxy), kind_(kind),
      generation_(generation), bytes_(description.bytes), usage_(description.usage),
      pool_(description.pool) {
    if (owner_) owner_->AddRef();
    if (!owner_ || !raw_ || !proxy_) return;

    registered_ = owner_->register_buffer_proxy(raw_pointer_, this);
    if (!registered_) return;
    if (!generation_ || !description.valid || !bytes_ ||
        bytes_ > MAX_BUFFER_SHADOW || !owner_->visuals.effective.foliage_diagnostics) {
        return;
    }
    mirror_ = owner_->open_buffer_mirror(raw_pointer_, kind_, generation_, bytes_, usage_, pool_);
}

BufferProxyCore::~BufferProxyCore() {
    if (owner_) owner_->forget_buffer_proxy(raw_pointer_, this);
    if (owner_) owner_->Release();
}

ULONG BufferProxyCore::add_ref() noexcept {
    if (raw_) raw_->AddRef();
    return ++refs_;
}

ULONG BufferProxyCore::release() noexcept {
    const ULONG remaining = --refs_;
    if (raw_) raw_->Release();
    if (remaining == 0) {
        if (kind_ == BufferKind::Vertex) delete static_cast<VertexBufferProxy*>(proxy_);
        else delete static_cast<IndexBufferProxy*>(proxy_);
    }
    return remaining;
}

HRESULT BufferProxyCore::query(REFIID iid, void** out) noexcept {
    if (!raw_ || !out) return E_POINTER;
    HRESULT hr = raw_->QueryInterface(iid, out);
    if (FAILED(hr) || !*out) return hr;

    void* proxy_interface = nullptr;
    if (iid == IID_IUnknown ||
        (kind_ == BufferKind::Vertex && iid == IID_IDirect3DVertexBuffer8) ||
        (kind_ == BufferKind::Index && iid == IID_IDirect3DIndexBuffer8)) {
        proxy_interface = proxy_;
    } else if (iid == IID_IDirect3DResource8) {
        if (kind_ == BufferKind::Vertex) {
            proxy_interface = static_cast<IDirect3DResource8*>(
                static_cast<VertexBufferProxy*>(proxy_));
        } else {
            proxy_interface = static_cast<IDirect3DResource8*>(
                static_cast<IndexBufferProxy*>(proxy_));
        }
    }

    if (proxy_interface) {
        static_cast<IUnknown*>(*out)->Release();
        *out = proxy_interface;
        add_ref();
        return hr;
    }

    // An unrecognized successful QI exposes the raw resource. Keep the exact
    // API result, but revoke the CPU mirror because subsequent writes can bypass
    // the observed Lock/Unlock methods.
    invalidate("successful_unknown_query_interface_raw_escape");
    return hr;
}

HRESULT BufferProxyCore::get_device(IDirect3DDevice8** out) noexcept {
    if (!out) return E_POINTER;
    *out = nullptr;
    if (!raw_ || !owner_) return D3DERR_INVALIDCALL;

    IDirect3DDevice8* device = nullptr;
    HRESULT hr = raw_->GetDevice(&device);
    if (FAILED(hr) || !device) return hr;
    if (device == owner_->native()) {
        // Transfer the reference returned by the native GetDevice call to the
        // wrapper's logical reference count.
        owner_->adopt();
        *out = owner_;
        return hr;
    }

    *out = device;
    invalidate("get_device_owner_mismatch");
    return hr;
}

HRESULT BufferProxyCore::set_private(REFGUID guid, const void* data,
                                     DWORD size, DWORD flags) noexcept {
    return raw_ ? raw_->SetPrivateData(guid, data, size, flags) : D3DERR_INVALIDCALL;
}
HRESULT BufferProxyCore::get_private(REFGUID guid, void* data, DWORD* size) noexcept {
    return raw_ ? raw_->GetPrivateData(guid, data, size) : D3DERR_INVALIDCALL;
}
HRESULT BufferProxyCore::free_private(REFGUID guid) noexcept {
    return raw_ ? raw_->FreePrivateData(guid) : D3DERR_INVALIDCALL;
}
DWORD BufferProxyCore::set_priority(DWORD priority) noexcept {
    return raw_ ? raw_->SetPriority(priority) : 0;
}
DWORD BufferProxyCore::get_priority() noexcept { return raw_ ? raw_->GetPriority() : 0; }
void BufferProxyCore::preload() noexcept { if (raw_) raw_->PreLoad(); }
D3DRESOURCETYPE BufferProxyCore::get_type() noexcept {
    return raw_ ? raw_->GetType() : D3DRTYPE_FORCE_DWORD;
}

void BufferProxyCore::clear_ranges_locked() noexcept {
    if (mirror_) mirror_->initialized.clear();
}

void BufferProxyCore::poison_locked(const char* reason) noexcept {
    if (!mirror_) return;
    std::lock_guard<std::mutex> lock(mirror_->mutex);
    mirror_->poisoned = true;
    clear_ranges_locked();
    if (mirror_->revision != UINT64_MAX) ++mirror_->revision;
    try {
        mirror_->poison_reason = reason ? reason : "unknown_write_provenance";
    } catch (...) {
        mirror_->poison_reason.clear();
    }
}

bool BufferProxyCore::merge_range(uint32_t begin, uint32_t end) noexcept {
    if (!mirror_ || begin >= end || end > bytes_ ||
        mirror_->initialized.size() >= MAX_INITIALIZED_RANGES) return false;
    try {
        BufferMirror::Range add{begin, end};
        std::vector<BufferMirror::Range> merged;
        merged.reserve(mirror_->initialized.size() + 1);
        bool inserted = false;
        for (const auto& range : mirror_->initialized) {
            if (range.end < add.begin) {
                merged.push_back(range);
                continue;
            }
            if (add.end < range.begin) {
                if (!inserted) {
                    merged.push_back(add);
                    inserted = true;
                }
                merged.push_back(range);
                continue;
            }
            add.begin = std::min(add.begin, range.begin);
            add.end = std::max(add.end, range.end);
        }
        if (!inserted) merged.push_back(add);
        if (merged.size() > MAX_INITIALIZED_RANGES) return false;
        mirror_->initialized.swap(merged);
        return true;
    } catch (...) {
        return false;
    }
}

void BufferProxyCore::remove_range(uint32_t begin, uint32_t end) noexcept {
    if (!mirror_) return;
    try {
        std::vector<BufferMirror::Range> kept;
        kept.reserve(mirror_->initialized.size() + 1);
        for (const auto& range : mirror_->initialized) {
            if (range.end <= begin || range.begin >= end) {
                kept.push_back(range);
                continue;
            }
            if (range.begin < begin) kept.push_back({range.begin, begin});
            if (range.end > end) kept.push_back({end, range.end});
        }
        mirror_->initialized.swap(kept);
    } catch (...) {
        clear_ranges_locked();
    }
}

void BufferProxyCore::invalidate(const char* reason) noexcept {
    std::lock_guard<std::mutex> core_lock(mutex_);
    poison_locked(reason);
    lock_ = PendingLock{};
}

HRESULT BufferProxyCore::lock(UINT offset, UINT size, BYTE** out, DWORD flags) noexcept {
    if (!raw_ || !owner_) return D3DERR_INVALIDCALL;
    auto trace_guard = owner_->trace.guard();
    HRESULT hr = kind_ == BufferKind::Vertex
        ? static_cast<VertexBufferProxy*>(proxy_)->raw()->Lock(offset, size, out, flags)
        : static_cast<IndexBufferProxy*>(proxy_)->raw()->Lock(offset, size, out, flags);
    if (FAILED(hr)) return hr;

    std::lock_guard<std::mutex> core_lock(mutex_);
    if (lock_.data || lock_.valid || lock_.readonly) {
        poison_locked("nested_successful_lock");
        lock_ = PendingLock{};
        return hr;
    }

    lock_ = PendingLock{};
    const uint64_t end = size ? uint64_t(offset) + size : bytes_;
    const DWORD unknown_flags = flags & ~(KNOWN_WRITE_FLAGS | D3DLOCK_READONLY);
    const bool contradictory_write_hints =
        (flags & D3DLOCK_DISCARD) != 0 && (flags & D3DLOCK_NOOVERWRITE) != 0;
    if (!mirror_ || !mirror_->available || unknown_flags != 0 || contradictory_write_hints ||
        offset > bytes_ || end > bytes_ || end < offset) {
        poison_locked("unknown_or_out_of_range_lock");
        if ((flags & D3DLOCK_READONLY) != 0) lock_.readonly = true;
        return hr;
    }

    if ((flags & D3DLOCK_READONLY) != 0) {
        // Read-only locks cannot change bytes, but contradictory or write-hint
        // combinations are outside the mirror's proven contract.
        constexpr DWORD READONLY_ALLOWED = D3DLOCK_READONLY | D3DLOCK_NOSYSLOCK;
        if ((flags & ~READONLY_ALLOWED) != 0) poison_locked("unexpected_readonly_lock_flags");
        lock_.readonly = true;
        return hr;
    }

    {
        std::lock_guard<std::mutex> mirror_lock(mirror_->mutex);
        if (mirror_->poisoned) return hr;
        if ((flags & D3DLOCK_DISCARD) != 0) {
            clear_ranges_locked();
            if (mirror_->revision != UINT64_MAX) ++mirror_->revision;
        }
    }

    BYTE* data = nullptr;
    if (!out || !safe_copy(&data, out, sizeof(data)) || !data) {
        poison_locked("successful_lock_without_observable_pointer");
        return hr;
    }

    lock_ = {data, offset, static_cast<uint32_t>(end), flags, true, false};
    return hr;
}

HRESULT BufferProxyCore::unlock() noexcept {
    if (!raw_ || !owner_) return D3DERR_INVALIDCALL;
    auto trace_guard = owner_->trace.guard();

    PendingLock pending{};
    {
        std::lock_guard<std::mutex> core_lock(mutex_);
        pending = lock_;
        lock_ = PendingLock{};
    }

    std::vector<BYTE> copy;
    bool captured = false;
    const size_t length = pending.end >= pending.begin
        ? static_cast<size_t>(pending.end - pending.begin) : 0;
    if (pending.valid && mirror_ && length && owner_->reserve_buffer_copy_bytes(length)) {
        try {
            copy.resize(length);
            captured = safe_copy(copy.data(), pending.data, length);
        } catch (...) {
            captured = false;
        }
    }

    HRESULT hr = kind_ == BufferKind::Vertex
        ? static_cast<VertexBufferProxy*>(proxy_)->raw()->Unlock()
        : static_cast<IndexBufferProxy*>(proxy_)->raw()->Unlock();

    std::lock_guard<std::mutex> core_lock(mutex_);
    if (!mirror_) return hr;
    std::lock_guard<std::mutex> mirror_lock(mirror_->mutex);
    if (FAILED(hr)) {
        mirror_->poisoned = true;
        clear_ranges_locked();
        if (mirror_->revision != UINT64_MAX) ++mirror_->revision;
        try { mirror_->poison_reason = "native_unlock_failed"; } catch (...) {}
        return hr;
    }

    if (pending.readonly) return hr;
    if (!pending.valid) {
        mirror_->poisoned = true;
        clear_ranges_locked();
        if (mirror_->revision != UINT64_MAX) ++mirror_->revision;
        try { mirror_->poison_reason = "unlock_without_tracked_write_lock"; } catch (...) {}
        return hr;
    }
    if (mirror_->poisoned) return hr;
    if (length == 0) return hr;
    if (!captured) {
        remove_range(pending.begin, pending.end);
        if (mirror_->revision != UINT64_MAX) ++mirror_->revision;
        try { mirror_->poison_reason = "cpu_write_copy_budget_or_safe_copy_failed"; } catch (...) {}
        return hr;
    }

    std::memcpy(mirror_->data.data() + pending.begin, copy.data(), copy.size());
    if (!merge_range(pending.begin, pending.end)) {
        mirror_->poisoned = true;
        clear_ranges_locked();
        try { mirror_->poison_reason = "initialized_range_budget_exceeded"; } catch (...) {}
    }
    if (mirror_->revision != UINT64_MAX) ++mirror_->revision;
    return hr;
}

VertexBufferProxy::VertexBufferProxy(Device8* owner, IDirect3DVertexBuffer8* raw,
                                     uint64_t generation) noexcept
    : core_(owner, static_cast<IUnknown*>(raw), this, BufferKind::Vertex,
            generation, describe(raw)) {}

IDirect3DVertexBuffer8* VertexBufferProxy::raw() const noexcept {
    return static_cast<IDirect3DVertexBuffer8*>(core_.raw_unknown());
}

HRESULT STDMETHODCALLTYPE VertexBufferProxy::QueryInterface(REFIID iid, void** out) { return core_.query(iid, out); }
ULONG STDMETHODCALLTYPE VertexBufferProxy::AddRef() { return core_.add_ref(); }
ULONG STDMETHODCALLTYPE VertexBufferProxy::Release() { return core_.release(); }
HRESULT STDMETHODCALLTYPE VertexBufferProxy::GetDevice(IDirect3DDevice8** out) { return core_.get_device(out); }
HRESULT STDMETHODCALLTYPE VertexBufferProxy::SetPrivateData(REFGUID guid, const void* data, DWORD size, DWORD flags) { return core_.set_private(guid, data, size, flags); }
HRESULT STDMETHODCALLTYPE VertexBufferProxy::GetPrivateData(REFGUID guid, void* data, DWORD* size) { return core_.get_private(guid, data, size); }
HRESULT STDMETHODCALLTYPE VertexBufferProxy::FreePrivateData(REFGUID guid) { return core_.free_private(guid); }
DWORD STDMETHODCALLTYPE VertexBufferProxy::SetPriority(DWORD priority) { return core_.set_priority(priority); }
DWORD STDMETHODCALLTYPE VertexBufferProxy::GetPriority() { return core_.get_priority(); }
void STDMETHODCALLTYPE VertexBufferProxy::PreLoad() { core_.preload(); }
D3DRESOURCETYPE STDMETHODCALLTYPE VertexBufferProxy::GetType() { return core_.get_type(); }
HRESULT STDMETHODCALLTYPE VertexBufferProxy::Lock(UINT offset, UINT size, BYTE** out, DWORD flags) { return core_.lock(offset, size, out, flags); }
HRESULT STDMETHODCALLTYPE VertexBufferProxy::Unlock() { return core_.unlock(); }
HRESULT STDMETHODCALLTYPE VertexBufferProxy::GetDesc(D3DVERTEXBUFFER_DESC* desc) { return raw()->GetDesc(desc); }

IndexBufferProxy::IndexBufferProxy(Device8* owner, IDirect3DIndexBuffer8* raw,
                                   uint64_t generation) noexcept
    : core_(owner, static_cast<IUnknown*>(raw), this, BufferKind::Index,
            generation, describe(raw)) {}

IDirect3DIndexBuffer8* IndexBufferProxy::raw() const noexcept {
    return static_cast<IDirect3DIndexBuffer8*>(core_.raw_unknown());
}

HRESULT STDMETHODCALLTYPE IndexBufferProxy::QueryInterface(REFIID iid, void** out) { return core_.query(iid, out); }
ULONG STDMETHODCALLTYPE IndexBufferProxy::AddRef() { return core_.add_ref(); }
ULONG STDMETHODCALLTYPE IndexBufferProxy::Release() { return core_.release(); }
HRESULT STDMETHODCALLTYPE IndexBufferProxy::GetDevice(IDirect3DDevice8** out) { return core_.get_device(out); }
HRESULT STDMETHODCALLTYPE IndexBufferProxy::SetPrivateData(REFGUID guid, const void* data, DWORD size, DWORD flags) { return core_.set_private(guid, data, size, flags); }
HRESULT STDMETHODCALLTYPE IndexBufferProxy::GetPrivateData(REFGUID guid, void* data, DWORD* size) { return core_.get_private(guid, data, size); }
HRESULT STDMETHODCALLTYPE IndexBufferProxy::FreePrivateData(REFGUID guid) { return core_.free_private(guid); }
DWORD STDMETHODCALLTYPE IndexBufferProxy::SetPriority(DWORD priority) { return core_.set_priority(priority); }
DWORD STDMETHODCALLTYPE IndexBufferProxy::GetPriority() { return core_.get_priority(); }
void STDMETHODCALLTYPE IndexBufferProxy::PreLoad() { core_.preload(); }
D3DRESOURCETYPE STDMETHODCALLTYPE IndexBufferProxy::GetType() { return core_.get_type(); }
HRESULT STDMETHODCALLTYPE IndexBufferProxy::Lock(UINT offset, UINT size, BYTE** out, DWORD flags) { return core_.lock(offset, size, out, flags); }
HRESULT STDMETHODCALLTYPE IndexBufferProxy::Unlock() { return core_.unlock(); }
HRESULT STDMETHODCALLTYPE IndexBufferProxy::GetDesc(D3DINDEXBUFFER_DESC* desc) { return raw()->GetDesc(desc); }

}
