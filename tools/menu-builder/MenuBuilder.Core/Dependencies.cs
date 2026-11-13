namespace MenuBuilder.Core;

/// <summary>How safe it is to delete or rename an element of a screen.</summary>
public enum ElementClass
{
    /// <summary>Native code or another egg finds this element by name, or it is the screen controller/camera.
    /// Deleting or renaming it breaks the screen; hide or disable it instead.</summary>
    NativeRequired,
    /// <summary>Retail element without a known reference (decoration, static text): deleting it is safe.</summary>
    NativeOptional,
    /// <summary>Created in this project: deleting removes it and every navigation reference to it.</summary>
    UserCreated,
    /// <summary>Retail focusable whose Button ID is a command of the native screen AI, or an element whose
    /// references cannot be proven absent. Treated like NativeRequired by default.</summary>
    UnknownDependency,
}

public sealed record Dependency(string Kind, string Detail);

public sealed record DependencyReport(string Element, ElementClass Class, List<Dependency> Dependencies)
{
    public bool BlocksDelete => Class is ElementClass.NativeRequired or ElementClass.UnknownDependency;
    public bool BlocksRename => Class is ElementClass.NativeRequired or ElementClass.UnknownDependency || Dependencies.Any(d => d.Kind == "egg-reference");
    /// <summary>Hide/Disable keep the egg (and its name, ID and native links) in the scene.</summary>
    public bool CanHide { get; init; } = true;
    public string Summary => $"{Element}: {Label(Class)}" + (Dependencies.Count > 0 ? " — " + string.Join("; ", Dependencies.Select(d => d.Detail)) : "");

    public static string Label(ElementClass c) => c switch
    {
        ElementClass.NativeRequired => "Native Required", ElementClass.NativeOptional => "Native Optional",
        ElementClass.UserCreated => "User Created", _ => "Unknown Dependency",
    };
}

/// <summary>Raised when an operation would break a native dependency and was not forced.</summary>
public sealed class DependencyException : InvalidOperationException
{
    public IReadOnlyList<DependencyReport> Reports { get; }
    public DependencyException(string operation, IReadOnlyList<DependencyReport> reports)
        : base($"{operation} blocked: " + string.Join(" | ", reports.Select(r => r.Summary)) + ". Use Hide or Disable to keep the native links, or force the operation.")
    { Reports = reports; }
}

/// <summary>
/// Finds the known native references of an element: the screen controller and camera, names that MRallye.exe looks up
/// (string table of the image), references from other eggs of the scene (popup ButtonEgg/Tiles, any AI value equal to
/// the name), Broker keys written by Extra Options, and Button IDs the native screen AI receives as commands.
/// </summary>
public sealed class DependencyAnalyzer
{
    readonly Workspace _ws;
    public DependencyAnalyzer(Workspace ws) { _ws = ws; }

    public DependencyReport Analyze(MenuProject project, ScreenDef screen, string egg)
    {
        var deps = new List<Dependency>();
        var def = screen.Element(egg) ?? screen.ForBase(egg);
        var scene = _ws.Compiler.BuildScene(project, screen);
        var e = scene.Find(egg);
        // References from other eggs count for every element, user-created ones included.
        foreach (var other in scene.Eggs.Where(o => o.Name != egg))
            foreach (var ai in other.Ais)
                foreach (var v in ai.Body?.Elements("Value") ?? Enumerable.Empty<System.Xml.Linq.XElement>())
                    if ((string?)v.Attribute("Value") == egg)
                        deps.Add(new("egg-reference", $"referenced by {other.Name} ({ai.Name} '{(string?)v.Attribute("Name")}')"));
        if (e?.ButtonId is int bid && bid > 0)
        {
            var linking = scene.Focusables.Where(f => f.Name != egg && f.Focusable is { } fa &&
                new[] { "Up Path", "Down Path", "Left Path", "Right Path" }.Any(p => fa.GetInt(p) == bid)).Select(f => f.Name).ToList();
            if (linking.Count > 0) deps.Add(new("navigation", $"focus path target of {string.Join(", ", linking)} (rerouted automatically)"));
            if (screen.DefaultFocus == bid) deps.Add(new("navigation", "default focus of the screen"));
        }
        if (def?.IsNew == true)
            return new DependencyReport(egg, deps.Any(d => d.Kind == "egg-reference") ? ElementClass.NativeRequired : ElementClass.UserCreated, deps);
        if (e == null) return new DependencyReport(egg, ElementClass.UnknownDependency, deps) { CanHide = false };

        var cls = ElementClass.NativeOptional;
        if (e.Kind is ElementKind.Screen or ElementKind.Camera)
        {
            deps.Add(new("controller", e.Kind == ElementKind.Screen ? $"screen controller ({scene.ScreenAi})" : "scene camera"));
            return new DependencyReport(egg, ElementClass.NativeRequired, deps) { CanHide = false };
        }
        var baseName = def?.Base ?? egg;
        if (_ws.Exe?.Strings.Contains(baseName) == true)
        {
            deps.Add(new("exe-name", $"MRallye.exe looks up '{baseName}' by name"));
            cls = ElementClass.NativeRequired;
        }
        if (deps.Any(d => d.Kind == "egg-reference")) cls = ElementClass.NativeRequired;
        foreach (var ai in e.Ais)
            foreach (var v in ai.Body?.Elements("Value") ?? Enumerable.Empty<System.Xml.Linq.XElement>())
                if (((string?)v.Attribute("Value"))?.StartsWith("Frontend/ExtraOptions/", StringComparison.Ordinal) == true)
                {
                    deps.Add(new("extra-options", $"Extra Options drives '{(string?)v.Attribute("Value")}' through this element"));
                    cls = ElementClass.NativeRequired;
                }
        if (!screen.IsCustom && e.ButtonId is int id && id > 0 && cls != ElementClass.NativeRequired &&
            _ws.Compiler.Base(screen.Base).Focusables.Any(f => f.ButtonId == id))
        {
            deps.Add(new("native-command", $"Button ID {id} is a command of the native screen AI {_ws.Compiler.Base(screen.Base).ScreenAi}; its handling cannot be proven absent"));
            cls = ElementClass.UnknownDependency;
        }
        return new DependencyReport(egg, cls, deps);
    }

    public List<DependencyReport> Analyze(MenuProject project, ScreenDef screen, IEnumerable<string> eggs) =>
        eggs.Select(n => Analyze(project, screen, n)).ToList();
}
