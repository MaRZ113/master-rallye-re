using System.Globalization;
using System.Text;
using System.Xml;
using System.Xml.Linq;

namespace MenuBuilder.Core;

public enum ElementKind { Screen, Button, XYButton, Multistate, Slider, Arrow, Popup, Toggle, Text, Label, Image, Panel, Background, Effect, Camera, Other }

/// <summary>One AI slot of an egg (AI_List/AI No=n). Values are edited in place, unknown ones are preserved.</summary>
public sealed class AiBlock
{
    public XElement Slot { get; }
    public AiBlock(XElement slot) { Slot = slot; }
    public string Name => Slot.Elements("Value").FirstOrDefault(v => (string?)v.Attribute("Name") == "AI Name")?.Attribute("Value")?.Value ?? "Null";
    public XElement? Body => Slot.Element(Name);
    public string? Get(string name) => Body?.Elements("Value").FirstOrDefault(v => (string?)v.Attribute("Name") == name)?.Attribute("Value")?.Value;
    public int? GetInt(string name) => int.TryParse(Get(name), NumberStyles.Integer, CultureInfo.InvariantCulture, out var v) ? v : null;
    public bool Has(string name) => Get(name) != null;

    public void Set(string name, string value, string type = "Int")
    {
        var body = Body ?? throw new InvalidOperationException($"AI {Name} has no body");
        var v = body.Elements("Value").FirstOrDefault(e => (string?)e.Attribute("Name") == name);
        if (v == null) body.Add(v = new XElement("Value", new XAttribute("Name", name), new XAttribute("Type", type), new XAttribute("Value", value)));
        else v.SetAttributeValue("Value", value);
    }
    public void Set(string name, int value) => Set(name, value.ToString(CultureInfo.InvariantCulture), "Int");
}

/// <summary>Egg wrapper over the retail Scene XML (EggLists_Version4). Edits keep every other value intact.</summary>
public sealed class Egg
{
    public XElement Element { get; }
    public Egg(XElement e) { Element = e; }

    public string Name { get => (string?)Element.Attribute("Name") ?? ""; set => Element.SetAttributeValue("Name", value); }
    XElement? V(string name) => Element.Elements("Value").FirstOrDefault(v => (string?)v.Attribute("Name") == name);
    string? Val(string name) => V(name)?.Attribute("Value")?.Value;
    void SetVal(string name, string value) => V(name)?.SetAttributeValue("Value", value);

    static float F(string s) => float.Parse(s, CultureInfo.InvariantCulture);
    static string Fmt(float f) => f.ToString("0.00", CultureInfo.InvariantCulture);

    float[] Row(int i)
    {
        var m = V("en2d Matrix");
        var r = m?.Attribute("Row" + i)?.Value ?? (i == 0 ? "1 0 0 0" : i == 1 ? "0 1 0 0" : i == 2 ? "0 0 1 0" : "0 0 0 1");
        return r.Split(' ', StringSplitOptions.RemoveEmptyEntries).Select(F).ToArray();
    }
    void SetRow(int i, float[] v) => V("en2d Matrix")?.SetAttributeValue("Row" + i, string.Join(' ', v.Select(Fmt)));

    public float X { get => Row(3)[0]; set { var r = Row(3); r[0] = value; SetRow(3, r); } }
    public float Y { get => Row(3)[1]; set { var r = Row(3); r[1] = value; SetRow(3, r); } }
    public float ScaleX { get => Row(0)[0]; set { var r = Row(0); r[0] = value; SetRow(0, r); } }
    public float ScaleY { get => Row(1)[1]; set { var r = Row(1); r[1] = value; SetRow(1, r); } }
    public string Model { get => Val("en2d Model Name") ?? "Null"; set => SetVal("en2d Model Name", value); }
    public int BankIndex { get => int.Parse(Val("en2d Image Bank Index") ?? "0", CultureInfo.InvariantCulture); set => SetVal("en2d Image Bank Index", value.ToString(CultureInfo.InvariantCulture)); }
    public int DrawPriority { get => int.Parse(Val("Draw Priority") ?? "0", CultureInfo.InvariantCulture); set => SetVal("Draw Priority", value.ToString(CultureInfo.InvariantCulture)); }
    public bool Visible { get => (Val("en2d Visible") ?? "True") == "True"; set => SetVal("en2d Visible", value ? "True" : "False"); }
    public bool UsesEn2d => (Val("Use en2d") ?? "True") == "True";

    public IEnumerable<AiBlock> Ais => Element.Element("AI_List")?.Elements("AI").Select(a => new AiBlock(a)) ?? Enumerable.Empty<AiBlock>();
    public AiBlock? Ai(string name) => Ais.FirstOrDefault(a => a.Name == name);
    public IEnumerable<string> AiNames => Ais.Select(a => a.Name).Where(n => n != "Null");

    static readonly string[] ButtonAis = { "gaFrontendStandardButtonAI", "gaFrontendXYButtonAI", "gaFrontendMultistateAI",
        "enUISliderAI", "gaFrontendPopupAI", "gaFrontendEnabledButtonAI" };
    /// <summary>AI carrying the focusable "Button ID" and navigation paths.</summary>
    public AiBlock? Focusable => Ais.FirstOrDefault(a => ButtonAis.Contains(a.Name) && a.Has("Button ID"));
    public int? ButtonId => Focusable?.GetInt("Button ID");
    public AiBlock? TextAi => Ai("enUITextButtonAI") ?? Ai("enUIFormattedTextAI");

    public ElementKind Kind
    {
        get
        {
            var ai = AiNames.ToList();
            if (ai.Any(a => a.StartsWith("gaFEScreen"))) return ElementKind.Screen;
            if (ai.Contains("aiStaticCamera") || ai.Contains("aiFollowMatrix")) return ElementKind.Camera;
            if (ai.Contains("gaFrontendMultistateAI")) return ElementKind.Multistate;
            if (ai.Contains("enUISliderAI")) return ElementKind.Slider;
            if (ai.Contains("gaFrontendPopupAI")) return ElementKind.Popup;
            if (ai.Contains("gaFrontendXYButtonAI")) return ElementKind.XYButton;
            if (ai.Contains("gaFrontendEnabledButtonAI")) return ElementKind.Toggle;
            if (ai.Contains("gaFrontendStandardButtonAI")) return ElementKind.Button;
            if (ai.Contains("gaFrontendArrowAI")) return ElementKind.Arrow;
            if (ai.Contains("enUITextButtonAI")) return ElementKind.Label;
            if (ai.Contains("enUIFormattedTextAI")) return ElementKind.Text;
            if (ai.Contains("enUITileBox") || ai.Contains("enUIGradientBoxAI")) return ElementKind.Panel;
            if (ai.Contains("gaFrontendPulserAI") || ai.Contains("gaFrontendBackgroundFaderAI")) return ElementKind.Effect;
            if (Model.Contains("backgrounds", StringComparison.OrdinalIgnoreCase)) return ElementKind.Background;
            if (Model != "Null" && Model != "dummy") return ElementKind.Image;
            return ElementKind.Other;
        }
    }

    public bool IsFocusable => ButtonId is > 0;
    /// <summary>Owner of a Button ID: buttons, multistates and toggles. Carousel items (XYButton), sliders and
    /// popups share the ID of the row they belong to and are not separate focus targets.</summary>
    public bool IsPrimaryFocusable => IsFocusable && Kind is ElementKind.Button or ElementKind.Multistate or ElementKind.Toggle;
}

/// <summary>Lossless scene document (one FrontendScreens/*.xml).</summary>
public sealed class SceneDocument
{
    public XDocument Document { get; }
    public string Name { get; }

    public SceneDocument(string name, XDocument doc) { Name = name; Document = doc; }

    public static SceneDocument Load(string name, byte[] raw)
    {
        using var ms = new MemoryStream(raw);
        var doc = XDocument.Load(ms, LoadOptions.PreserveWhitespace);
        return new SceneDocument(name, doc);
    }

    public SceneDocument Clone(string? name = null) => new(name ?? Name, new XDocument(Document));

    public IEnumerable<XElement> Lists => Document.Root?.Element("EggLists_Version4")?.Elements("List") ?? Enumerable.Empty<XElement>();
    public IEnumerable<Egg> Eggs => Lists.SelectMany(l => l.Elements("Egg")).Select(e => new Egg(e));
    public Egg? Find(string name) => Eggs.FirstOrDefault(e => e.Name == name);

    public Egg? ScreenEgg => Eggs.FirstOrDefault(e => e.Kind == ElementKind.Screen);
    public string? ScreenAi => ScreenEgg?.AiNames.FirstOrDefault(a => a.StartsWith("gaFEScreen"));

    /// <summary>
    /// Focus targets: buttons/multistates/toggles, plus popups whose ButtonEgg has no button AI of its own
    /// (VehicleSetup RESET: the "Are you sure" popup carries Button ID 4 for the ResetToDefault label).
    /// </summary>
    public IEnumerable<Egg> Focusables
    {
        get
        {
            var eggs = Eggs.ToList();
            var primary = eggs.Where(e => e.IsPrimaryFocusable).ToList();
            var ids = primary.Select(e => e.ButtonId).ToHashSet();
            return eggs.Where(e => e.IsPrimaryFocusable || (e.Kind == ElementKind.Popup && e.IsFocusable && !ids.Contains(e.ButtonId)));
        }
    }

    /// <summary>Egg that is drawn and hit for a focus target (a popup's ButtonEgg, else the egg itself).</summary>
    public Egg VisualOf(Egg focusable) =>
        focusable.Ai("gaFrontendPopupAI")?.Get("ButtonEgg") is { } owner && Find(owner) is { } o ? o : focusable;

    /// <summary>Insert an egg after <paramref name="after"/> (same List) or at the end of the first list.</summary>
    public Egg Add(XElement egg, Egg? after = null)
    {
        if (after != null) after.Element.AddAfterSelf(egg);
        else (Lists.FirstOrDefault() ?? throw new InvalidDataException("scene has no egg list")).Add(egg);
        return new Egg(egg);
    }

    public string UniqueName(string stem)
    {
        var names = Eggs.Select(e => e.Name).ToHashSet(StringComparer.Ordinal);
        if (!names.Contains(stem)) return stem;
        for (int i = 2; ; i++) if (!names.Contains($"{stem}{i}")) return $"{stem}{i}";
    }

    /// <summary>
    /// Serialized exactly like the retail scene files: CRLF, two-space indent, attributes in document order,
    /// empty elements closed as "/>" and no declaration. Unmodified retail scenes round-trip byte-identical.
    /// </summary>
    public byte[] Serialize()
    {
        var sb = new StringBuilder();
        void Write(XElement e, int depth)
        {
            sb.Append(' ', depth * 2).Append('<').Append(e.Name.LocalName);
            foreach (var a in e.Attributes()) sb.Append(' ').Append(a.Name.LocalName).Append("=\"").Append(Escape(a.Value)).Append('"');
            var children = e.Elements().ToList();
            var text = string.Concat(e.Nodes().OfType<XText>().Select(t => t.Value)).Trim();
            if (children.Count == 0 && text.Length == 0) { sb.Append("/>").Append(Crlf); return; }
            if (children.Count == 0) { sb.Append('>').Append(Escape(text)).Append("</").Append(e.Name.LocalName).Append('>').Append(Crlf); return; }
            sb.Append('>').Append(Crlf);
            foreach (var c in children) Write(c, depth + 1);
            sb.Append(' ', depth * 2).Append("</").Append(e.Name.LocalName).Append('>').Append(Crlf);
        }
        Write(Document.Root!, 0);
        return Encoding.Latin1.GetBytes(sb.ToString());
    }

    const string Crlf = "\r\n";

    static string Escape(string v) => v.Replace("&", "&amp;").Replace("<", "&lt;").Replace(">", "&gt;").Replace("\"", "&quot;");
}
