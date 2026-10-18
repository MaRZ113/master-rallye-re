"""Minimal PCSX2 GSDump (state v9) reader: header, screenshot, GIF packet replay of register state.

Collects every vertex kick with the GS state that applies to it, grouped into draw states.
Read-only research helper; no rasterisation.
"""
import struct, sys, json
from collections import defaultdict, Counter

AD = {0x00:'PRIM',0x01:'RGBAQ',0x02:'ST',0x03:'UV',0x04:'XYZF2',0x05:'XYZ2',0x06:'TEX0_1',0x07:'TEX0_2',
      0x08:'CLAMP_1',0x09:'CLAMP_2',0x0a:'FOG',0x0c:'XYZF3',0x0d:'XYZ3',0x14:'TEX1_1',0x15:'TEX1_2',
      0x18:'XYOFFSET_1',0x19:'XYOFFSET_2',0x1a:'PRMODECONT',0x1b:'PRMODE',0x3b:'TEXA',0x3d:'FOGCOL',
      0x40:'SCISSOR_1',0x41:'SCISSOR_2',0x42:'ALPHA_1',0x43:'ALPHA_2',0x44:'DIMX',0x45:'DTHE',0x46:'COLCLAMP',
      0x47:'TEST_1',0x48:'TEST_2',0x49:'PABE',0x4a:'FBA_1',0x4b:'FBA_2',0x4c:'FRAME_1',0x4d:'FRAME_2',
      0x4e:'ZBUF_1',0x4f:'ZBUF_2',0x50:'BITBLTBUF',0x51:'TRXPOS',0x52:'TRXREG',0x53:'TRXDIR'}


def read_dump(path):
    d = open(path, 'rb').read()
    magic, hsize = struct.unpack_from('<II', d, 0)
    assert magic == 0xffffffff, 'not a v2+ GS dump'
    h = struct.unpack_from('<9I', d, 8)
    keys = ('state_version','state_size','serial_offset','serial_size','crc','shot_w','shot_h','shot_off','shot_size')
    hdr = dict(zip(keys, h))
    base = 8
    hdr['serial'] = d[base+hdr['serial_offset']:base+hdr['serial_offset']+hdr['serial_size']].decode('latin1')
    shot = d[base+hdr['shot_off']:base+hdr['shot_off']+hdr['shot_size']]
    pos = 8 + hsize
    state = d[pos:pos+hdr['state_size']]; pos += hdr['state_size']
    regs = d[pos:pos+8192]; pos += 8192
    packets = []
    while pos < len(d):
        t = d[pos]; pos += 1
        if t == 0:
            path = d[pos]; size = struct.unpack_from('<I', d, pos+1)[0]; pos += 5
            packets.append(('xfer', path, d[pos:pos+size])); pos += size
        elif t == 1:
            packets.append(('vsync', d[pos])); pos += 1
        elif t == 2:
            packets.append(('readfifo', struct.unpack_from('<I', d, pos)[0])); pos += 4
        elif t == 3:
            packets.append(('regs', d[pos:pos+8192])); pos += 8192
        else:
            raise ValueError('unknown packet type %d at %d' % (t, pos-1))
    return hdr, shot, state, regs, packets


class GS:
    def __init__(self):
        self.r = defaultdict(int)
        self.r[0x1a] = 1  # PRMODECONT default AC=1
        self.vtx = []      # current primitive queue
        self.kicks = []    # (state key, rgba, f, xyz, uv/st)
        self.q = 1.0
        self.primseq = 0   # bumps on every PRIM write (vertex queue restart)
        self.uploads = []

    def prim_attr(self):
        prim = self.r[0x00]
        attr = prim if self.r[0x1a] & 1 else self.r[0x1b]
        return prim & 7, attr

    def state_key(self):
        ptype, attr = self.prim_attr()
        ctxt = (attr >> 9) & 1
        tex0 = self.r[0x06 + ctxt]; alpha = self.r[0x42 + ctxt]; test = self.r[0x47 + ctxt]
        return (ptype, attr & 0x7f8, ctxt, tex0 & 0x3fff, (tex0 >> 20) & 0x3f, (tex0 >> 34) & 1, (tex0 >> 35) & 3,
                alpha & 0xff, (alpha >> 32) & 0xff, (self.r[0x4c + ctxt]) & 0x1ff, test & 0xffff)

    def kick(self, x, y, z, f):
        rgba = self.r[0x01]
        self.kicks.append((self.state_key(), (rgba & 0xff, (rgba >> 8) & 0xff, (rgba >> 16) & 0xff, (rgba >> 24) & 0xff),
                           f, (x/16.0, y/16.0, z), self.r[0x3d] & 0xffffff, self.q, self.r[0x02], (self.r[0x00] if self.r[0x1a]&1 else self.r[0x1b])))

    def write(self, addr, v):
        self.r[addr] = v
        if addr == 0x00: self.primseq += 1
        if addr == 0x01:
            self.q = struct.unpack('<f', struct.pack('<I', (v >> 32) & 0xffffffff))[0]
        if addr in (0x04, 0x0c):   # XYZF2/3 raw
            self.kick(v & 0xffff, (v >> 16) & 0xffff, (v >> 32) & 0xffffff, (v >> 56) & 0xff)
        elif addr in (0x05, 0x0d):
            self.kick(v & 0xffff, (v >> 16) & 0xffff, (v >> 32) & 0xffffffff, (self.r[0x0a] >> 56) & 0xff)

    def gif(self, data):
        pos = 0
        n = len(data)
        while pos + 16 <= n:
            lo, hi = struct.unpack_from('<QQ', data, pos); pos += 16
            nloop = lo & 0x7fff; pre = (lo >> 46) & 1; prim = (lo >> 47) & 0x7ff
            flg = (lo >> 58) & 3; nreg = (lo >> 60) & 0xf or 16
            regs = [(hi >> (4*i)) & 0xf for i in range(nreg)]
            if pre and flg != 2:
                self.r[0x00] = prim; self.primseq += 1
            if flg == 0:
                for _ in range(nloop):
                    for reg in regs:
                        if pos + 16 > n: return
                        a, b = struct.unpack_from('<QQ', data, pos); pos += 16
                        self.packed(reg, a, b)
            elif flg == 1:
                total = nloop * nreg
                for i in range(total):
                    if pos + 8 > n: return
                    v = struct.unpack_from('<Q', data, pos)[0]; pos += 8
                    reg = regs[i % nreg]
                    if reg == 0xe or reg == 0xf: continue
                    addr = {0:0x00,1:0x01,2:0x02,3:0x03,4:0x04,5:0x05,6:0x06,7:0x07,8:0x08,9:0x09,0xa:0x0a,0xc:0x0c,0xd:0x0d}.get(reg)
                    if addr is not None: self.write(addr, v)
                if total & 1: pos += 8
            else:
                bb = self.r[0x50]; tr = self.r[0x52]; tp = self.r[0x51]
                self.uploads.append({'dbp': (bb >> 32) & 0x3fff, 'dbw': (bb >> 48) & 0x3f, 'dpsm': (bb >> 56) & 0x3f,
                                     'w': tr & 0xfff, 'h': (tr >> 32) & 0xfff, 'x': (tp >> 32) & 0x7ff, 'y': (tp >> 48) & 0x7ff,
                                     'data': data[pos:pos + nloop * 16]})
                pos += nloop * 16   # IMAGE

    def packed(self, reg, a, b):
        if reg == 0x0:
            self.write(0x00, a & 0x7ff)  # bumps primseq
        elif reg == 0x1:
            r, g = a & 0xff, (a >> 32) & 0xff; bb, al = b & 0xff, (b >> 32) & 0xff
            self.r[0x01] = r | (g << 8) | (bb << 16) | (al << 24)
        elif reg == 0x2:
            self.r[0x02] = a
            self.q = struct.unpack('<f', struct.pack('<I', b & 0xffffffff))[0]
        elif reg == 0x3:
            self.r[0x03] = (a & 0x3fff) | (((a >> 32) & 0x3fff) << 16)
        elif reg == 0x4:
            x, y = a & 0xffff, (a >> 32) & 0xffff; z = (b >> 4) & 0xffffff; f = (b >> 36) & 0xff
            self.kick(x, y, z, f)
        elif reg == 0x5:
            x, y = a & 0xffff, (a >> 32) & 0xffff; z = b & 0xffffffff
            self.kick(x, y, z, (self.r[0x0a] >> 56) & 0xff)
        elif reg == 0xa:
            self.r[0x0a] = ((b >> 36) & 0xff) << 56
        elif reg == 0xe:
            self.write(b & 0xff, a)
        elif reg in (0x6, 0x7, 0x8, 0x9):
            self.r[{0x6:0x06,0x7:0x07,0x8:0x08,0x9:0x09}[reg]] = a


def replay(path, frames=None):
    hdr, shot, state, regs, packets = read_dump(path)
    gs = GS()
    seen_vsync = 0
    for p in packets:
        if p[0] == 'xfer':
            gs.gif(p[2])
        elif p[0] == 'vsync':
            seen_vsync += 1
            if frames and seen_vsync >= frames: break
    return hdr, shot, gs, packets


if __name__ == '__main__':
    hdr, shot, gs, packets = replay(sys.argv[1])
    print(json.dumps({k: hdr[k] for k in ('state_version','serial','crc','shot_w','shot_h')}))
    print('packets', Counter(p[0] for p in packets), 'kicks', len(gs.kicks))


BLOCK32 = [[0,1,4,5,16,17,20,21],[2,3,6,7,18,19,22,23],[8,9,12,13,24,25,28,29],[10,11,14,15,26,27,30,31]]


COLUMN32 = [[0,1,4,5,8,9,12,13],[2,3,6,7,10,11,14,15],[16,17,20,21,24,25,28,29],[18,19,22,23,26,27,30,31],
            [32,33,36,37,40,41,44,45],[34,35,38,39,42,43,46,47],[48,49,52,53,56,57,60,61],[50,51,54,55,58,59,62,63]]

COLUMN16 = [[0,2,8,10,16,18,24,26,1,3,9,11,17,19,25,27],[4,6,12,14,20,22,28,30,5,7,13,15,21,23,29,31],
            [32,34,40,42,48,50,56,58,33,35,41,43,49,51,57,59],[36,38,44,46,52,54,60,62,37,39,45,47,53,55,61,63],
            [64,66,72,74,80,82,88,90,65,67,73,75,81,83,89,91],[68,70,76,78,84,86,92,94,69,71,77,79,85,87,93,95],
            [96,98,104,106,112,114,120,122,97,99,105,107,113,115,121,123],[100,102,108,110,116,118,124,126,101,103,109,111,117,119,125,127]]


def vram_of(state):
    return state[373:373 + 4 * 1024 * 1024]


def read_ct32(vram, bp, bw, w, h):
    out = bytearray(w * h * 4)
    for y in range(h):
        for x in range(w):
            page = (x // 64) + (y // 32) * bw
            block = BLOCK32[(y // 8) % 4][(x // 8) % 8]
            word = COLUMN32[y % 8][x % 8]
            a = ((bp + page * 32 + block) * 64 + word) * 4
            out[(y * w + x) * 4:(y * w + x) * 4 + 4] = vram[a:a + 4]
    return bytes(out)


BLOCK16 = [[0,2,8,10],[1,3,9,11],[4,6,12,14],[5,7,13,15],[16,18,24,26],[17,19,25,27],[20,22,28,30],[21,23,29,31]]


def read_ct16(vram, bp, bw, w, h):
    out = bytearray(w * h * 4)
    for y in range(h):
        for x in range(w):
            page = (x // 64) + (y // 64) * bw
            block = BLOCK16[(y // 8) % 8][(x // 16) % 4]
            hw = COLUMN16[y % 8][x % 16]
            a = ((bp + page * 32 + block) * 64) * 4 + hw * 2
            v = vram[a] | (vram[a + 1] << 8)
            o = (y * w + x) * 4
            out[o] = (v & 31) << 3; out[o+1] = ((v >> 5) & 31) << 3; out[o+2] = ((v >> 10) & 31) << 3; out[o+3] = 255 if v & 0x8000 else 0
    return bytes(out)
