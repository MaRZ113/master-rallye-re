using System.IO.Compression;

namespace MenuBuilder.Core;

/// <summary>Minimal RGBA PNG writer/reader (no external dependencies).</summary>
public static class Png
{
    static readonly uint[] Crc = Enumerable.Range(0, 256).Select(n =>
    {
        uint c = (uint)n;
        for (int k = 0; k < 8; k++) c = (c & 1) != 0 ? 0xEDB88320u ^ (c >> 1) : c >> 1;
        return c;
    }).ToArray();

    static uint Crc32(byte[] data, int start, int len)
    {
        uint c = 0xFFFFFFFF;
        for (int i = start; i < start + len; i++) c = Crc[(c ^ data[i]) & 0xFF] ^ (c >> 8);
        return c ^ 0xFFFFFFFF;
    }

    static void Chunk(Stream s, string type, byte[] data)
    {
        var buf = new byte[8 + data.Length + 4];
        WriteBE(buf, 0, (uint)data.Length);
        for (int i = 0; i < 4; i++) buf[4 + i] = (byte)type[i];
        Buffer.BlockCopy(data, 0, buf, 8, data.Length);
        WriteBE(buf, 8 + data.Length, Crc32(buf, 4, 4 + data.Length));
        s.Write(buf);
    }

    static void WriteBE(byte[] b, int o, uint v) { b[o] = (byte)(v >> 24); b[o + 1] = (byte)(v >> 16); b[o + 2] = (byte)(v >> 8); b[o + 3] = (byte)v; }

    /// <summary>Pixels are 0xAARRGGBB, row 0 at the top.</summary>
    public static byte[] Encode(uint[] px, int w, int h)
    {
        using var ms = new MemoryStream();
        ms.Write(new byte[] { 0x89, 0x50, 0x4E, 0x47, 0x0D, 0x0A, 0x1A, 0x0A });
        var ihdr = new byte[13];
        WriteBE(ihdr, 0, (uint)w); WriteBE(ihdr, 4, (uint)h);
        ihdr[8] = 8; ihdr[9] = 6;
        Chunk(ms, "IHDR", ihdr);
        var raw = new byte[h * (1 + w * 4)];
        for (int y = 0; y < h; y++)
        {
            int o = y * (1 + w * 4);
            for (int x = 0; x < w; x++)
            {
                uint p = px[y * w + x];
                raw[o + 1 + x * 4] = (byte)(p >> 16); raw[o + 2 + x * 4] = (byte)(p >> 8);
                raw[o + 3 + x * 4] = (byte)p; raw[o + 4 + x * 4] = (byte)(p >> 24);
            }
        }
        using (var z = new MemoryStream())
        {
            using (var zs = new ZLibStream(z, CompressionLevel.Fastest, true)) zs.Write(raw);
            Chunk(ms, "IDAT", z.ToArray());
        }
        Chunk(ms, "IEND", Array.Empty<byte>());
        return ms.ToArray();
    }

    public static void Save(string path, uint[] px, int w, int h) => File.WriteAllBytes(path, Encode(px, w, h));
}
