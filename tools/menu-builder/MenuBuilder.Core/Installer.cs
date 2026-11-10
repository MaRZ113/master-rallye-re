using System.Globalization;
using System.Text;
using System.Text.Json;

namespace MenuBuilder.Core;

/// <summary>
/// Writes a compiled layout into &lt;game&gt;/MenuBuilder/Layouts/&lt;name&gt; and the runtime table read by the
/// native module in dinput8.dll. Only files under &lt;game&gt;/MenuBuilder are ever created or removed; game
/// data, saves (DataGame/PlayerState.xml, options.xml) and other mods' loose pages are never touched.
/// </summary>
public static class Installer
{
    public const string Folder = "MenuBuilder";
    public const int RuntimeFormat = 1;

    public static string LayoutDir(string gameRoot, string name) => Path.Combine(gameRoot, Folder, "Layouts", SafeName(name));
    public static string SafeName(string name) => new(name.Select(ch => char.IsLetterOrDigit(ch) || ch is '-' or '_' ? ch : '_').ToArray());

    /// <summary>FNV-1a 64 of a file, the base-page identity the native runtime re-checks before redirecting.</summary>
    public static ulong Fnv64(byte[] data)
    {
        ulong h = 0xcbf29ce484222325;
        foreach (var b in data) { h ^= b; h *= 0x100000001b3; }
        return h;
    }

    static string I(double v) => Math.Round(v, 2).ToString("0.##", CultureInfo.InvariantCulture);

    static string ActionTokens(ActionBinding a, Func<string, int> resolveScreen)
    {
        var t = new List<string> { a.Type };
        if (a.Command is int c) t.Add($"command={c}");
        if (a.Screen != null) t.Add($"screen={resolveScreen(a.Screen)}");
        if (a.Key != null) t.Add($"key={a.Key}");
        if (a.Value is int v) t.Add($"value={v}");
        if (a.Min is int mn) t.Add($"min={mn}");
        if (a.Max is int mx) t.Add($"max={mx}");
        if (a.Step is int st) t.Add($"step={st}");
        if (a.Extension != null) t.Add($"ext={a.Extension}");
        if (a.Args != null) t.Add($"args={a.Args.Replace('\t', ' ')}");
        return string.Join('\t', t);
    }

    public static string RuntimeTable(CompiledLayout layout, GameData data, ExeTables? exe)
    {
        int Resolve(string screen)
        {
            var custom = layout.Screens.FirstOrDefault(s => s.IsCustom && s.Name == screen);
            if (custom != null) return custom.NativeId;
            return exe?.ScreenId(screen) ?? -1;
        }
        var sb = new StringBuilder();
        sb.Append("MRMENU\t").Append(RuntimeFormat).Append('\n');
        sb.Append("layout\t").Append(layout.Name).Append('\n');
        sb.Append("mouse\t").Append(layout.Mouse ? 1 : 0).Append('\n');
        sb.Append("aspects\t").Append(string.Join('\t', layout.Aspects)).Append('\n');
        foreach (var s in layout.Screens)
        {
            var basePath = Compiler.ScenePath(s.Base);
            var src = s.IsCustom ? "custom" : data.Source(basePath);
            var fnv = s.IsCustom ? 0 : Fnv64(data.Read(basePath) ?? Array.Empty<byte>());
            sb.Append($"screen\t{s.SceneName}\t{s.NativeId}\t{(s.IsCustom ? "custom" : "retail")}\t{src}\t{fnv:x16}\n");
            foreach (var a in layout.Aspects) sb.Append($"variant\t{s.SceneName}\t{a}\t{Aspect.Parse(a).FileKey}/{s.SceneName}.xml\n");
            if (s.DefaultFocus is int f) sb.Append($"focus\t{s.SceneName}\t{f}\n");
            if (s.Back != null) sb.Append($"back\t{s.SceneName}\t{ActionTokens(s.Back, Resolve)}\n");
            foreach (var b in s.Buttons)
            {
                // Retail commands stay with the native AI; only runtime-owned bindings are listed as actions.
                var action = b.Status is BindingStatus.NativeRetail ? new ActionBinding { Type = ActionBinding.Native } : b.Action;
                sb.Append($"button\t{s.SceneName}\t{b.Id}\t{b.Egg}\t{(b.Enabled ? 1 : 0)}\t{I(b.Local.X0)} {I(b.Local.Y0)} {I(b.Local.X1)} {I(b.Local.Y1)}\t{ActionTokens(action, Resolve)}\n");
                foreach (var (a, r) in b.Hit) sb.Append($"hit\t{s.SceneName}\t{b.Id}\t{a}\t{I(r.X0)} {I(r.Y0)} {I(r.X1)} {I(r.Y1)}\n");
            }
        }
        sb.Append("end\n");
        return sb.ToString();
    }

    public sealed record InstallResult(string Directory, List<string> Files, string RuntimeTable);

    public static InstallResult Install(MenuProject project, CompiledLayout layout, GameData data, ExeTables? exe, bool activate = true, string? targetRoot = null)
    {
        var root = targetRoot ?? data.Root;
        var dir = LayoutDir(root, layout.Name);
        if (Directory.Exists(dir)) Directory.Delete(dir, true);
        Directory.CreateDirectory(dir);
        var files = new List<string>();
        void Write(string rel, byte[] bytes)
        {
            var p = Path.Combine(dir, rel.Replace('/', Path.DirectorySeparatorChar));
            Directory.CreateDirectory(Path.GetDirectoryName(p)!);
            File.WriteAllBytes(p, bytes);
            files.Add(rel);
        }
        foreach (var s in layout.Screens)
        {
            foreach (var (a, doc) in s.Variants) Write($"{Aspect.Parse(a).FileKey}/{s.SceneName}.xml", doc.Serialize());
            if (s.Hnt != null) Write($"{s.SceneName}.hnt", s.Hnt);
        }
        var table = RuntimeTable(layout, data, exe);
        Write("runtime.txt", Encoding.ASCII.GetBytes(table));
        Write("project.mrmenu.json", Encoding.UTF8.GetBytes(project.ToJson()));
        var manifest = new
        {
            format = "mr-menu-layout", version = RuntimeFormat, name = layout.Name, built = DateTime.UtcNow.ToString("o"),
            exe = exe?.Sha256, screens = layout.Screens.Select(s => new { s.Name, s.SceneName, s.NativeId, s.IsCustom, s.Base, s.BaseSource, s.BaseSha256 }),
            files = files.Select(f => new { path = f, sha256 = GameData.Sha256(File.ReadAllBytes(Path.Combine(dir, f))) }),
        };
        Write("layout.json", JsonSerializer.SerializeToUtf8Bytes(manifest, new JsonSerializerOptions { WriteIndented = true }));
        if (activate) SetActive(root, layout.Name);
        return new InstallResult(dir, files, table);
    }

    public static string ConfigPath(string gameRoot) => Path.Combine(gameRoot, Folder, "MenuBuilder.ini");

    /// <summary>Selects a layout (Enabled=1) or Classic (name null → Enabled=0). The layout files stay on disk.</summary>
    public static void SetActive(string gameRoot, string? layout)
    {
        Directory.CreateDirectory(Path.Combine(gameRoot, Folder));
        var current = ReadConfig(gameRoot);
        var text = "; Master Rallye Menu Builder runtime selection (read by dinput8.dll at start)\r\n" +
                   "[General]\r\nConfigVersion=1\r\n" +
                   $"Enabled={(layout != null ? 1 : 0)}\r\n" +
                   $"Layout={SafeName(layout ?? current.layout ?? "")}\r\n" +
                   "\r\n[Diagnostics]\r\n; 1 = write MenuBuilder/live/<screen>.txt (eggs, focus, hitboxes) on every screen load\r\n" +
                   $"LiveDump={(current.liveDump ? 1 : 0)}\r\n";
        File.WriteAllText(ConfigPath(gameRoot), text, Encoding.ASCII);
    }

    public static (bool enabled, string? layout, bool liveDump, string? autoTest) ReadConfig(string gameRoot)
    {
        var p = ConfigPath(gameRoot);
        if (!File.Exists(p)) return (false, null, true, null);
        bool enabled = false, live = true; string? layout = null, autoTest = null;
        foreach (var line in File.ReadAllLines(p))
        {
            var kv = line.Split('=', 2);
            if (kv.Length != 2) continue;
            var k = kv[0].Trim(); var v = kv[1].Trim();
            if (k.Equals("Enabled", StringComparison.OrdinalIgnoreCase)) enabled = v == "1";
            else if (k.Equals("Layout", StringComparison.OrdinalIgnoreCase)) layout = v.Length > 0 ? v : null;
            else if (k.Equals("LiveDump", StringComparison.OrdinalIgnoreCase)) live = v == "1";
            else if (k.Equals("AutoTest", StringComparison.OrdinalIgnoreCase)) autoTest = v.Length > 0 ? v : null;
        }
        return (enabled, layout, live, autoTest);
    }

    public static IEnumerable<string> InstalledLayouts(string gameRoot)
    {
        var d = Path.Combine(gameRoot, Folder, "Layouts");
        return Directory.Exists(d) ? Directory.GetDirectories(d).Select(Path.GetFileName).Where(n => n != null)! : Enumerable.Empty<string>();
    }

    public static bool Uninstall(string gameRoot, string name)
    {
        var dir = LayoutDir(gameRoot, name);
        var cfg = ReadConfig(gameRoot);
        if (cfg.layout == SafeName(name)) SetActive(gameRoot, null);
        if (!Directory.Exists(dir)) return false;
        Directory.Delete(dir, true);
        return true;
    }
}
