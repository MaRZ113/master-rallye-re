"""Colin McRae Rally 04 (PC) car P3D -> mesh blocks (diagnostic reader).

File: 'CP3D' u16 1, u8 7, u8 2, u32 size; the rest is a memory image whose pointers are file offsets.
Mesh block: char name[12] (empty = same material as before), u32 index_count, u32 0,
u32 max_index, ..., u32 vertex_ptr (== its own offset + 12), u32 1, u32 0; vertices
float pos[3], float normal[3], u32 colour, float uv[2] (36 B); then u32 index_ptr (== own
offset + 12), u32 1, u32 0, u16 indices (triangle strip, repeated indices = restarts).
"""
import struct, sys

ZERO = bytes(1)


def _ptrs(d):
    return [i for i in range(8, len(d) - 12, 4) if struct.unpack_from('<I', d, i)[0] == i + 12]


def blocks(d):
    P = _ptrs(d); out = []; k = 0
    while k + 1 < len(P):
        i = P[k]; p = i + 12; j = P[k + 1]; nv = (j - p) // 36
        if nv <= 0 or (j - p) % 36:
            k += 1; continue
        limit = P[k + 2] - 48 if k + 2 < len(P) else len(d)
        I = []; o = j + 12
        while o + 2 <= limit:
            v = struct.unpack_from('<H', d, o)[0]
            if v >= nv: break
            I.append(v); o += 2
        hdr = struct.unpack_from('<3I', d, i - 36)
        raw = d[i - 48:i - 36].split(ZERO)[0]
        name = raw.decode('latin-1') if raw and all(32 < c < 127 for c in raw) else ''
        if 2 < hdr[0] <= len(I): I = I[:hdr[0]]
        V = [struct.unpack_from('<6fI2f', d, p + 36 * q) for q in range(nv)]
        out.append({'offset': i, 'name': name, 'nverts': nv, 'nidx': len(I), 'header': hdr, 'V': V, 'I': I})
        k += 2
    return out


def strip_tris(I):
    T = []
    for k in range(len(I) - 2):
        a, b, c = I[k], I[k + 1], I[k + 2]
        if a == b or b == c or a == c: continue
        T.append((a, b, c) if k % 2 == 0 else (b, a, c))
    return T


if __name__ == '__main__':
    d = open(sys.argv[1], 'rb').read()
    for b in blocks(d):
        print(hex(b['offset']), b['name'] or '-', b['nverts'], b['nidx'], b['header'], len(strip_tris(b['I'])))
