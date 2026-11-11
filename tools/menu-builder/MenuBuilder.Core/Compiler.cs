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
    public bool Enabled = true;
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
    public List<string> Notes { get; } = new();
}

public sealed class CompiledLayout
{
    public string Name { get; init; } = "";
    public bool Mouse { get; init; }
    public List<string> Aspects { get; init; } = new();
    public List<CompiledScreen> Screens { get; } = new();
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

    /// <summary>Applies a screen definition to its base and returns the 4:3 document (no aspect shifts).</summary>
    public SceneDocument BuildScene(MenuProject project, ScreenDef screen, List<string>? notes = null)
    {
        notes ??= new();
        var doc = Base(screen.Base).Clone(screen.IsCustom ? "MB_" + screen.Name : screen.Base);
        if (screen.IsCustom) EnsureHost(doc, notes);
        foreach (var el in screen.Elements)
        {
            try { ApplyElement(project, screen, doc, el); }
            catch (Exception ex) { notes.Add($"{el.Name}: {ex.Message}"); }
        }
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

    void EnsureHost(SceneDocument doc, List<string> notes)
    {
        var screenEgg = doc.ScreenEgg;
        if (screenEgg != null && doc.ScreenAi == HostAi) return;
        var host = Base(HostScreen).ScreenEgg ?? throw new InvalidDataException("host screen egg missing");
        var copy = new XElement(host.Element);
        if (screenEgg != null) { screenEgg.Element.ReplaceWith(copy); notes.Add($"screen AI {doc.ScreenAi ?? "?"} replaced by host {HostAi}"); }
        else doc.Add(copy);
    }

    XElement ResolveTemplate(MenuProject project, ScreenDef screen, SceneDocument doc, string template, out ElementPatch componentPatch)
    {
        componentPatch = new ElementPatch();
        if (template.StartsWith("component:", StringComparison.Ordinal))
        {
            var name = template["component:".Length..];
            if (!project.Components.TryGetValue(name, out var comp)) throw new InvalidDataException($"component {name} missing");
            var style = comp.Style != null && project.Styles.TryGetValue(comp.Style, out var s) ? s : null;
            componentPatch = (style ?? new ElementPatch()).Merge(comp.Patch);
            template = comp.Template;
        }
        var slash = template.IndexOf('/');
        Egg? src = slash < 0 ? doc.Find(template) ?? Base(screen.Base).Find(template)
                             : Base(template[..slash]).Find(template[(slash + 1)..]);
        return new XElement((src ?? throw new InvalidDataException($"template egg {template} missing")).Element);
    }

    void ApplyElement(MenuProject project, ScreenDef screen, SceneDocument doc, ElementDef el)
    {
        var style = el.Style != null && project.Styles.TryGetValue(el.Style, out var s) ? s : null;
        if (!el.IsNew)
        {
            var egg = doc.Find(el.Base!) ?? throw new InvalidDataException($"base egg {el.Base} not in {screen.Base}");
            if (el.Deleted) { egg.Element.Remove(); return; }
            if (el.Name != el.Base && !string.IsNullOrEmpty(el.Name)) egg.Name = el.Name;
            ApplyPatch(egg, (style ?? new ElementPatch()).Merge(el.Patch));
            return;
        }
        if (el.Deleted) return;
        var x = ResolveTemplate(project, screen, doc, el.Template ?? throw new InvalidDataException("new element without template"), out var comp);
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
                if (slash < 0) continue;
                var ai = egg.Ai(k[..slash]) ?? throw new InvalidDataException($"{egg.Name}: AI {k[..slash]} missing for raw edit");
                var type = ai.Body?.Elements("Value").FirstOrDefault(e => (string?)e.Attribute("Name") == k[(slash + 1)..])?.Attribute("Type")?.Value ?? "String";
                ai.Set(k[(slash + 1)..], v, type);
            }
    }

    /// <summary>Merged style+patch for an element (used for anchors).</summary>
    static ElementPatch Effective(MenuProject project, ElementDef el)
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

    public CompiledLayout Compile(MenuProject project, ExeTables? exe)
    {
        var layout = new CompiledLayout { Name = project.Name, Mouse = project.Settings.Mouse, Aspects = project.Settings.Aspects.ToList() };
        if (!layout.Aspects.Contains("4:3")) layout.Aspects.Insert(0, "4:3");
        int nextCustom = FirstCustomScreenId;
        foreach (var screen in project.Screens)
        {
            var notes = new List<string>();
            var doc = BuildScene(project, screen, notes);
            var cs = new CompiledScreen
            {
                Name = screen.Name, IsCustom = screen.IsCustom, Base = screen.Base,
                SceneName = screen.IsCustom ? "MB_" + screen.Name : screen.Base,
                NativeId = screen.IsCustom ? nextCustom++ : exe?.ScreenId(screen.Base) ?? -1,
                BaseSource = _data.Source(ScenePath(screen.Base)), BaseSha256 = BaseSha(screen.Base),
                DefaultFocus = screen.DefaultFocus,
                Back = screen.Back ?? (screen.IsCustom ? new ActionBinding { Type = ActionBinding.Back } : null),
            };
            cs.Notes.AddRange(notes);
            foreach (var a in layout.Aspects) cs.Variants[a] = Variant(project, screen, doc, a);
            var retailIds = screen.IsCustom ? new HashSet<int>() : Base(screen.Base).Focusables.Select(e => e.ButtonId ?? 0).ToHashSet();
            foreach (var egg in doc.Focusables)
            {
                int id = egg.ButtonId ?? 0;
                var def = screen.Element(egg.Name) ?? screen.ForBase(egg.Name);
                var action = def?.Action?.Clone();
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
                    _ => BindingStatus.Runtime,
                };
                var f = egg.Focusable!;
                var visual = doc.VisualOf(egg);
                var b = new CompiledButton
                {
                    Id = id, Egg = visual.Name, Kind = egg.Kind, Action = action, Status = status,
                    Local = _layout.Hitbox(visual).Offset(-visual.X, -visual.Y),
                    Up = f.GetInt("Up Path") ?? 0, Down = f.GetInt("Down Path") ?? 0, Left = f.GetInt("Left Path") ?? 0, Right = f.GetInt("Right Path") ?? 0,
                    Enabled = f.Get("Enabled") != "False",
                };
                foreach (var (a, vdoc) in cs.Variants)
                    if (vdoc.Find(visual.Name) is { } ve) b.Hit[a] = _layout.Hitbox(ve);
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
