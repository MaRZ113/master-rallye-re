using System.IO.Compression;
using System.Security.Cryptography;

namespace MenuBuilder.Core;

/// <summary>
/// Read-only view of a Master Rallye installation. Resolution order follows the game: the Vehicle Manager
/// roster overlay (MRMods/Vehicles/active/resources, served by the dinput8 loader through the CreateFileA import)
/// wins, then a loose file under the game root (native VFS 0x64D530), then the Data.sma member.
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
            _sma = new ZipArchive(SmaStream.Open(sma), ZipArchiveMode.Read);
            foreach (var e in _sma.Entries)
                if (e.Length > 0 || !e.FullName.EndsWith('/')) _entries[Normalize(e.FullName)] = e;
        }
        if (!File.Exists(Path.Combine(Root, "MRallye.exe")) && _sma == null)
            throw new DirectoryNotFoundException($"{Root} is not a Master Rallye installation (no MRallye.exe / Data.sma)");
    }

    public static string Normalize(string rel) => rel.Replace('\\', '/').TrimStart('/');

    /// <summary>Folder of the active Vehicle Manager roster resources (game-relative files that replace or add data).</summary>
    public const string OverlayFolder = "MRMods/Vehicles/active/resources";

    public string? OverlayPath(string rel)
    {
        var p = Path.Combine(Root, OverlayFolder.Replace('/', Path.DirectorySeparatorChar), Normalize(rel).Replace('/', Path.DirectorySeparatorChar));
        return File.Exists(p) ? p : null;
    }

    public string? LoosePath(string rel)
    {
        var p = Path.Combine(Root, Normalize(rel).Replace('/', Path.DirectorySeparatorChar));
        return File.Exists(p) ? p : null;
    }

    public bool InArchive(string rel) => _entries.ContainsKey(Normalize(rel));
    public bool Exists(string rel) => OverlayPath(rel) != null || LoosePath(rel) != null || InArchive(rel);

    /// <summary>Effective file as the game would load it (roster overlay, then loose, then Data.sma).</summary>
    public byte[]? Read(string rel)
    {
        rel = Normalize(rel);
        if (_cache.TryGetValue(rel, out var hit)) return hit;
        var loose = OverlayPath(rel) ?? LoosePath(rel);
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

    public string Source(string rel) => OverlayPath(rel) != null ? "overlay" : LoosePath(rel) != null ? "loose" : InArchive(rel) ? "archive" : "missing";

    /// <summary>Drops cached file contents (after the roster or loose files changed).</summary>
    public void ClearCache() => _cache.Clear();

    public IEnumerable<string> ArchiveFiles(string prefix) =>
        _entries.Keys.Where(k => k.StartsWith(Normalize(prefix), StringComparison.OrdinalIgnoreCase));

    public void Dispose() => _sma?.Dispose();

    public static string Sha256(byte[] data) => Convert.ToHexString(SHA256.HashData(data)).ToLowerInvariant();
}

/// <summary>
/// Read-only view of Data.sma for System.IO.Compression. The retail archive is a ZIP whose end-of-central-directory
/// signature is "SM" instead of "PK" (the game's VFS checks its own signature); the file on disk is
/// never modified, the two signature bytes are presented as "PK" while reading. Re-packed archives with the standard
/// signature are read unchanged.
/// </summary>
public sealed class SmaStream : Stream
{
    readonly FileStream _f;
    readonly long _patchAt;   // offset of the 'S' of "SM", or -1

    SmaStream(FileStream f, long patchAt) { _f = f; _patchAt = patchAt; }

    public static Stream Open(string path)
    {
        var f = new FileStream(path, FileMode.Open, FileAccess.Read, FileShare.Read);
        // The EOCD record is in the last 22 + 65535 bytes (maximum comment length).
        long start = Math.Max(0, f.Length - (22 + 65535));
        var tail = new byte[f.Length - start];
        f.Position = start;
        f.ReadExactly(tail);
        f.Position = 0;
        for (int i = tail.Length - 22; i >= 0; i--)
        {
            if (tail[i + 2] != 5 || tail[i + 3] != 6) continue;
            if (tail[i] == (byte)'P' && tail[i + 1] == (byte)'K') return f;                 // standard ZIP
            if (tail[i] == (byte)'S' && tail[i + 1] == (byte)'M') return new SmaStream(f, start + i);
        }
        return f;   // let ZipArchive report the problem
    }

    public override int Read(byte[] buffer, int offset, int count)
    {
        long pos = _f.Position;
        int n = _f.Read(buffer, offset, count);
        if (_patchAt >= 0)
            for (int k = 0; k < 2; k++)
            {
                long at = _patchAt + k - pos;
                if (at >= 0 && at < n) buffer[offset + at] = k == 0 ? (byte)'P' : (byte)'K';
            }
        return n;
    }

    public override bool CanRead => true;
    public override bool CanSeek => true;
    public override bool CanWrite => false;
    public override long Length => _f.Length;
    public override long Position { get => _f.Position; set => _f.Position = value; }
    public override long Seek(long offset, SeekOrigin origin) => _f.Seek(offset, origin);
    public override void Flush() { }
    public override void SetLength(long value) => throw new NotSupportedException();
    public override void Write(byte[] buffer, int offset, int count) => throw new NotSupportedException();
    protected override void Dispose(bool disposing) { if (disposing) _f.Dispose(); base.Dispose(disposing); }
}
