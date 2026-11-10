namespace MenuBuilder.Core;

/// <summary>.dxt: 0xFEED, 1, id, W, H, then W*H BGRA, rows stored bottom-up (docs/formats/dxt.md).</summary>
public sealed class DxtTexture
{
    public int Width { get; }
    public int Height { get; }
    /// <summary>BGRA, row 0 = stored row 0 (texture v = 0).</summary>
    public byte[] Bgra { get; }

    public DxtTexture(int w, int h, byte[] bgra) { Width = w; Height = h; Bgra = bgra; }

    public static DxtTexture Parse(byte[] b)
    {
        if (b.Length < 20 || BitConverter.ToUInt32(b, 0) != 0xFEED) throw new InvalidDataException("not a DXT texture");
        int w = BitConverter.ToInt32(b, 12), h = BitConverter.ToInt32(b, 16);
        if (w <= 0 || h <= 0 || 20 + (long)w * h * 4 != b.Length) throw new InvalidDataException("DXT size mismatch");
        return new DxtTexture(w, h, b.AsSpan(20).ToArray());
    }

    /// <summary>Bilinear-free point sample with clamping; u,v in texture space (v = 0 is stored row 0).</summary>
    public uint Sample(float u, float v)
    {
        int x = (int)(u * Width), y = (int)(v * Height);
        x = x < 0 ? 0 : x >= Width ? Width - 1 : x;
        y = y < 0 ? 0 : y >= Height ? Height - 1 : y;
        return BitConverter.ToUInt32(Bgra, (y * Width + x) * 4);
    }
}

public readonly record struct DxbTriangle(float U0, float V0, float U1, float V1, float U2, float V2,
    int X0, int Y0, int X1, int Y1, int X2, int Y2, string Texture);

public sealed class DxbImage
{
    public List<DxbTriangle> Triangles { get; } = new();
    public int MinX, MinY, MaxX, MaxY;
    /// <summary>Native image size (0x525440 reads +0x14 table): bounding box of the image geometry.</summary>
    public int Width => MaxX - MinX;
    public int Height => MaxY - MinY;
}

/// <summary>
/// .dxb tag-125 2D image bank: u32 0xF001, u32 125, u32 N, N pairs {code, image},
/// u32 M images, each u32 T triangles {6 f32 uv, 6 i32 xy, u32 len, name}. All 113 retail files
/// parse to the exact end. Local y grows downward: screen_y(up) = egg_y - local_y.
/// </summary>
public sealed class DxbBank
{
    public List<(int code, int image)> Map { get; } = new();
    public List<DxbImage> Images { get; } = new();

    public static DxbBank Parse(byte[] b)
    {
        int o = 0;
        int I() { int v = BitConverter.ToInt32(b, o); o += 4; return v; }
        float F() { float v = BitConverter.ToSingle(b, o); o += 4; return v; }
        if (I() != 0xF001 || I() != 125) throw new InvalidDataException("not a DXB tag-125 bank");
        var bank = new DxbBank();
        int n = I();
        for (int i = 0; i < n; i++) bank.Map.Add((I(), I()));
        int m = I();
        for (int i = 0; i < m; i++)
        {
            var img = new DxbImage { MinX = int.MaxValue, MinY = int.MaxValue, MaxX = int.MinValue, MaxY = int.MinValue };
            int t = I();
            for (int k = 0; k < t; k++)
            {
                float u0 = F(), v0 = F(), u1 = F(), v1 = F(), u2 = F(), v2 = F();
                int x0 = I(), y0 = I(), x1 = I(), y1 = I(), x2 = I(), y2 = I();
                int len = I();
                string name = System.Text.Encoding.Latin1.GetString(b, o, len); o += len;
                img.Triangles.Add(new DxbTriangle(u0, v0, u1, v1, u2, v2, x0, y0, x1, y1, x2, y2, name));
                foreach (var (x, y) in new[] { (x0, y0), (x1, y1), (x2, y2) })
                {
                    img.MinX = Math.Min(img.MinX, x); img.MaxX = Math.Max(img.MaxX, x);
                    img.MinY = Math.Min(img.MinY, y); img.MaxY = Math.Max(img.MaxY, y);
                }
            }
            if (t == 0) img.MinX = img.MinY = img.MaxX = img.MaxY = 0;
            bank.Images.Add(img);
        }
        if (o != b.Length) throw new InvalidDataException($"DXB trailing bytes: {b.Length - o}");
        return bank;
    }

    /// <summary>Image for a bank index; the {code,image} map is the indirection used by fonts and sprite banks.</summary>
    public DxbImage? ImageFor(int index)
    {
        foreach (var (code, image) in Map) if (code == index && image >= 0 && image < Images.Count) return Images[image];
        return index >= 0 && index < Images.Count ? Images[index] : null;
    }

    public DxbImage? Glyph(char c)
    {
        int code = c;
        foreach (var (k, image) in Map) if (k == code && image >= 0 && image < Images.Count) return Images[image];
        return null;
    }
}

/// <summary>Loads and caches frontend resources from a <see cref="GameData"/> exactly by the names the XML uses.</summary>
public sealed class AssetCache
{
    readonly GameData _data;
    readonly Dictionary<string, DxbBank?> _banks = new(StringComparer.OrdinalIgnoreCase);
    readonly Dictionary<string, DxtTexture?> _textures = new(StringComparer.OrdinalIgnoreCase);
    public List<string> Missing { get; } = new();

    public AssetCache(GameData data) { _data = data; }
    public GameData Data => _data;

    static string ModelPath(string model) => "DataGx/" + GameData.Normalize(model) + ".dxb";

    /// <summary>en2d Model Name ("frontend\buttons\longbutton") or font name ("fonts/Arial/Arial_16").</summary>
    public DxbBank? Bank(string? model)
    {
        if (string.IsNullOrEmpty(model) || model == "Null" || model == "dummy") return null;
        if (_banks.TryGetValue(model, out var hit)) return hit;
        DxbBank? bank = null;
        var raw = _data.Read(ModelPath(model));
        if (raw != null) { try { bank = DxbBank.Parse(raw); } catch { } }
        else Missing.Add(ModelPath(model));
        return _banks[model] = bank;
    }

    public DxtTexture? Texture(string model, string texture)
    {
        var dir = GameData.Normalize(model);
        int slash = dir.LastIndexOf('/');
        var path = "DataGx/" + (slash >= 0 ? dir[..slash] + "/" : "") + texture + ".dxt";
        if (_textures.TryGetValue(path, out var hit)) return hit;
        DxtTexture? tex = null;
        var raw = _data.Read(path);
        if (raw != null) { try { tex = DxtTexture.Parse(raw); } catch { } }
        else Missing.Add(path);
        return _textures[path] = tex;
    }

    /// <summary>All model names available under DataGx/Frontend (for the sprite picker).</summary>
    public IEnumerable<string> FrontendModels() =>
        _data.ArchiveFiles("DataGx/Frontend/").Where(p => p.EndsWith(".dxb", StringComparison.OrdinalIgnoreCase))
            .Select(p => p["DataGx/".Length..^4].Replace('/', '\\').ToLowerInvariant()).OrderBy(x => x);
}
