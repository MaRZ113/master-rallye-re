"""Print the held-arrow repeat diagnostic written by the course layer (scroll-diag.bin in the game folder)."""
import struct, sys
TAGS = {1: "native press", 2: "repeat fires", 3: "UI/Active", 4: "XYButton/Moving", 5: "after jump", 6: "hold ended"}
raw = open(sys.argv[1], "rb").read(); t0 = None
for k in range(len(raw) // 36):
    tag, tick, extra, mode, pos, count, rdir, rnext, rcount = struct.unpack_from("<9i", raw, 36 * k)
    t0 = tick if t0 is None else t0
    print("%7d ms  %-15s extra %4d  mode %d  pos %3d / %3d  dir %2d  count %3d" % (tick - t0, TAGS.get(tag, tag), extra, mode, pos, count, rdir, rcount))
