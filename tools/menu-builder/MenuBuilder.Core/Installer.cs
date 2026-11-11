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
    /// <summary>2 = author-blocked buttons (hidden/disabled) and dynamic values. A format-1 runtime rejects it and keeps the
    /// Classic frontend instead of serving hidden buttons as clickable.</summary>
    public const int RuntimeFormat = 2;

    public const string BuilderVersion = "1.1.0";

    /// <summary>Folder of an installed layout; the name is validated, never rewritten.</summary>
    public static string LayoutDir(string gameRoot, string name)
    {
        var dir = Path.Combine(LayoutsRoot(gameRoot), LayoutName.Validate(name));
        if (!SafeFs.IsStrictlyInside(LayoutsRoot(gameRoot), dir)) throw new UnsafePathException($"layout path {dir} leaves the Layouts folder");
        return dir;
    }

    /// <summary>FNV-1a 64 of a file, the base-page identity the native runtime re-checks before redirecting.</summary>
    public static ulong Fnv64(byte[] data)
    {
        ulong h = 0xcbf29ce484222325;
        foreach (var b in data) { h ^= b; h *= 0x100000001b3; }
        return h;
    }

    static string I(double v) => Math.Round(v, 2).ToString("0.##", CultureInfo.InvariantCulture);

    /// <summary>Runtime table cells are tab separated, one record per line, printable ASCII.</summary>
    static string Clean(string s) => new(s.Select(c => c is < ' ' or > '~' ? ' ' : c).ToArray());

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
        if (a.Args != null) t.Add($"args={Clean(a.Args)}");
        if (a.Type == ActionBinding.Ext) t.Add($"optional={(a.Optional == false ? 0 : 1)}");
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
                sb.Append($"button\t{s.SceneName}\t{b.Id}\t{b.Egg}\t{(b.Blocked ? 0 : 1)}\t{I(b.Local.X0)} {I(b.Local.Y0)} {I(b.Local.X1)} {I(b.Local.Y1)}\t{ActionTokens(action, Resolve)}\n");
                foreach (var (a, r) in b.Hit) sb.Append($"hit\t{s.SceneName}\t{b.Id}\t{a}\t{I(r.X0)} {I(r.Y0)} {I(r.X1)} {I(r.Y1)}\n");
            }
            foreach (var v in s.Values)
                sb.Append($"value\t{s.SceneName}\t{v.Egg}\t{v.Key}\t{v.Source}\t{Clean(v.Fallback)}\t{Clean(v.Format)}\n");
        }
        sb.Append("end\n");
        return sb.ToString();
    }

    public enum Outcome { Installed, Updated, ValidationFailed, RollbackCompleted, InstallationFailed }

    public sealed class Options
    {
        /// <summary>Select the layout in MenuBuilder.ini after publishing.</summary>
        public bool Activate { get; init; } = true;
        /// <summary>Folder that holds MRallye.exe (default: the game root of the data).</summary>
        public string? TargetRoot { get; init; }
        /// <summary>Replace an installed layout of the same name that belongs to another project.</summary>
        public bool ReplaceForeign { get; init; }
    }

    public sealed record InstallResult(Outcome Outcome, string? Directory, List<string> Files, string? RuntimeTable, string Message,
                                       List<Finding> Findings, string? KeptBackup = null)
    {
        public bool Ok => Outcome is Outcome.Installed or Outcome.Updated;
        public string Title => Outcome switch
        {
            Outcome.Installed => "Installed", Outcome.Updated => "Updated", Outcome.ValidationFailed => "Validation Failed",
            Outcome.RollbackCompleted => "Rollback Completed", _ => "Installation Failed",
        };
    }

    /// <summary>Test hook: called with the name of each publication step ("staged", "backed-up", "published",
    /// "activated"); throwing simulates a failure at that point. Never set by the editor or the CLI.</summary>
    public static Action<string>? FaultInjection { get; set; }
    static void Step(string name) => FaultInjection?.Invoke(name);

    public static string LayoutsRoot(string gameRoot) => Path.Combine(SafeFs.Full(gameRoot), Folder, "Layouts");

    /// <summary>
    /// Transactional install: validate, compile into a staging folder next to the live one (same volume), verify the
    /// staged files, rename the live layout to a backup, rename the staged folder into place, activate, then delete
    /// the backup. Any failure before the swap leaves the live layout untouched; a failure after it renames the backup
    /// back (Rollback Completed). Directory renames on one NTFS volume are atomic; file copies are never used to publish.
    /// </summary>
    public static InstallResult Install(MenuProject project, CompiledLayout layout, IReadOnlyList<Finding> findings, GameData data, ExeTables? exe, Options? options = null)
    {
        options ??= new Options();
        var all = findings.ToList();
        var nameProblem = LayoutName.Problem(layout.Name);
        if (nameProblem != null)
            all.Insert(0, new Finding(Severity.Error, "*", null, "LAYOUT_NAME", $"invalid layout name '{layout.Name}': {nameProblem}")
                { Operation = "install", Fix = $"rename the project, e.g. '{LayoutName.Suggest(layout.Name)}'" });
        int errors = all.Count(f => f.Severity == Severity.Error);
        if (errors > 0)
            return new(Outcome.ValidationFailed, null, new(), null, $"{errors} error(s); nothing was written and the installed layout is unchanged", all);

        string root, layouts, live;
        try
        {
            root = SafeFs.Full(options.TargetRoot ?? data.Root);
            if (!System.IO.Directory.Exists(root)) throw new DirectoryNotFoundException($"target folder {root} does not exist");
            layouts = LayoutsRoot(root);
            SafeFs.CreateDirectoryChecked(root, Path.Combine(root, Folder));
            SafeFs.CreateDirectoryChecked(root, layouts);
            live = Path.Combine(layouts, layout.Name);
            SafeFs.RequireInside(layouts, live);
        }
        catch (Exception ex) { return new(Outcome.InstallationFailed, null, new(), null, "Cannot prepare the Layouts folder: " + ex.Message, all); }

        var notes = new List<string>();
        try { RecoverInterrupted(layouts, layout.Name, notes); }
        catch (Exception ex) { return new(Outcome.InstallationFailed, live, new(), null, "An interrupted earlier install could not be recovered: " + ex.Message, all); }

        bool existed = System.IO.Directory.Exists(live);
        if (existed && !options.ReplaceForeign)
        {
            var owner = Owner(live);
            if (!SameOwner(owner, project))
                return new(Outcome.ValidationFailed, live, new(), null,
                    $"a layout named '{layout.Name}' is already installed by another project ({owner.name ?? "unknown"}{(owner.id != null ? ", id " + owner.id : "")}); " +
                    "rename this project or replace that layout explicitly", all);
        }

        var id = Guid.NewGuid().ToString("N")[..8];
        var stage = Path.Combine(layouts, $".mb-stage-{layout.Name}-{id}");
        var backup = Path.Combine(layouts, $".mb-backup-{layout.Name}-{id}");
        List<string> files;
        string table;
        try
        {
            SafeFs.CreateDirectoryChecked(layouts, stage);
            (files, table) = WriteLayout(stage, project, layout, data, exe);
            Verify(stage, layout, files);
            Step("staged");
        }
        catch (Exception ex)
        {
            TryDelete(layouts, stage);
            return new(Outcome.InstallationFailed, live, new(), null, $"Compiling into the staging folder failed ({ex.Message}); the installed layout is unchanged", all);
        }

        // Swap: live -> backup, stage -> live.
        if (existed)
        {
            try { SafeFs.RequireInside(layouts, live); System.IO.Directory.Move(live, backup); Step("backed-up"); }
            catch (Exception ex)
            {
                if (!System.IO.Directory.Exists(live) && System.IO.Directory.Exists(backup)) { try { System.IO.Directory.Move(backup, live); } catch { } }
                TryDelete(layouts, stage);
                return new(Outcome.InstallationFailed, live, new(), null, $"The installed layout could not be replaced: {Locked(ex)}; it is unchanged", all);
            }
        }
        var iniPath = ConfigPath(root);
        byte[]? iniBefore = File.Exists(iniPath) ? File.ReadAllBytes(iniPath) : null;
        try
        {
            System.IO.Directory.Move(stage, live);
            Step("published");
            if (options.Activate) { SetActive(root, layout.Name); Step("activated"); }
        }
        catch (Exception ex)
        {
            var reason = Locked(ex);
            try
            {
                if (options.Activate)
                {
                    if (iniBefore != null) SafeFs.WriteAtomic(iniPath, iniBefore);
                    else if (File.Exists(iniPath)) File.Delete(iniPath);
                }
                if (System.IO.Directory.Exists(live) && (!existed || System.IO.Directory.Exists(backup)))
                {
                    var failed = Path.Combine(layouts, $".mb-failed-{layout.Name}-{id}");
                    System.IO.Directory.Move(live, failed);
                    TryDelete(layouts, failed);
                }
                if (existed) System.IO.Directory.Move(backup, live);
                TryDelete(layouts, stage);
                return new(Outcome.RollbackCompleted, live, new(), null,
                    existed ? $"Publishing failed ({reason}); the previous layout was restored" : $"Publishing failed ({reason}); nothing is installed", all);
            }
            catch (Exception rex)
            {
                return new(Outcome.InstallationFailed, live, new(), null,
                    $"Publishing failed ({reason}) and the rollback did not finish ({rex.Message}); the previous layout is kept in {backup} and is restored automatically by the next install",
                    all, existed ? backup : null);
            }
        }
        if (existed) TryDelete(layouts, backup, notes);
        var msg = $"{(existed ? "Updated" : "Installed")} {files.Count} files in {live}{(options.Activate ? " (active)" : "")}";
        if (notes.Count > 0) msg += "; " + string.Join("; ", notes);
        return new(existed ? Outcome.Updated : Outcome.Installed, live, files, table, msg, all);
    }

    static string Locked(Exception ex) => ex is IOException or UnauthorizedAccessException
        ? $"{ex.Message.TrimEnd('.')} - a file may be open in the running game or another program"
        : ex.Message;

    static void TryDelete(string layouts, string dir, List<string>? notes = null)
    {
        try { SafeFs.DeleteTree(layouts, dir); }
        catch (Exception ex) { notes?.Add($"temporary folder {Path.GetFileName(dir)} could not be removed ({ex.Message}); it is cleaned up by the next install"); }
    }

    static bool IsTemp(string folder, string kind, string name) =>
        folder.Length == $".mb-{kind}-{name}-".Length + 8 && folder.StartsWith($".mb-{kind}-{name}-", StringComparison.OrdinalIgnoreCase);

    /// <summary>Restores a backup left by an interrupted swap and removes stale staging/backup folders of this name.</summary>
    public static void RecoverInterrupted(string layouts, string name, List<string> notes)
    {
        if (!System.IO.Directory.Exists(layouts)) return;
        var live = Path.Combine(layouts, name);
        var mine = new DirectoryInfo(layouts).GetDirectories(".mb-*")
            .Where(d => new[] { "stage", "backup", "failed", "trash" }.Any(k => IsTemp(d.Name, k, name))).ToList();
        var backups = mine.Where(d => IsTemp(d.Name, "backup", name)).OrderByDescending(d => d.LastWriteTimeUtc).ToList();
        if (!System.IO.Directory.Exists(live) && backups.Count > 0)
        {
            SafeFs.RequireInside(layouts, backups[0].FullName);
            System.IO.Directory.Move(backups[0].FullName, live);
            notes.Add($"restored the layout from an interrupted install ({backups[0].Name})");
            mine.Remove(backups[0]);
        }
        foreach (var d in mine.Where(d => System.IO.Directory.Exists(d.FullName))) TryDelete(layouts, d.FullName, notes);
    }

    static (string? name, string? id) Owner(string liveDir)
    {
        try
        {
            using var doc = JsonDocument.Parse(File.ReadAllBytes(Path.Combine(liveDir, "layout.json")));
            var r = doc.RootElement;
            string? Str(string k) => r.TryGetProperty(k, out var v) && v.ValueKind == JsonValueKind.String ? v.GetString() : null;
            return (Str("project") ?? Str("name"), Str("projectId"));
        }
        catch { return (null, Unreadable); }
    }
    const string Unreadable = "?unreadable";

    /// <summary>Same owner: equal project IDs, or a side without an ID (layouts and projects of version 1.0).</summary>
    static bool SameOwner((string? name, string? id) owner, MenuProject project) =>
        owner.id != Unreadable && (owner.id == null || project.Id == null || string.Equals(owner.id, project.Id, StringComparison.OrdinalIgnoreCase));

    static (List<string> files, string table) WriteLayout(string dir, MenuProject project, CompiledLayout layout, GameData data, ExeTables? exe)
    {
        var files = new List<string>();
        void Write(string rel, byte[] bytes)
        {
            var p = Path.Combine(dir, rel.Replace('/', Path.DirectorySeparatorChar));
            SafeFs.RequireInside(dir, p);
            System.IO.Directory.CreateDirectory(Path.GetDirectoryName(p)!);
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
            format = "mr-menu-layout", version = RuntimeFormat, name = layout.Name, project = project.Name, projectId = project.Id,
            builder = BuilderVersion, built = DateTime.UtcNow.ToString("o"),
            exe = exe?.Sha256, screens = layout.Screens.Select(s => new { s.Name, s.SceneName, s.NativeId, s.IsCustom, s.Base, s.BaseSource, s.BaseSha256 }),
            files = files.Select(f => new { path = f, sha256 = GameData.Sha256(File.ReadAllBytes(Path.Combine(dir, f))) }).ToList(),
        };
        Write("layout.json", JsonSerializer.SerializeToUtf8Bytes(manifest, new JsonSerializerOptions { WriteIndented = true }));
        return (files, table);
    }

    /// <summary>Completeness check of a staged layout before it is published.</summary>
    static void Verify(string dir, CompiledLayout layout, List<string> files)
    {
        using var doc = JsonDocument.Parse(File.ReadAllBytes(Path.Combine(dir, "layout.json")));
        foreach (var f in doc.RootElement.GetProperty("files").EnumerateArray())
        {
            var rel = f.GetProperty("path").GetString()!;
            var path = Path.Combine(dir, rel.Replace('/', Path.DirectorySeparatorChar));
            if (!File.Exists(path) || GameData.Sha256(File.ReadAllBytes(path)) != f.GetProperty("sha256").GetString())
                throw new InvalidDataException($"staged file {rel} is missing or differs");
        }
        var table = File.ReadAllText(Path.Combine(dir, "runtime.txt"), Encoding.ASCII);
        if (!table.StartsWith($"MRMENU\t{RuntimeFormat}\n", StringComparison.Ordinal) || !table.EndsWith("end\n", StringComparison.Ordinal))
            throw new InvalidDataException("runtime table is truncated");
        foreach (var s in layout.Screens)
            foreach (var a in layout.Aspects)
                if (!files.Contains($"{Aspect.Parse(a).FileKey}/{s.SceneName}.xml")) throw new InvalidDataException($"variant {a} of {s.SceneName} was not written");
    }

    public static string ConfigPath(string gameRoot) => Path.Combine(gameRoot, Folder, "MenuBuilder.ini");

    /// <summary>Selects a layout (Enabled=1) or Classic (name null → Enabled=0). The layout files stay on disk.</summary>
    public static void SetActive(string gameRoot, string? layout)
    {
        if (layout != null) LayoutName.Validate(layout);
        var root = SafeFs.Full(gameRoot);
        SafeFs.CreateDirectoryChecked(root, Path.Combine(root, Folder));
        var current = ReadConfig(root);
        var keep = layout ?? (LayoutName.IsValid(current.layout) ? current.layout : null) ?? "";
        var text = "; Master Rallye Menu Builder runtime selection (read by dinput8.dll at start)\r\n" +
                   "[General]\r\nConfigVersion=1\r\n" +
                   $"Enabled={(layout != null ? 1 : 0)}\r\n" +
                   $"Layout={keep}\r\n" +
                   "\r\n[Diagnostics]\r\n; 1 = write MenuBuilder/live/<screen>.txt (eggs, focus, hitboxes) on every screen load\r\n" +
                   $"LiveDump={(current.liveDump ? 1 : 0)}\r\n" +
                   (current.autoTest != null ? $"; scripted in-game check (tools/menu-builder/test/*.autotest)\r\nAutoTest={current.autoTest}\r\n" : "");
        SafeFs.WriteAtomic(ConfigPath(root), Encoding.ASCII.GetBytes(text));
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

    /// <summary>Installed layouts (valid names only; staging, backup and foreign folders are not listed).</summary>
    public static IEnumerable<string> InstalledLayouts(string gameRoot)
    {
        var d = LayoutsRoot(gameRoot);
        return Directory.Exists(d)
            ? Directory.GetDirectories(d).Select(Path.GetFileName).Where(n => n != null && LayoutName.IsValid(n) && !SafeFs.IsReparsePoint(Path.Combine(d, n))).Select(n => n!)
            : Enumerable.Empty<string>();
    }

    /// <summary>Removes one installed layout; switches to Classic first when it is the active one.</summary>
    public static bool Uninstall(string gameRoot, string name)
    {
        var dir = LayoutDir(gameRoot, name);
        var layouts = LayoutsRoot(gameRoot);
        var cfg = ReadConfig(gameRoot);
        if (string.Equals(cfg.layout, name, StringComparison.OrdinalIgnoreCase)) SetActive(gameRoot, null);
        if (!Directory.Exists(dir)) return false;
        SafeFs.RequireInside(layouts, dir);
        var trash = Path.Combine(layouts, $".mb-trash-{name}-{Guid.NewGuid().ToString("N")[..8]}");
        Directory.Move(dir, trash);
        SafeFs.DeleteTree(layouts, trash);
        return true;
    }
}
