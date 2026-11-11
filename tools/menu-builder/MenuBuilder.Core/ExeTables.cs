using System.Text;

namespace MenuBuilder.Core;

/// <summary>
/// Static tables read from the user's own retail MRallye.exe (SHA-256 bf8aef32...). Nothing is
/// copied into the project: localized strings, font IDs and the frontend screen table are read
/// at run time from the installation.
/// </summary>
public sealed class ExeTables
{
    public const string RetailSha256 = "bf8aef32407eb6552c05045b8abef149f32983cedd9503b865069b444c5f96b4";
    // gaLocal text tables, selected by language index (0x485C20): rows {group, index, char*}, end = -2.
    static readonly uint[] TextTables = { 0x6C9A60, 0x6BB888, 0x6B8000, 0x6C2998, 0x6BF110, 0x6C6220 };
    // Font ID table (0x485CA0): rows {id, char*}, end = -2.
    const uint FontTable = 0x6CD2F8;
    // Screen name constructors (0x448C60): PUSH name; MOV ECX, 0x6F5BD8 + 4*id; CALL.
    const uint ScreenInit = 0x448C60, ScreenTable = 0x6F5BD8;
    public const int RetailScreenCount = 0x36;

    readonly byte[] _image;
    readonly List<(uint va, uint size, uint raw, uint rawSize)> _sections = new();
    public bool IsRetail { get; }
    public string Sha256 { get; }
    public IReadOnlyList<string> Screens { get; }
    public IReadOnlyDictionary<int, string> Fonts { get; }
    readonly Dictionary<(int, int), string>[] _texts;

    public ExeTables(string exePath)
    {
        _image = File.ReadAllBytes(exePath);
        Sha256 = GameData.Sha256(_image);
        IsRetail = Sha256 == RetailSha256;
        int pe = BitConverter.ToInt32(_image, 0x3C);
        int count = BitConverter.ToUInt16(_image, pe + 6), opt = BitConverter.ToUInt16(_image, pe + 20);
        uint baseVa = BitConverter.ToUInt32(_image, pe + 52);
        for (int i = 0; i < count; i++)
        {
            int o = pe + 24 + opt + 40 * i;
            _sections.Add((baseVa + BitConverter.ToUInt32(_image, o + 12), BitConverter.ToUInt32(_image, o + 8),
                BitConverter.ToUInt32(_image, o + 20), BitConverter.ToUInt32(_image, o + 16)));
        }
        if (!IsRetail)
        {
            // Modded EXEs keep the same data layout in practice, but only the retail image is certified.
            Screens = Array.Empty<string>(); Fonts = new Dictionary<int, string>();
            _texts = Array.Empty<Dictionary<(int, int), string>>();
            try { Screens = ReadScreens(); Fonts = ReadFonts(); _texts = TextTables.Select(ReadTexts).ToArray(); } catch { }
            return;
        }
        Screens = ReadScreens();
        Fonts = ReadFonts();
        _texts = TextTables.Select(ReadTexts).ToArray();
    }

    int Offset(uint va)
    {
        foreach (var s in _sections)
            if (va >= s.va && va < s.va + Math.Max(s.size, s.rawSize) && va - s.va < s.rawSize) return (int)(s.raw + va - s.va);
        throw new InvalidDataException($"VA 0x{va:X} not in file image");
    }
    uint U32(uint va) => BitConverter.ToUInt32(_image, Offset(va));
    string CStr(uint va)
    {
        int o = Offset(va), e = Array.IndexOf(_image, (byte)0, o);
        return Encoding.Latin1.GetString(_image, o, e - o);
    }

    List<string> ReadScreens()
    {
        var names = new string[RetailScreenCount];
        int o = Offset(ScreenInit);
        for (int i = 0; i < 0x360; i++)
        {
            if (_image[o + i] == 0x68 && _image[o + i + 5] == 0xB9)
            {
                uint s = BitConverter.ToUInt32(_image, o + i + 1), slot = BitConverter.ToUInt32(_image, o + i + 6);
                int id = (int)((slot - ScreenTable) / 4);
                if (id >= 0 && id < names.Length) names[id] = CStr(s);
                i += 9;
            }
        }
        return names.Select((n, i) => n ?? $"Screen{i}").ToList();
    }

    Dictionary<int, string> ReadFonts()
    {
        var r = new Dictionary<int, string>();
        for (uint a = FontTable; ; a += 8)
        {
            int id = (int)U32(a);
            // The retail table has no -2 terminator: the last row points at the string stored right after it.
            if (id <= 0 || id > 256 || r.Count > 64) break;
            try { r[id] = CStr(U32(a + 4)); } catch (InvalidDataException) { break; }
        }
        return r;
    }

    Dictionary<(int, int), string> ReadTexts(uint table)
    {
        var r = new Dictionary<(int, int), string>();
        for (uint a = table; ; a += 12)
        {
            int group = (int)U32(a);
            if (group == -2 || r.Count > 20000) break;
            int index = (int)U32(a + 4);
            uint p = U32(a + 8);
            try { r[(group, index)] = CStr(p); } catch { }
        }
        return r;
    }

    public int LanguageCount => _texts.Length;

    /// <summary>gaLocal lookup (vtable +0xC). Text ID Index 0 falls back to index 0 like 0x524EB0.</summary>
    public string? Text(int group, int index, int language = 0)
    {
        if (_texts.Length == 0) return null;
        var t = _texts[Math.Clamp(language, 0, _texts.Length - 1)];
        return t.TryGetValue((group, index), out var s) ? s : null;
    }

    public IEnumerable<(int group, int index, string text)> AllTexts(int language = 0) =>
        _texts.Length == 0 ? Enumerable.Empty<(int, int, string)>() :
        _texts[Math.Clamp(language, 0, _texts.Length - 1)].Select(kv => (kv.Key.Item1, kv.Key.Item2, kv.Value));

    public int ScreenId(string name)
    {
        for (int i = 0; i < Screens.Count; i++)
            if (string.Equals(Screens[i], name, StringComparison.OrdinalIgnoreCase)) return i;
        return -1;
    }
}
