using System.IO.Compression;
using System.Security.Cryptography;

namespace MenuBuilder.Core;

/// <summary>
/// Read-only view of a Master Rallye installation. Resolution order follows the native VFS
/// (0x64D530): a loose file under the game root wins, otherwise the Data.sma member is used.
/// Nothing in the installation is ever written by this class.
/// </summary>
public sealed class GameData : IDisposable
{
    public string Root { get; }
    readonly ZipArchive? _sma;
    readonly Dictionary<string, ZipArchiveEntry> _entries = new(StringComparer.OrdinalIgnoreCase);
    readonly Dictionary<string, byte[]> _cache = new(StringComparer.OrdinalIgnoreCase);

    public GameData(string root)
    {
        Root = Path.GetFullPath(root);
        var sma = Path.Combine(Root, "Data.sma");
        if (File.Exists(sma))
        {
            _sma = new ZipArchive(File.OpenRead(sma), ZipArchiveMode.Read);
            foreach (var e in _sma.Entries)
                if (e.Length > 0 || !e.FullName.EndsWith('/')) _entries[Normalize(e.FullName)] = e;
        }
        if (!File.Exists(Path.Combine(Root, "MRallye.exe")) && _sma == null)
            throw new DirectoryNotFoundException($"{Root} is not a Master Rallye installation (no MRallye.exe / Data.sma)");
    }

    public static string Normalize(string rel) => rel.Replace('\\', '/').TrimStart('/');

    public string? LoosePath(string rel)
    {
        var p = Path.Combine(Root, Normalize(rel).Replace('/', Path.DirectorySeparatorChar));
        return File.Exists(p) ? p : null;
    }

    public bool InArchive(string rel) => _entries.ContainsKey(Normalize(rel));
    public bool Exists(string rel) => LoosePath(rel) != null || InArchive(rel);

    /// <summary>Effective file as the game would load it (loose first).</summary>
    public byte[]? Read(string rel)
    {
        rel = Normalize(rel);
        if (_cache.TryGetValue(rel, out var hit)) return hit;
        var loose = LoosePath(rel);
        var data = loose != null ? File.ReadAllBytes(loose) : ReadArchive(rel);
        if (data != null) _cache[rel] = data;
        return data;
    }

    /// <summary>Retail baseline from Data.sma only, ignoring loose overrides.</summary>
    public byte[]? ReadArchive(string rel)
    {
        if (!_entries.TryGetValue(Normalize(rel), out var e)) return null;
        lock (_entries)
        {
            using var s = e.Open();
            using var m = new MemoryStream();
            s.CopyTo(m);
            return m.ToArray();
        }
    }

    public string Source(string rel) => LoosePath(rel) != null ? "loose" : InArchive(rel) ? "archive" : "missing";

    public IEnumerable<string> ArchiveFiles(string prefix) =>
        _entries.Keys.Where(k => k.StartsWith(Normalize(prefix), StringComparison.OrdinalIgnoreCase));

    public void Dispose() => _sma?.Dispose();

    public static string Sha256(byte[] data) => Convert.ToHexString(SHA256.HashData(data)).ToLowerInvariant();
}
