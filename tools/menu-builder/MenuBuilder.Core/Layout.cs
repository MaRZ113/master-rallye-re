namespace MenuBuilder.Core;

/// <summary>Axis-aligned rectangle in authored UI units (x right, y up, 640x480 reference).</summary>
public readonly record struct UiRect(double X0, double Y0, double X1, double Y1)
{
    public double Width => X1 - X0;
    public double Height => Y1 - Y0;
    public bool IsEmpty => Width <= 0 || Height <= 0;
    public bool Contains(double x, double y) => x >= X0 && x < X1 && y >= Y0 && y < Y1;
    public UiRect Offset(double dx, double dy) => new(X0 + dx, Y0 + dy, X1 + dx, Y1 + dy);
    public UiRect Union(UiRect o) => IsEmpty ? o : o.IsEmpty ? this : new(Math.Min(X0, o.X0), Math.Min(Y0, o.Y0), Math.Max(X1, o.X1), Math.Max(Y1, o.Y1));
    public bool Intersects(UiRect o) => X0 < o.X1 && o.X0 < X1 && Y0 < o.Y1 && o.Y0 < Y1;
    public override string ToString() => $"[{X0:0.#},{Y0:0.#} – {X1:0.#},{Y1:0.#}]";
}

public sealed class TextRun
{
    public string Text = "";
    public string? FontName;
    public DxbBank? Font;
    public int Width, Height;
    /// <summary>Top-left of the text block in egg-local DXB coordinates (y down).</summary>
    public double LocalX, LocalY;
    public bool Dynamic;
}

/// <summary>
/// Native layout rules shared by preview, hitbox compiler and validator so appearance and hitbox
/// cannot diverge: both come from the same DXB image geometry and egg matrix.
/// </summary>
public sealed class LayoutEngine
{
    public AssetCache Assets { get; }
    public ExeTables? Exe { get; }
    public int Language { get; set; }
    /// <summary>Values for Broker-driven text ("Text*") in previews.</summary>
    public Dictionary<string, string> PreviewValues { get; } = new(StringComparer.OrdinalIgnoreCase);

    public LayoutEngine(AssetCache assets, ExeTables? exe) { Assets = assets; Exe = exe; }

    // Eggs whose visibility the native screen AI drives at run time (closed popups, MainMenu "ARE YOU SURE?").
    static readonly HashSet<string> NativeHiddenNames = new(StringComparer.Ordinal) { "SureText" };

    /// <summary>True when the egg is hidden in game until a native state shows it (preview hides it by default).</summary>
    public static bool NativeHidden(SceneDocument doc, Egg egg)
    {
        if (NativeHiddenNames.Contains(egg.Name)) return true;
        if (egg.Ai("gaFrontendPopupAI") != null) return true;
        return doc.Eggs.Any(e => e.Ai("gaFrontendPopupAI")?.Get("Tiles") == egg.Name);
    }

    public const string IconBank = "frontend/icons/buttonicons";

    public DxbImage? Image(Egg egg, int? state = null)
    {
        if (!egg.UsesEn2d) return null;
        var bank = Assets.Bank(egg.Model);
        if (bank == null) return null;
        // StandardButton + TextButton select the bank image by state (0x45C420 → 0x525630):
        // 0 normal, 1 focused, 2 disabled, 3 disabled + focused.
        if (state is int st && egg.Ai("gaFrontendStandardButtonAI") != null && egg.TextAi?.Name == "enUITextButtonAI" && bank.Images.Count >= 4)
            return bank.ImageFor(st);
        return bank.ImageFor(egg.BankIndex);
    }

    /// <summary>Native visual state of a button egg for a given focus.</summary>
    public static int State(Egg egg, int? focusedId)
    {
        var f = egg.Focusable;
        if (f == null) return 0;
        bool focused = focusedId != null && egg.ButtonId == focusedId;
        bool enabled = f.Get("Enabled") != "False";
        return enabled ? (focused ? 1 : 0) : (focused ? 3 : 2);
    }

    /// <summary>Button icon image (TextButton "Icon" N → ButtonIcons image N-1, drawn at local (4, 5)).</summary>
    public DxbImage? Icon(Egg egg)
    {
        var t = egg.TextAi;
        if (t?.Name != "enUITextButtonAI" || t.GetInt("Icon") is not int icon || icon <= 0) return null;
        return Assets.Bank(IconBank)?.ImageFor(icon - 1);
    }

    /// <summary>Sprite bounds: screen_y = egg_y - scale*local_y (DXB local y grows downward).</summary>
    public UiRect SpriteRect(Egg egg)
    {
        var img = Image(egg);
        if (img == null || img.Triangles.Count == 0) return default;
        double sx = egg.ScaleX, sy = egg.ScaleY;
        double x0 = egg.X + sx * img.MinX, x1 = egg.X + sx * img.MaxX;
        double ya = egg.Y - sy * img.MaxY, yb = egg.Y - sy * img.MinY;
        return new UiRect(Math.Min(x0, x1), Math.Min(ya, yb), Math.Max(x0, x1), Math.Max(ya, yb));
    }

    public string? FontName(int id) => Exe != null && Exe.Fonts.TryGetValue(id, out var n) ? n : id switch
    {
        1 => "fonts/Arial/Arial_12", 2 => "fonts/Arial/Arial_16", 3 => "fonts/Arial/Arial_24", _ => null,
    };

    public static int Justify(int mode, int size, int box) => mode switch { 1 => box / 2 - size / 2, 2 => box - size, _ => 0 };

    /// <summary>Text resolution like 0x524EB0: Text* (Broker) wins, then Text ID/Index (gaLocal), then Text String.</summary>
    public (string text, bool dynamic) ResolveText(AiBlock ai)
    {
        var key = ai.Get("Text*");
        if (!string.IsNullOrEmpty(key) && key != "Null")
            return (PreviewValues.TryGetValue(key, out var v) ? v : "{" + key.Split('/').Last() + "}", true);
        int id = ai.GetInt("Text ID#") ?? 0, index = ai.GetInt("Text ID Index#") ?? 0;
        if (id != 0) return (Exe?.Text(id, index, Language) ?? $"#{id}.{index}", false);
        var s = ai.Get("Text String");
        return (s == null || s == "Null" ? "" : s, false);
    }

    public (int w, int h) Measure(DxbBank font, string text)
    {
        int w = 0, h = 0;
        foreach (var c in text) { var g = font.Glyph(c) ?? font.Glyph(char.ToUpperInvariant(c)); if (g != null) w += g.Width; }
        foreach (var c in "ABCDEFGHIJKLMNOPQRSTUVWXYZ") { var g = font.Glyph(c); if (g != null) h = Math.Max(h, g.Height); }
        return (w, h);
    }

    /// <summary>Text block of a label/text egg. TextButton justifies inside the egg image box (0x525440/0x52EB20).</summary>
    public TextRun? Text(Egg egg)
    {
        var ai = egg.TextAi;
        if (ai == null) return null;
        var (text, dynamic) = ResolveText(ai);
        bool button = ai.Name == "enUITextButtonAI";
        int fontId = (button ? ai.GetInt("Font ID#") : ai.GetInt("Font#")) ?? 1;
        var fontName = FontName(fontId);
        var font = Assets.Bank(fontName);
        if (button) text = text.ToUpperInvariant();
        var run = new TextRun { Text = text, FontName = fontName, Font = font, Dynamic = dynamic };
        if (font == null) return run;
        (run.Width, run.Height) = Measure(font, text);
        if (button)
        {
            var img = Image(egg);
            int boxW = img?.Width ?? 0, boxH = img?.Height ?? 0;
            int hj = ai.GetInt("HJustification") ?? 0, vj = ai.GetInt("VJustification") ?? 0;
            run.LocalX = (img?.MinX ?? 0) + (ai.GetInt("Text OffsetX") ?? 0) + Justify(hj, run.Width, boxW);
            run.LocalY = (img?.MinY ?? 0) + (ai.GetInt("Text OffsetY") ?? 0) + Justify(vj, run.Height, boxH);
        }
        else
        {
            var off = (ai.Get("Offset") ?? "0 0 0").Split(' ', StringSplitOptions.RemoveEmptyEntries)
                .Select(s => double.Parse(s, System.Globalization.CultureInfo.InvariantCulture)).ToArray();
            int hj = ai.GetInt("Horizontal Justification") ?? 0, vj = ai.GetInt("Vertical Justification") ?? 0;
            // Formatted text justifies around its anchor: 1 = centred, 2 = right/bottom aligned on the anchor.
            run.LocalX = off[0] - (hj == 1 ? run.Width / 2.0 : hj == 2 ? run.Width : 0);
            run.LocalY = -off[1] - run.Height - (vj == 1 ? -run.Height / 2.0 : vj == 2 ? -run.Height : 0);
        }
        return run;
    }

    /// <summary>Text block in authored units; the egg matrix scales text like sprites (in-game verified).</summary>
    public UiRect TextRect(Egg egg, TextRun run) =>
        new(egg.X + egg.ScaleX * run.LocalX, egg.Y - egg.ScaleY * (run.LocalY + run.Height),
            egg.X + egg.ScaleX * (run.LocalX + run.Width), egg.Y - egg.ScaleY * run.LocalY);

    /// <summary>Visual bounds (sprite ∪ text) used for selection in the editor.</summary>
    public UiRect Bounds(Egg egg)
    {
        var r = SpriteRect(egg);
        var t = Text(egg);
        if (t != null && t.Width > 0) r = r.Union(TextRect(egg, t));
        if (r.IsEmpty) r = new UiRect(egg.X - 4, egg.Y - 4, egg.X + 4, egg.Y + 4);
        return r;
    }

    /// <summary>Native hitbox of a focusable egg: its sprite image box, else its text box.</summary>
    public UiRect Hitbox(Egg egg)
    {
        var r = SpriteRect(egg);
        if (!r.IsEmpty) return r;
        var t = Text(egg);
        return t != null && t.Width > 0 ? TextRect(egg, t) : default;
    }
}
