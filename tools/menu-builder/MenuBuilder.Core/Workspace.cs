using System.Text.Json;

namespace MenuBuilder.Core;

/// <summary>Everything bound to one game installation; the single entry point for the editor, CLI and tools.</summary>
public sealed class Workspace : IDisposable
{
    public GameData Data { get; }
    public ExeTables? Exe { get; }
    public string? ExeError { get; }
    public AssetCache Assets { get; }
    public LayoutEngine Layout { get; }
    public Compiler Compiler { get; }
    public SceneRenderer Renderer { get; }
    public Validator Validator { get; }

    /// <param name="exePath">MRallye.exe when it is not inside <paramref name="gameRoot"/> (SDK launcher resource roots).</param>
    public Workspace(string gameRoot, string? exePath = null)
    {
        Data = new GameData(gameRoot);
        var exe = exePath ?? Path.Combine(Data.Root, "MRallye.exe");
        if (File.Exists(exe)) { try { Exe = new ExeTables(exe); } catch (Exception ex) { Exe = null; ExeError = ex.ToString(); } }
        Assets = new AssetCache(Data);
        Layout = new LayoutEngine(Assets, Exe);
        Compiler = new Compiler(Data, Layout);
        Renderer = new SceneRenderer(Layout);
        Validator = new Validator(Layout, Exe);
    }

    public void Dispose() => Data.Dispose();

    /// <summary>Retail frontend screens that exist as scenes (Data.sma or loose).</summary>
    public IEnumerable<(int id, string name, string source)> RetailScreens()
    {
        IReadOnlyList<string> names = Exe?.Screens ?? new List<string>();
        for (int i = 0; i < names.Count; i++)
        {
            var path = Compiler.ScenePath(names[i]);
            if (Data.Exists(path) && !names.Take(i).Contains(names[i])) yield return (i, names[i], Data.Source(path));
        }
    }

    public ScreenDef NewRetailScreen(string name) => new()
    {
        Name = name, Kind = ScreenDef.Retail, Base = name, BaseSha256 = Compiler.BaseSha(name),
    };

    public ScreenDef NewCustomScreen(string name, string? title = null, string visualBase = Compiler.HostScreen, bool keepButtons = false)
    {
        var s = new ScreenDef { Name = name, Kind = ScreenDef.Custom, Base = visualBase, BaseSha256 = Compiler.BaseSha(visualBase), Title = title ?? name.ToUpperInvariant() };
        if (!keepButtons)
            foreach (var egg in Compiler.Base(visualBase).Focusables)
                s.Elements.Add(new ElementDef { Name = egg.Name, Base = egg.Name, Deleted = true, Note = "removed from visual base" });
        return s;
    }

    /// <summary>Scene of a screen with all project edits (4:3, no anchors).</summary>
    public SceneDocument Scene(MenuProject project, ScreenDef screen) => Compiler.BuildScene(project, screen);

    public SceneDocument SceneVariant(MenuProject project, ScreenDef screen, string aspect) =>
        PreviewStates(screen, Compiler.Variant(project, screen, Compiler.BuildScene(project, screen), aspect));

    /// <summary>
    /// Preview of run-time states: buttons bound to an action that has no handler yet (planned or another module) are
    /// served disabled by the runtime, so previews grey them the same way. Compiled pages keep them enabled; the
    /// runtime decides when the screen is loaded.
    /// </summary>
    public static SceneDocument PreviewStates(ScreenDef screen, SceneDocument doc)
    {
        foreach (var egg in doc.Focusables)
        {
            var def = screen.Element(egg.Name) ?? screen.ForBase(egg.Name);
            if (def?.Action is not { Type: ActionBinding.Ext } a) continue;
            var info = ActionCatalog.Find(a.Extension);
            if ((info == null || info.Owner == ActionOwner.Planned) && egg.Focusable!.Has("Enabled")) egg.Focusable.Set("Enabled", "False", "Bool");
        }
        return doc;
    }

    public (CompiledLayout layout, List<Finding> findings) Build(MenuProject project)
    {
        Assets.Missing.Clear();
        Layout.Language = project.Settings.Language;
        var compiled = Compiler.Compile(project, Exe);
        return (compiled, Validator.Validate(project, compiled));
    }

    /// <summary>Validate, compile and publish transactionally (see <see cref="Installer.Install"/>). Errors block it.</summary>
    public Installer.InstallResult Install(MenuProject project, Installer.Options? options = null)
    {
        CompiledLayout layout;
        List<Finding> findings;
        try { (layout, findings) = Build(project); }
        catch (Exception ex)
        {
            return new Installer.InstallResult(Installer.Outcome.ValidationFailed, null, new(), null, "Compilation failed: " + ex.Message,
                new() { new Finding(Severity.Error, "*", null, "COMPILE_FAILED", ex.Message) { Operation = "compile project" } });
        }
        return Installer.Install(project, layout, findings, Data, Exe, options);
    }

    // ---- screen exchange (*.mrscreen.json) -------------------------------------------------------

    public sealed class ScreenPackage
    {
        public string Format { get; set; } = "mr-menu-screen";
        public int Version { get; set; } = 1;
        public ScreenDef Screen { get; set; } = new();
        public Dictionary<string, ElementPatch> Styles { get; set; } = new();
        public Dictionary<string, ComponentDef> Components { get; set; } = new();
    }

    public static string ExportScreen(MenuProject project, string screenName)
    {
        var s = project.Screen(screenName) ?? throw new KeyNotFoundException(screenName);
        var pkg = new ScreenPackage { Screen = JsonSerializer.Deserialize<ScreenDef>(JsonSerializer.Serialize(s, MenuProject.Json), MenuProject.Json)! };
        foreach (var el in s.Elements)
        {
            if (el.Style != null && project.Styles.TryGetValue(el.Style, out var st)) pkg.Styles[el.Style] = st;
            if (el.Template?.StartsWith("component:") == true && project.Components.TryGetValue(el.Template[10..], out var c))
            {
                pkg.Components[el.Template[10..]] = c;
                if (c.Style != null && project.Styles.TryGetValue(c.Style, out var cs)) pkg.Styles[c.Style] = cs;
            }
        }
        return JsonSerializer.Serialize(pkg, MenuProject.Json);
    }

    /// <summary>Imports a screen package; an existing screen with the same name is replaced. Styles/components merge (existing kept).</summary>
    public static ScreenDef ImportScreen(MenuProject project, string json, string? rename = null)
    {
        var pkg = JsonSerializer.Deserialize<ScreenPackage>(json, MenuProject.Json) ?? throw new InvalidDataException("empty screen package");
        if (pkg.Format != "mr-menu-screen") throw new InvalidDataException("not a mr-menu-screen file");
        var s = pkg.Screen;
        if (rename != null) s.Name = rename;
        project.Screens.RemoveAll(x => string.Equals(x.Name, s.Name, StringComparison.OrdinalIgnoreCase));
        project.Screens.Add(s);
        foreach (var (k, v) in pkg.Styles) project.Styles.TryAdd(k, v);
        foreach (var (k, v) in pkg.Components) project.Components.TryAdd(k, v);
        return s;
    }
}
