using System.Globalization;

namespace MenuBuilder.Core;

/// <summary>D3D8 renderer interface modes (MRRRenderer.ini [Quality] Widescreen / Widescreen.InterfaceMode).</summary>
public enum InterfaceMode { Stock = 0, Centered4x3 = 1, PreserveMargins = 2 }

public readonly record struct Aspect(string Key, double Ratio)
{
    public static readonly Aspect[] Standard =
    {
        new("4:3", 4.0 / 3.0), new("16:10", 16.0 / 10.0), new("16:9", 16.0 / 9.0), new("21:9", 64.0 / 27.0),
    };

    public static Aspect Parse(string key)
    {
        foreach (var a in Standard) if (a.Key == key) return a;
        var p = key.Split(':', 'x', 'X');
        if (p.Length == 2 && double.TryParse(p[0], NumberStyles.Float, CultureInfo.InvariantCulture, out var w) &&
            double.TryParse(p[1], NumberStyles.Float, CultureInfo.InvariantCulture, out var h) && w > 0 && h > 0)
            return new Aspect(key, w / h);
        throw new FormatException($"bad aspect '{key}'");
    }

    public static Aspect FromSize(int width, int height) => new($"{width}x{height}", (double)width / height);

    /// <summary>Variant chosen for a window: nearest ratio among the compiled keys (same rule as the native runtime).</summary>
    public static string Nearest(IEnumerable<string> keys, double ratio) =>
        keys.OrderBy(k => Math.Abs(Parse(k).Ratio - ratio)).First();

    public string FileKey => Key.Replace(':', 'x');
}

/// <summary>
/// Model of the renderer's 2D interface projection (R-GFX5 widescreen-integration.md):
/// Stock stretches 640x480 to the window; Centered4x3 widens the ortho canvas to 480*aspect with the
/// authored 640x480 centred (half = (480*aspect-640)/2 extra units per side); PreserveMargins additionally
/// shifts packets whose authored point matches one of the 51 reference rules by ±half, and left text bands by -half.
/// </summary>
public static class WidescreenModel
{
    public static double Half(double ratio) => Math.Max(0, (480.0 * ratio - 640.0) / 2.0);

    /// <summary>Reference rules (margin-rules.json, CONFIRMED_BY_REFERENCE_EXE, source bcf310a7…). Coordinates: authored UI, y up.</summary>
    public static readonly (float X, float Y, int Dir)[] PointRules =
    {
        (15,150,-1),(15,390,-1),(20,135,-1),(20,150,-1),(20,175,-1),(20,350,-1),(20,360,-1),(20,365,-1),(20,375,-1),(20,380,-1),
        (20,410,-1),(20,415,-1),(23,370,-1),(440,390,1),(450,160,1),(450,400,1),(475,390,1),(485,160,1),(485,400,1),(490,210,1),
        (490,440,1),(490,450,1),(510,390,1),(520,160,1),(520,400,1),(540,408,1),(540,423,1),(545,40,1),(545,280,1),(545,390,1),
        (550,179,1),(550,194,1),(550,419,1),(550,434,1),(555,160,1),(555,400,1),(565,75,1),(565,315,1),(570,22,1),(570,262,1),
        (580,390,1),(590,160,1),(590,400,1),(601,52,1),(601,292,1),(610,408,1),(610,423,1),(620,179,1),(620,194,1),(620,419,1),
        (620,434,1),
    };
    public const int LeftBandMinX = 25, LeftBandMaxX = 106;
    public static readonly (int Min, int Max)[] LeftBandY = { (19, 100), (259, 340) };

    /// <summary>
    /// PreserveMargins direction of an egg whose en2d packet point (+0x54, the egg translation) is (x,y):
    /// renderer ui_margins.cpp margin_direction — exact reference points first, then the left band
    /// x∈[25,106], y∈[19,100)∪[259,340) for every packet (sprites and labels alike). Vehicle Select
    /// carousel cards on the row y=309 keep their source coordinates.
    /// </summary>
    public static int MarginDirection(float x, float y, bool carouselCard = false)
    {
        if (carouselCard && Math.Abs(y - 309f) <= 1f / 4096f) return 0;
        foreach (var r in PointRules) if (r.X == x && r.Y == y) return r.Dir;
        if (x >= LeftBandMinX && x <= LeftBandMaxX)
            foreach (var (min, max) in LeftBandY) if (y >= min && y < max) return -1;
        return 0;
    }

    /// <summary>Horizontal offset applied by the renderer to an egg (authored units).</summary>
    public static double RendererShift(InterfaceMode mode, double ratio, float x, float y, bool carouselCard = false) =>
        mode == InterfaceMode.PreserveMargins ? MarginDirection(x, y, carouselCard) * Half(ratio) : 0;

    /// <summary>Visible authored-x range in the window.</summary>
    public static (double Left, double Right) VisibleRange(InterfaceMode mode, double ratio) =>
        mode == InterfaceMode.Stock ? (0, 640) : (-Half(ratio), 640 + Half(ratio));

    /// <summary>Anchor shift used when compiling an aspect variant (applies only when the renderer widens the canvas).</summary>
    public static double AnchorShift(string? anchor, double ratio) => anchor switch
    {
        "left" => -Half(ratio),
        "right" => Half(ratio),
        _ => 0,
    };
}
