using System.Text.RegularExpressions;

namespace MenuBuilder.Core;

/// <summary>
/// Layout/project names become a folder under &lt;game&gt;\MenuBuilder\Layouts and a value in MenuBuilder.ini, so they
/// are validated instead of being silently rewritten: two different names can never map to one folder, an empty or
/// dot name can never address the Layouts root, and nothing outside the Layouts folder can be named.
/// </summary>
public static class LayoutName
{
    public const int MaxLength = 48;
    static readonly Regex Allowed = new("^[A-Za-z0-9][A-Za-z0-9_-]*$", RegexOptions.CultureInvariant);
    static readonly HashSet<string> Reserved = new(StringComparer.OrdinalIgnoreCase)
    {
        "CON", "PRN", "AUX", "NUL", "CLOCK$", "CONIN$", "CONOUT$",
        "COM1", "COM2", "COM3", "COM4", "COM5", "COM6", "COM7", "COM8", "COM9",
        "LPT1", "LPT2", "LPT3", "LPT4", "LPT5", "LPT6", "LPT7", "LPT8", "LPT9",
    };

    /// <summary>Why <paramref name="name"/> cannot be a layout name, or null when it can.</summary>
    public static string? Problem(string? name)
    {
        if (string.IsNullOrWhiteSpace(name)) return "the name is empty";
        if (name is "." or "..") return "'.' and '..' are not names";
        if (name.Length > MaxLength) return $"the name is longer than {MaxLength} characters";
        if (!Allowed.IsMatch(name)) return "use letters A-Z, digits, '-' and '_' only (no spaces, dots, slashes or other characters); the first character must be a letter or digit";
        if (Reserved.Contains(name)) return $"'{name}' is a reserved Windows device name";
        return null;
    }

    public static bool IsValid(string? name) => Problem(name) == null;

    public static string Validate(string? name) =>
        Problem(name) is { } p ? throw new InvalidLayoutNameException(name ?? "", p) : name!;

    /// <summary>A valid name close to <paramref name="name"/> (for the "rename the project" suggestion).</summary>
    public static string Suggest(string? name)
    {
        var chars = (name ?? "").Trim().Select(c => c < 128 && (char.IsLetterOrDigit(c) || c is '-' or '_') ? c : '_').ToArray();
        var s = new string(chars).Trim('_', '-');
        if (s.Length > MaxLength) s = s[..MaxLength];
        if (s.Length == 0 || !char.IsLetterOrDigit(s[0])) s = "Layout" + s;
        if (Reserved.Contains(s)) s += "_";
        return s;
    }
}

public sealed class InvalidLayoutNameException : ArgumentException
{
    public string Name { get; }
    public InvalidLayoutNameException(string name, string problem)
        : base($"invalid layout name '{name}': {problem} (suggestion: {LayoutName.Suggest(name)})") { Name = name; }
}

/// <summary>Raised by a file operation that would leave its sandbox or cross a link.</summary>
public sealed class UnsafePathException : IOException
{
    public UnsafePathException(string message) : base(message) { }
}

/// <summary>
/// File system operations confined to one sandbox folder (the Layouts root). Paths are compared in full form,
/// every folder below the sandbox is checked for reparse points (junctions, symbolic links, mount points) and
/// recursive deletes never descend into a link: a link found inside a tree is removed as a link, its target is
/// never touched.
/// </summary>
public static class SafeFs
{
    static readonly StringComparison Cmp = StringComparison.OrdinalIgnoreCase;

    public static string Full(string path) => Path.TrimEndingDirectorySeparator(Path.GetFullPath(path));

    public static bool IsReparsePoint(string path)
    {
        try { return (File.GetAttributes(path) & FileAttributes.ReparsePoint) != 0; }
        catch (FileNotFoundException) { return false; }
        catch (DirectoryNotFoundException) { return false; }
    }

    /// <summary>True when <paramref name="path"/> is strictly inside <paramref name="root"/> (never the root itself).</summary>
    public static bool IsStrictlyInside(string root, string path)
    {
        var r = Full(root) + Path.DirectorySeparatorChar;
        var p = Full(path);
        return p.Length > r.Length && p.StartsWith(r, Cmp);
    }

    /// <summary>
    /// Throws unless <paramref name="path"/> is strictly inside <paramref name="root"/> and no existing folder from
    /// <paramref name="root"/> (inclusive) down to <paramref name="path"/> (inclusive) is a reparse point.
    /// </summary>
    public static void RequireInside(string root, string path)
    {
        var r = Full(root);
        var p = Full(path);
        if (!IsStrictlyInside(r, p)) throw new UnsafePathException($"refusing to touch '{p}': it is not inside '{r}'");
        if (IsReparsePoint(r)) throw new UnsafePathException($"refusing to work in '{r}': the folder is a junction or symbolic link");
        var cur = r;
        foreach (var part in p[(r.Length + 1)..].Split(Path.DirectorySeparatorChar))
        {
            cur = Path.Combine(cur, part);
            if ((Directory.Exists(cur) || File.Exists(cur)) && IsReparsePoint(cur))
                throw new UnsafePathException($"refusing to touch '{cur}': it is a junction or symbolic link");
        }
    }

    /// <summary>Creates <paramref name="dir"/> (and parents up to the existing ancestor) with no link on the way.</summary>
    public static void CreateDirectoryChecked(string parentRoot, string dir)
    {
        var r = Full(parentRoot);
        var p = Full(dir);
        if (!p.Equals(r, Cmp)) RequireInside(r, p);
        else if (IsReparsePoint(r)) throw new UnsafePathException($"refusing to work in '{r}': the folder is a junction or symbolic link");
        Directory.CreateDirectory(p);
        if (!p.Equals(r, Cmp)) RequireInside(r, p);
    }

    /// <summary>
    /// Deletes a folder tree inside <paramref name="root"/>. Never deletes <paramref name="root"/>, never follows a
    /// link: a junction or symbolic link inside the tree is unlinked (its target stays). Read-only files are deleted.
    /// </summary>
    public static void DeleteTree(string root, string dir)
    {
        RequireInside(root, dir);
        if (!Directory.Exists(dir)) return;
        DeleteChildren(Full(dir));
        Directory.Delete(dir, false);
    }

    static void DeleteChildren(string dir)
    {
        foreach (var entry in new DirectoryInfo(dir).EnumerateFileSystemInfos())
        {
            if ((entry.Attributes & FileAttributes.ReparsePoint) != 0)
            {
                // Remove the link itself; Directory.Delete(non-recursive) on a junction removes only the link.
                if (entry is DirectoryInfo d) d.Delete(false); else { entry.Attributes = FileAttributes.Normal; entry.Delete(); }
                continue;
            }
            if (entry is DirectoryInfo sub)
            {
                DeleteChildren(sub.FullName);
                sub.Attributes = FileAttributes.Directory;
                sub.Delete(false);
            }
            else
            {
                if ((entry.Attributes & FileAttributes.ReadOnly) != 0) entry.Attributes = FileAttributes.Normal;
                entry.Delete();
            }
        }
    }

    /// <summary>Writes a file next to its destination and swaps it in with a rename (no torn file on failure).</summary>
    public static void WriteAtomic(string path, byte[] bytes)
    {
        var tmp = path + ".mb-tmp";
        File.WriteAllBytes(tmp, bytes);
        try { File.Move(tmp, path, overwrite: true); }
        catch { try { File.Delete(tmp); } catch { } throw; }
    }
}
