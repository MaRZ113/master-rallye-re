using System.Text.Json;
using System.Text.Json.Serialization;

namespace MenuBuilder.Core;

/// <summary>
/// Typed action bound to a focusable element. Every type except "extension" is executed by the
/// native runtime itself; "extension" needs a provider registered at run time
/// (MRMenuRegisterActionV1 or a built-in provider) and is reported as unavailable otherwise.
/// </summary>
public sealed class ActionBinding
{
    public const string Native = "native", None = "none", Navigate = "navigate.screen", Back = "navigate.back", Forward = "native.forward",
        SetInt = "broker.set_int", ToggleBool = "broker.toggle_bool", CycleInt = "broker.cycle_int", Ext = "extension";
    public static readonly string[] Types = { Native, Navigate, Back, Forward, SetInt, ToggleBool, CycleInt, Ext, None };

    public string Type { get; set; } = Native;
    /// <summary>native: command delivered to the screen's own AI (defaults to the element's Button ID).</summary>
    public int? Command { get; set; }
    /// <summary>navigate.screen: retail screen name or a custom screen of this project.
    /// native.forward: retail screen that receives <see cref="Command"/> as if its own button was pressed.</summary>
    public string? Screen { get; set; }
    public string? Key { get; set; }
    public int? Value { get; set; }
    public int? Min { get; set; }
    public int? Max { get; set; }
    public int? Step { get; set; }
    /// <summary>extension: provider name, e.g. "extra_options.model_source".</summary>
    public string? Extension { get; set; }
    public string? Args { get; set; }

    public ActionBinding Clone() => (ActionBinding)MemberwiseClone();
    public override string ToString() => Type switch
    {
        Native => Command is int c ? $"native #{c}" : "native",
        Navigate => $"→ {Screen}",
        Back => "← back",
        Forward => $"→ {Screen} #{Command}",
        SetInt => $"{Key} = {Value}",
        ToggleBool => $"toggle {Key}",
        CycleInt => $"cycle {Key} {Min}..{Max}",
        Ext => $"ext {Extension}",
        _ => Type,
    };
}

/// <summary>Sparse set of element properties. Null = keep the base value.</summary>
public sealed class ElementPatch
{
    public float? X { get; set; }
    public float? Y { get; set; }
    public float? ScaleX { get; set; }
    public float? ScaleY { get; set; }
    public string? Model { get; set; }
    public int? BankIndex { get; set; }
    public int? DrawPriority { get; set; }
    public bool? Visible { get; set; }
    public int? ButtonId { get; set; }
    public int? Up { get; set; }
    public int? Down { get; set; }
    public int? Left { get; set; }
    public int? Right { get; set; }
    public bool? Enabled { get; set; }
    /// <summary>Literal label ("Text String"); clears Text ID when set.</summary>
    public string? Text { get; set; }
    public int? TextId { get; set; }
    public int? TextIndex { get; set; }
    /// <summary>Broker key that provides the text ("Text*").</summary>
    public string? TextKey { get; set; }
    public int? Font { get; set; }
    public int? TextOffsetX { get; set; }
    public int? TextOffsetY { get; set; }
    /// <summary>Button icon (enUITextButtonAI "Icon"): image Icon-1 of Frontend\Icons\ButtonIcons, 0 = none.</summary>
    public int? Icon { get; set; }
    public int? HJustify { get; set; }
    public int? VJustify { get; set; }
    /// <summary>Horizontal anchor for widescreen variants: none | left | right | center.</summary>
    public string? Anchor { get; set; }
    /// <summary>Raw value edits: "AIName/Value Name" → value. Kept for advanced users and unknown AIs.</summary>
    public Dictionary<string, string>? Raw { get; set; }

    /// <summary>Settable patch fields (excludes computed properties such as <see cref="IsEmpty"/>).</summary>
    public static readonly System.Reflection.PropertyInfo[] Fields =
        typeof(ElementPatch).GetProperties().Where(p => p.CanWrite && p.GetIndexParameters().Length == 0).ToArray();

    public ElementPatch Clone()
    {
        var c = (ElementPatch)MemberwiseClone();
        if (Raw != null) c.Raw = new Dictionary<string, string>(Raw);
        return c;
    }

    /// <summary>Overlay <paramref name="top"/> on this patch (top wins).</summary>
    public ElementPatch Merge(ElementPatch? top)
    {
        var r = Clone();
        if (top == null) return r;
        foreach (var p in Fields)
        {
            if (p.Name == nameof(Raw)) continue;
            var v = p.GetValue(top);
            if (v != null) p.SetValue(r, v);
        }
        if (top.Raw != null) { r.Raw ??= new(); foreach (var kv in top.Raw) r.Raw[kv.Key] = kv.Value; }
        return r;
    }

    [JsonIgnore]
    public bool IsEmpty => Fields.All(p => p.GetValue(this) == null);
}

public sealed class ElementDef
{
    /// <summary>Output egg name (unique in the screen).</summary>
    public string Name { get; set; } = "";
    /// <summary>Existing egg in the base screen this element edits; null for new elements.</summary>
    public string? Base { get; set; }
    /// <summary>New elements: "Egg" of the base screen, "Screen/Egg" of a retail screen or "component:Name".</summary>
    public string? Template { get; set; }
    public string? Style { get; set; }
    public bool Deleted { get; set; }
    public ElementPatch Patch { get; set; } = new();
    public ActionBinding? Action { get; set; }
    public string? Note { get; set; }

    [JsonIgnore] public bool IsNew => Base == null;
    public ElementDef Clone()
    {
        var c = (ElementDef)MemberwiseClone();
        c.Patch = Patch.Clone();
        c.Action = Action?.Clone();
        return c;
    }
}

public sealed class ComponentDef
{
    /// <summary>"Screen/Egg" of a retail screen that provides the native egg structure.</summary>
    public string Template { get; set; } = "";
    public string? Style { get; set; }
    public ElementPatch Patch { get; set; } = new();
    public string? Description { get; set; }
}

public sealed class ScreenDef
{
    public const string Retail = "retail", Custom = "custom";
    /// <summary>Retail screen name (e.g. MainMenu) or the custom screen name.</summary>
    public string Name { get; set; } = "";
    public string Kind { get; set; } = Retail;
    /// <summary>Retail screen whose scene is the starting point (custom screens: visual base).</summary>
    public string Base { get; set; } = "";
    /// <summary>SHA-256 of the base scene the delta was authored against (informational; the delta re-applies by egg name).</summary>
    public string? BaseSha256 { get; set; }
    public string? Title { get; set; }
    public int? DefaultFocus { get; set; }
    /// <summary>Custom screens: action for the native Back (-3) command. Default navigate.back.</summary>
    public ActionBinding? Back { get; set; }
    public List<ElementDef> Elements { get; set; } = new();
    /// <summary>Aspect key ("16:9") → egg name → patch applied only to that variant.</summary>
    public Dictionary<string, Dictionary<string, ElementPatch>> Aspects { get; set; } = new();

    [JsonIgnore] public bool IsCustom => Kind == Custom;
    public ElementDef? Element(string name) => Elements.FirstOrDefault(e => e.Name == name);
    public ElementDef? ForBase(string baseEgg) => Elements.FirstOrDefault(e => e.Base == baseEgg);
}

public sealed class ProjectSettings
{
    /// <summary>Hover/click selection with the mouse using the compiled hitboxes.</summary>
    public bool Mouse { get; set; } = true;
    /// <summary>Aspect variants produced by the compiler.</summary>
    public List<string> Aspects { get; set; } = new() { "4:3", "16:10", "16:9", "21:9" };
    public int Language { get; set; }
}

public sealed class MenuProject
{
    public const string FormatName = "mr-menu-project";
    public const int CurrentVersion = 1;
    public string Format { get; set; } = FormatName;
    public int Version { get; set; } = CurrentVersion;
    public string Name { get; set; } = "Untitled";
    public string? Description { get; set; }
    public string? Author { get; set; }
    public ProjectSettings Settings { get; set; } = new();
    public Dictionary<string, ElementPatch> Styles { get; set; } = new();
    public Dictionary<string, ComponentDef> Components { get; set; } = new();
    public List<ScreenDef> Screens { get; set; } = new();

    public ScreenDef? Screen(string name) => Screens.FirstOrDefault(s => string.Equals(s.Name, name, StringComparison.OrdinalIgnoreCase));

    public static readonly JsonSerializerOptions Json = new()
    {
        WriteIndented = true,
        DefaultIgnoreCondition = JsonIgnoreCondition.WhenWritingNull,
        PropertyNamingPolicy = JsonNamingPolicy.CamelCase,
        ReadCommentHandling = JsonCommentHandling.Skip,
        AllowTrailingCommas = true,
    };

    public string ToJson() => JsonSerializer.Serialize(this, Json);
    public static MenuProject FromJson(string json)
    {
        var p = JsonSerializer.Deserialize<MenuProject>(json, Json) ?? throw new InvalidDataException("empty project");
        if (p.Format != FormatName) throw new InvalidDataException($"not a {FormatName} file");
        if (p.Version > CurrentVersion) throw new InvalidDataException($"project version {p.Version} is newer than this builder ({CurrentVersion})");
        return p;
    }
    public static MenuProject Load(string path) => FromJson(File.ReadAllText(path));
    public void Save(string path) => File.WriteAllText(path, ToJson());
    public MenuProject Clone() => FromJson(ToJson());
}
