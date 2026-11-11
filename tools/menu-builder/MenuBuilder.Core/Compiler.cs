using System.Globalization;
using System.Text;
using System.Xml.Linq;

namespace MenuBuilder.Core;

public enum BindingStatus { NativeRetail, NativeRemap, Runtime, Extension, Unbound, Disabled }

public sealed class CompiledButton
{
    public int Id { get; init; }
    public string Egg { get; init; } = "";
    public ElementKind Kind { get; init; }
    public ActionBinding Action { get; init; } = new();
    public BindingStatus Status { get; init; }
    /// <summary>Hitbox relative to the egg translation (scale applied), y up.</summary>
    public UiRect Local { get; init; }
    /// <summary>Absolute authored hitbox per aspect variant.</summary>
    public Dictionary<string, UiRect> Hit { get; } = new();
    public int Up, Down, Left, Right;
    /// <summary>Native "Enabled" flag of the focusable as written in the scene.</summary>
    public bool Enabled = true;
    /// <summary>Hidden by the author (Visible = false on an element that is visible in its base): never focusable or hit.</summary>
    public bool Hidden;
    /// <summary>Hidden or disabled by the author: the runtime gives it no hitbox and swallows its command.</summary>
    public bool Blocked;
}

/// <summary>Dynamic text: the runtime writes the formatted provider value into a Broker Name the text egg displays.</summary>
public sealed class CompiledValue
{
    public string Egg { get; init; } = "";
    public string Key { get; init; } = "";
    public string Source { get; init; } = "";
    public string Format { get; init; } = "{value}";
    public string Fallback { get; init; } = "N/A";
}

/// <summary>Raised while applying one element; becomes an ERROR finding with its code, operation and fix.</summary>
public sealed class BuildException : Exception
{
    public string Code { get; }
    public string Operation { get; }
    public string? Fix { get; }
    public BuildException(string code, string operation, string message, string? fix = null) : base(message) { Code = code; Operation = operation; Fix = fix; }
}

public sealed class CompiledScreen
{
    public string Name { get; init; } = "";
    public bool IsCustom { get; init; }
    /// <summary>Native screen index: retail 0..53, custom 64+.</summary>
    public int NativeId { get; set; }
    /// <summary>Scene name under FrontendScreens/ (custom: MB_&lt;Name&gt;).</summary>
    public string SceneName { get; init; } = "";
    public string Base { get; init; } = "";
    public string BaseSource { get; init; } = "";
    public string BaseSha256 { get; init; } = "";
    public Dictionary<string, SceneDocument> Variants { get; } = new();
    public List<CompiledButton> Buttons { get; } = new();
    public int? DefaultFocus { get; set; }
    public ActionBinding? Back { get; set; }
    public byte[]? Hnt { get; set; }
    public List<CompiledValue> Values { get; } = new();
    /// <summary>Diagnostics of the scene build (errors here block installation).</summary>
    public List<Finding> Diagnostics { get; } = new();
}

public sealed class CompiledLayout
{
    public string Name { get; init; } = "";
    public bool Mouse { get; init; }
    public List<string> Aspects { get; init; } = new();
    public List<CompiledScreen> Screens { get; } = new();
    /// <summary>Project-level diagnostics (screens that could not be built at all, unchanged screens).</summary>
    public List<Finding> Diagnostics { get; } = new();
}

/// <summary>Turns a declarative project into native scene XML per aspect plus runtime tables.</summary>
public sealed class Compiler
{
    public const int FirstCustomScreenId = 64;
    public const string HostScreen = "GraphicsMain", HostAi = "gaFEScreenGraphicsMainAI";
    readonly GameData _data;
    readonly LayoutEngine _layout;
    readonly Dictionary<string, SceneDocument> _bases = new(StringComparer.OrdinalIgnoreCase);

    public Compiler(GameData data, LayoutEngine layout) { _data = data; _layout = layout; }

    public static string ScenePath(string scene) => $"DataScene/FrontendScreens/{scene}.xml";

    /// <summary>Base scene as the installed game loads it (loose page of another mod wins over Data.sma).</summary>
    public SceneDocument Base(string screen, bool archiveOnly = false)
    {
        var key = (archiveOnly ? "A:" : "E:") + screen;
        if (_bases.TryGetValue(key, out var hit)) return hit.Clone();
        var raw = (archiveOnly ? _data.ReadArchive(ScenePath(screen)) : _data.Read(ScenePath(screen)))
                  ?? throw new FileNotFoundException($"screen scene {screen} not found");
        var doc = SceneDocument.Load(screen, raw);
        _bases[key] = doc;
        return doc.Clone();
    }

    public string BaseSha(string screen) => GameData.Sha256(_data.Read(ScenePath(screen)) ?? Array.Empty<byte>());

    public static string SceneNameOf(ScreenDef screen) => screen.IsCustom ? "MB_" + screen.Name : screen.Base;

    /// <summary>Broker Name written by the runtime for a dynamic text element.</summary>
    public static string ValueKey(string scene, string egg) => $"MenuBuilder/{scene}/{egg}";

    public static string FormatValue(string? format, string value) => (format ?? "{value}").Replace("{value}", value, StringComparison.Ordinal);

    /// <summary>
    /// Applies a screen definition to its base and returns the 4:3 document (no aspect shifts). Every element that
    /// cannot be applied, and every requested element that is missing from the result, is reported as an ERROR in
    /// <paramref name="diagnostics"/>; nothing is dropped silently.
    /// </summary>
    public SceneDocument BuildScene(MenuProject project, ScreenDef screen, List<Finding>? diagnostics = null, List<CompiledValue>? values = null)
    {
        var diags = diagnostics ?? new List<Finding>();
        var doc = Base(screen.Base).Clone(SceneNameOf(screen));
        if (screen.IsCustom) EnsureHost(doc, screen.Name, diags);
        var failed = new HashSet<string>(StringComparer.Ordinal);
        foreach (var el in screen.Elements)
        {
            string kind = el.IsNew ? "new element" : (doc.Find(el.Base!)?.Kind.ToString() ?? "retail egg");
            try
            {
                if ((el.IsNew || el.Name != el.Base) && !el.Deleted && !Ids.IsEggName(el.Name))
                    throw new BuildException("INVALID_ID", el.IsNew ? "create element" : "rename element",
                        $"'{el.Name}' is not a valid element name", "use letters, digits and '_' (first character a letter or '_'), at most 63 characters");
                ApplyElement(project, screen, doc, el);
                if (!el.Deleted && ApplyValue(doc, SceneNameOf(screen), el, Effective(project, el)) is { } v) values?.Add(v);
            }
            catch (BuildException ex)
            {
                failed.Add(el.Name);
                diags.Add(new Finding(Severity.Error, screen.Name, el.Name, ex.Code, ex.Message) { ElementType = kind, Operation = ex.Operation, Fix = ex.Fix });
            }
            catch (Exception ex)
            {
                failed.Add(el.Name);
                diags.Add(new Finding(Severity.Error, screen.Name, el.Name, "ELEMENT_BUILD_FAILED", ex.Message)
                    { ElementType = kind, Operation = el.IsNew ? "create element" : "edit retail element", Fix = "undo the last change of this element or delete it" });
            }
        }
        // A requested element must exist in the result; a silent loss would install a screen without it.
        foreach (var el in screen.Elements.Where(e => !e.Deleted && !failed.Contains(e.Name)))
            if (doc.Find(el.Name) == null)
                diags.Add(new Finding(Severity.Error, screen.Name, el.Name, "ELEMENT_MISSING",
                    "the element is not present in the compiled scene") { Operation = "compile scene", Fix = "re-create the element from a template" });
        foreach (var g in screen.Elements.Where(e => !e.Deleted).GroupBy(e => e.Name).Where(g => g.Count() > 1))
            diags.Add(new Finding(Severity.Error, screen.Name, g.Key, "DUPLICATE_DEFINITION", $"{g.Count()} element definitions use this name")
                { Operation = "compile scene", Fix = "rename or delete the duplicates" });
        // New focusables without an ID get the next free one.
        var used = doc.Eggs.Where(e => e.IsFocusable).Select(e => e.ButtonId ?? 0).ToHashSet();
        // Retail screen AIs handle commands that have no button in the XML (e.g. QuickRace 6/7 for player 2):
        // new buttons on retail screens start at 10 so an ID never aliases a hidden native command.
        int first = screen.IsCustom ? 1 : Math.Max(10, used.DefaultIfEmpty(0).Max() + 1);
        foreach (var el in screen.Elements.Where(e => e.IsNew && !e.Deleted && e.Patch.ButtonId == null))
        {
            var egg = doc.Find(el.Name);
            if (egg?.Focusable == null) continue;
            int id = egg.ButtonId ?? 0;
            if (id > 0 && doc.Focusables.Count(f => f.ButtonId == id) == 1) continue;
            int next = first; while (used.Contains(next)) next++;
            egg.Focusable.Set("Button ID", next); used.Add(next);
        }
        SyncPopups(doc);
        if (screen.IsCustom && screen.Title != null)
        {
            var title = doc.Eggs.FirstOrDefault(e => e.Name.EndsWith("TitleText", StringComparison.Ordinal) && e.TextAi != null);
            if (title != null) ApplyPatch(title, new ElementPatch { Text = screen.Title });
        }
        return doc;
    }

    /// <summary>
    /// A gaFrontendPopupAI shares the Button ID of its ButtonEgg and registers its own Up/Down paths for that ID
    /// (MainMenu SureChooser ↔ Quit); keep them equal to the owner's paths so edited navigation is not overridden.
    /// </summary>
    static void SyncPopups(SceneDocument doc)
    {
        foreach (var popup in doc.Eggs.Select(e => e.Ai("gaFrontendPopupAI")).Where(a => a != null))
        {
            var owner = popup!.Get("ButtonEgg") is { } name ? doc.Find(name)?.Focusable : null;
            if (owner == null) continue;
            foreach (var path in new[] { "Up Path", "Down Path", "Left Path", "Right Path" })
                if (popup.Has(path) && owner.GetInt(path) is int v) popup.Set(path, v);
        }
    }

    void EnsureHost(SceneDocument doc, string screen, List<Finding> diags)
    {
        var screenEgg = doc.ScreenEgg;
        if (screenEgg != null && doc.ScreenAi == HostAi) return;
        var host = Base(HostScreen).ScreenEgg;
        if (host == null)
        {
            diags.Add(new Finding(Severity.Error, screen, null, "NO_HOST", $"the {HostScreen} scene has no screen egg to host a custom screen")
                { Operation = "create custom screen host", Fix = "restore the retail GraphicsMain page" });
            return;
        }
        var copy = new XElement(host.Element);
        if (screenEgg != null)
        {
            diags.Add(new Finding(Severity.Info, screen, screenEgg.Name, "HOST", $"screen AI {doc.ScreenAi ?? "?"} of the visual base is replaced by the host {HostAi}"));
            screenEgg.Element.ReplaceWith(copy);
        }
        else doc.Add(copy);
    }

    XElement ResolveTemplate(MenuProject project, ScreenDef screen, SceneDocument doc, string template, out ElementPatch componentPatch)
    {
        componentPatch = new ElementPatch();
        if (template.StartsWith("component:", StringComparison.Ordinal))
        {
            var name = template["component:".Length..];
            if (!project.Components.TryGetValue(name, out var comp))
                throw new BuildException("COMPONENT_MISSING", "create from component", $"component '{name}' is not defined in the project", "import or re-create the component");
            var style = comp.Style != null && project.Styles.TryGetValue(comp.Style, out var s) ? s : null;
            componentPatch = (style ?? new ElementPatch()).Merge(comp.Patch);
            template = comp.Template;
        }
        var slash = template.IndexOf('/');
        Egg? src = slash < 0 ? doc.Find(template) ?? Base(screen.Base).Find(template)
                             : Base(template[..slash]).Find(template[(slash + 1)..]);
        if (src == null)
            throw new BuildException("TEMPLATE_MISSING", "create from template", $"template egg '{template}' does not exist in this installation",
                "pick another template; the retail page or the mod that provided it may have changed");
        if (src.Kind is ElementKind.Screen or ElementKind.Camera)
            throw new BuildException("TEMPLATE_INCOMPATIBLE", "create from template", $"'{template}' is a {src.Kind} egg and cannot be used as an element", "pick a button, text or image template");
        return new XElement(src.Element);
    }

    void ApplyElement(MenuProject project, ScreenDef screen, SceneDocument doc, ElementDef el)
    {
        var style = el.Style != null && project.Styles.TryGetValue(el.Style, out var s) ? s : null;
        if (!el.IsNew)
        {
            var egg = doc.Find(el.Base!);
            if (egg == null)
            {
                if (el.Deleted) return; // nothing left to delete
                throw new BuildException("BASE_EGG_MISSING", "edit retail element", $"'{el.Base}' is not in the {screen.Base} page of this installation",
                    "the base page changed (another mod or game version); delete this edit or re-create the element");
            }
            if (el.Deleted)
            {
                if (egg.Kind == ElementKind.Screen)
                    throw new BuildException("SCREEN_EGG_REQUIRED", "delete element", "the screen controller egg cannot be deleted", "restore it");
                egg.Element.Remove(); return;
            }
            if (el.Name != el.Base && !string.IsNullOrEmpty(el.Name)) egg.Name = el.Name;
            ApplyPatch(egg, (style ?? new ElementPatch()).Merge(el.Patch));
            return;
        }
        if (el.Deleted) return;
        if (el.Template == null) throw new BuildException("TEMPLATE_MISSING", "create element", "new element without a template", "delete it and insert it again");
        if (doc.Find(el.Name) != null)
            throw new BuildException("DUPLICATE_NAME", "create element", $"an egg named '{el.Name}' already exists in this screen", "rename the new element");
        var x = ResolveTemplate(project, screen, doc, el.Template, out var comp);
        var added = doc.Add(x);
        added.Name = el.Name;
        ApplyPatch(added, comp.Merge(style).Merge(el.Patch));
    }

    static string B(bool v) => v ? "True" : "False";

    public static void ApplyPatch(Egg egg, ElementPatch p)
    {
        if (p.X is float x) egg.X = x;
        if (p.Y is float y) egg.Y = y;
        if (p.ScaleX is float sx) egg.ScaleX = sx;
        if (p.ScaleY is float sy) egg.ScaleY = sy;
        if (p.Model != null) egg.Model = p.Model;
        if (p.BankIndex is int bi) egg.BankIndex = bi;
        if (p.DrawPriority is int dp) egg.DrawPriority = dp;
        if (p.Visible is bool vis) egg.Visible = vis;
        var f = egg.Focusable;
        if (f != null)
        {
            if (p.ButtonId is int id) f.Set("Button ID", id);
            if (p.Up is int u) f.Set("Up Path", u);
            if (p.Down is int d) f.Set("Down Path", d);
            if (p.Left is int l) f.Set("Left Path", l);
            if (p.Right is int r) f.Set("Right Path", r);
            if (p.Enabled is bool en && f.Has("Enabled")) f.Set("Enabled", B(en), "Bool");
        }
        var t = egg.TextAi;
        if (t != null)
        {
            bool button = t.Name == "enUITextButtonAI";
            if (p.Text != null) { t.Set("Text String", p.Text, "String"); t.Set("Text*", "Null", "String"); t.Set("Text ID#", 0); t.Set("Text ID Index#", 0); }
            if (p.TextId is int tid) { t.Set("Text ID#", tid); t.Set("Text*", "Null", "String"); }
            if (p.TextIndex is int tix) t.Set("Text ID Index#", tix);
            if (p.TextKey != null) t.Set("Text*", p.TextKey, "String");
            if (p.Font is int font) t.Set(button ? "Font ID#" : "Font#", font);
            if (button)
            {
                if (p.TextOffsetX is int ox) t.Set("Text OffsetX", ox);
                if (p.TextOffsetY is int oy) t.Set("Text OffsetY", oy);
                if (p.HJustify is int hj) t.Set("HJustification", hj);
                if (p.VJustify is int vj) t.Set("VJustification", vj);
            }
            else
            {
                if (p.TextOffsetX != null || p.TextOffsetY != null)
                {
                    var o = (t.Get("Offset") ?? "0 0 0").Split(' ', StringSplitOptions.RemoveEmptyEntries);
                    var ox = p.TextOffsetX?.ToString(CultureInfo.InvariantCulture) ?? o[0];
                    var oy = p.TextOffsetY?.ToString(CultureInfo.InvariantCulture) ?? o[1];
                    t.Set("Offset", $"{ox} {oy} 0.00", "Vector3");
                }
                if (p.HJustify is int hj) t.Set("Horizontal Justification", hj);
                if (p.VJustify is int vj) t.Set("Vertical Justification", vj);
            }
        }
        if (p.Raw != null)
            foreach (var (k, v) in p.Raw)
            {
                var slash = k.IndexOf('/');
                if (slash < 0) throw new BuildException("RAW_KEY", "raw value edit", $"raw key '{k}' must be 'AIName/Value Name'", "fix the key");
                var ai = egg.Ai(k[..slash]) ?? throw new BuildException("RAW_AI_MISSING", "raw value edit", $"AI {k[..slash]} is not on {egg.Name}", "remove the raw edit");
                var type = ai.Body?.Elements("Value").FirstOrDefault(e => (string?)e.Attribute("Name") == k[(slash + 1)..])?.Attribute("Type")?.Value ?? "String";
                ai.Set(k[(slash + 1)..], v, type);
            }
    }

    /// <summary>Dynamic text binding: the element shows the Broker Name the runtime fills from the value provider.</summary>
    CompiledValue? ApplyValue(SceneDocument doc, string scene, ElementDef el, ElementPatch p)
    {
        if (p.ValueSource == null) return null;
        var egg = doc.Find(el.Name);
        if (egg == null) return null;
        if (!ActionCatalog.IsValidId(p.ValueSource))
            throw new BuildException("VALUE_ID", "bind value", $"'{p.ValueSource}' is not a valid value ID", "use a catalog ID such as vehicle.model_source");
        var t = egg.TextAi ?? throw new BuildException("VALUE_NO_TEXT", "bind value", $"{egg.Kind} element has no text to show a value", "bind values to text or label elements");
        var key = ValueKey(scene, el.Name);
        t.Set("Text*", key, "String");
        t.Set("Text String", "Null", "String");
        var info = ActionCatalog.Find(p.ValueSource);
        // Preview: an example value for implemented providers, the fallback for planned/unknown ones (as in game).
        var shown = info != null && info.Owner != ActionOwner.Planned ? info.ValueExample : null;
        _layout.PreviewValues[key] = FormatValue(p.ValueFormat, shown ?? p.ValueFallback ?? "N/A");
        return new CompiledValue { Egg = el.Name, Key = key, Source = ActionCatalog.Canonical(p.ValueSource), Format = p.ValueFormat ?? "{value}", Fallback = p.ValueFallback ?? "N/A" };
    }

    /// <summary>Merged style+patch for an element (used for anchors).</summary>
    public static ElementPatch Effective(MenuProject project, ElementDef el)
    {
        var style = el.Style != null && project.Styles.TryGetValue(el.Style, out var s) ? s : null;
        ElementPatch comp = new();
        if (el.Template?.StartsWith("component:") == true && project.Components.TryGetValue(el.Template[10..], out var c))
            comp = (c.Style != null && project.Styles.TryGetValue(c.Style, out var cs) ? cs : new ElementPatch()).Merge(c.Patch);
        return comp.Merge(style).Merge(el.Patch);
    }

    /// <summary>Document for one aspect variant: anchors shift by ±half, then aspect overrides apply.</summary>
    public SceneDocument Variant(MenuProject project, ScreenDef screen, SceneDocument baseDoc, string aspect)
    {
        var doc = baseDoc.Clone();
        var ratio = Aspect.Parse(aspect).Ratio;
        foreach (var el in screen.Elements.Where(e => !e.Deleted))
        {
            var anchor = Effective(project, el).Anchor;
            var shift = WidescreenModel.AnchorShift(anchor, ratio);
            if (shift == 0) continue;
            var egg = doc.Find(el.Name);
            if (egg != null) egg.X = (float)Math.Round(egg.X + shift, 2);
        }
        if (screen.Aspects.TryGetValue(aspect, out var overrides))
            foreach (var (name, patch) in overrides)
                if (doc.Find(name) is { } egg) ApplyPatch(egg, patch);
        return doc;
    }

    /// <summary>A retail screen without any edit is not served (the native page stays in charge).</summary>
    public static bool IsUnchanged(ScreenDef screen) =>
        !screen.IsCustom && screen.Elements.Count == 0 && screen.Aspects.Values.All(m => m.Count == 0) && screen.DefaultFocus == null && screen.Back == null;

    /// <summary>Patch flag set by the author on an element (base delta, or the override of <paramref name="aspect"/>).</summary>
    static bool? AuthorFlag(MenuProject project, ScreenDef screen, string egg, string? aspect, Func<ElementPatch, bool?> flag)
    {
        if (aspect != null && screen.Aspects.TryGetValue(aspect, out var map) && map.TryGetValue(egg, out var ov) && flag(ov) is bool o) return o;
        var def = screen.Element(egg) ?? screen.ForBase(egg);
        return def == null ? null : flag(Effective(project, def));
    }

    public CompiledLayout Compile(MenuProject project, ExeTables? exe)
    {
        var layout = new CompiledLayout { Name = project.Name, Mouse = project.Settings.Mouse, Aspects = project.Settings.Aspects.ToList() };
        if (!layout.Aspects.Contains("4:3")) layout.Aspects.Insert(0, "4:3");
        int nextCustom = FirstCustomScreenId;
        foreach (var screen in project.Screens)
        {
            if (screen.IsCustom && !Ids.IsScreenName(screen.Name))
            {
                layout.Diagnostics.Add(new Finding(Severity.Error, screen.Name, null, "INVALID_ID", $"'{screen.Name}' is not a valid custom screen name")
                    { Operation = "compile screen", Fix = "use letters and digits only (first a letter), at most 32 characters" });
                continue;
            }
            if (IsUnchanged(screen))
            {
                layout.Diagnostics.Add(new Finding(Severity.Info, screen.Name, null, "UNCHANGED", "no edits; the native page is used as is"));
                continue;
            }
            var diags = new List<Finding>();
            var values = new List<CompiledValue>();
            SceneDocument doc;
            try { doc = BuildScene(project, screen, diags, values); }
            catch (Exception ex)
            {
                layout.Diagnostics.Add(new Finding(Severity.Error, screen.Name, null, "SCREEN_BUILD_FAILED", ex.Message)
                    { Operation = "load base page " + screen.Base, Fix = "check that the base screen exists in this installation" });
                continue;
            }
            var cs = new CompiledScreen
            {
                Name = screen.Name, IsCustom = screen.IsCustom, Base = screen.Base,
                SceneName = SceneNameOf(screen),
                NativeId = screen.IsCustom ? nextCustom++ : exe?.ScreenId(screen.Base) ?? -1,
                BaseSource = _data.Source(ScenePath(screen.Base)), BaseSha256 = BaseSha(screen.Base),
                DefaultFocus = screen.DefaultFocus,
                Back = screen.Back ?? (screen.IsCustom ? new ActionBinding { Type = ActionBinding.Back } : null),
            };
            cs.Diagnostics.AddRange(diags);
            cs.Values.AddRange(values);
            foreach (var a in layout.Aspects)
            {
                try { cs.Variants[a] = Variant(project, screen, doc, a); }
                catch (Exception ex)
                {
                    cs.Diagnostics.Add(new Finding(Severity.Error, screen.Name, null, "VARIANT_FAILED", ex.Message, a) { Operation = "apply aspect overrides", Fix = "remove the failing override" });
                    cs.Variants[a] = doc.Clone();
                }
            }
            var retailIds = screen.IsCustom ? new HashSet<int>() : Base(screen.Base).Focusables.Select(e => e.ButtonId ?? 0).ToHashSet();
            foreach (var egg in doc.Focusables)
            {
                int id = egg.ButtonId ?? 0;
                var def = screen.Element(egg.Name) ?? screen.ForBase(egg.Name);
                var action = def?.Action?.Clone();
                if (action?.Type == ActionBinding.Ext && action.Extension != null) action.Extension = ActionCatalog.Canonical(action.Extension);
                BindingStatus status;
                if (action == null)
                {
                    bool retail = !screen.IsCustom && (def == null || !def.IsNew) && retailIds.Contains(id);
                    action = retail ? new ActionBinding { Type = ActionBinding.Native, Command = id } : new ActionBinding { Type = ActionBinding.None };
                    status = retail ? BindingStatus.NativeRetail : BindingStatus.Unbound;
                }
                else status = action.Type switch
                {
                    ActionBinding.Native => !screen.IsCustom && retailIds.Contains(action.Command ?? id) ? (action.Command is int c && c != id ? BindingStatus.NativeRemap : BindingStatus.NativeRetail) : BindingStatus.Unbound,
                    ActionBinding.Ext => BindingStatus.Extension,
                    ActionBinding.None => BindingStatus.Disabled,
                    _ => ActionBinding.Types.Contains(action.Type) ? BindingStatus.Runtime : BindingStatus.Unbound,
                };
                var f = egg.Focusable!;
                var visual = doc.VisualOf(egg);
                bool hidden = AuthorFlag(project, screen, visual.Name, null, p => p.Visible) == false || AuthorFlag(project, screen, egg.Name, null, p => p.Visible) == false;
                bool disabled = AuthorFlag(project, screen, egg.Name, null, p => p.Enabled) == false;
                var b = new CompiledButton
                {
                    Id = id, Egg = visual.Name, Kind = egg.Kind, Action = action, Status = status,
                    Local = hidden ? default : _layout.Hitbox(visual).Offset(-visual.X, -visual.Y),
                    Up = f.GetInt("Up Path") ?? 0, Down = f.GetInt("Down Path") ?? 0, Left = f.GetInt("Left Path") ?? 0, Right = f.GetInt("Right Path") ?? 0,
                    Enabled = f.Get("Enabled") != "False", Hidden = hidden, Blocked = hidden || disabled,
                };
                foreach (var (a, vdoc) in cs.Variants)
                {
                    if (vdoc.Find(visual.Name) is not { } ve) continue;
                    // Hidden in this variant (base delta or aspect override): no hitbox, so no invisible click area.
                    if (hidden || AuthorFlag(project, screen, visual.Name, a, p => p.Visible) == false) continue;
                    b.Hit[a] = _layout.Hitbox(ve);
                }
                cs.Buttons.Add(b);
            }
            if (screen.IsCustom) cs.Hnt = BuildHnt(doc);
            layout.Screens.Add(cs);
        }
        // navigate.screen targets of custom screens resolve to their IDs at install time (runtime table).
        return layout;
    }

    /// <summary>Texture manifest for a custom scene, same shape as the retail *.hnt files.</summary>
    public byte[] BuildHnt(SceneDocument doc)
    {
        var banks = new SortedSet<string>(StringComparer.OrdinalIgnoreCase);
        foreach (var egg in doc.Eggs)
        {
            if (egg.Model is { } m && m != "Null" && m != "dummy") banks.Add(m.Replace('/', '\\'));
            var t = egg.TextAi;
            if (t != null)
            {
                int font = (t.Name == "enUITextButtonAI" ? t.GetInt("Font ID#") : t.GetInt("Font#")) ?? 1;
                if (_layout.FontName(font) is { } fn) banks.Add(fn.Replace('/', '\\'));
            }
        }
        var sb = new StringBuilder();
        var textures = new SortedSet<string>(StringComparer.OrdinalIgnoreCase);
        foreach (var bank in banks)
        {
            var dxb = _layout.Assets.Bank(bank);
            if (dxb == null) continue;
            var dir = bank.Contains('\\') ? bank[..bank.LastIndexOf('\\')] : "";
            foreach (var img in dxb.Images) foreach (var tri in img.Triangles) textures.Add(dir + "\\" + tri.Texture);
        }
        foreach (var t in textures) sb.Append("FSTexture\t[").Append(t).Append("]\n");
        foreach (var bank in banks) sb.Append("ImageBank\t[").Append(bank.ToLowerInvariant()).Append("]\n");
        return Encoding.ASCII.GetBytes(sb.ToString());
    }
}
