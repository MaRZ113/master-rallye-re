using System.Text.RegularExpressions;

namespace MenuBuilder.Core;

/// <summary>Who executes a typed game action at run time.</summary>
public enum ActionOwner
{
    /// <summary>The Menu Builder runtime itself (always available).</summary>
    BuiltIn,
    /// <summary>The Extra Options module of the integrated dinput8 loader; unavailable with the standalone runtime
    /// or when Extra Options is disabled in MRallyeExtraOptions.ini.</summary>
    ExtraOptions,
    /// <summary>Declared for a future module (e.g. V-CONFIG1); no runtime handler exists yet. The button is served
    /// disabled and its value shows the fallback text until a module registers the ID (MRMenuRegisterActionV1).</summary>
    Planned,
}

/// <summary>A typed action/value ID that elements can bind to. IDs are names, never addresses.</summary>
/// <param name="BrokerName">Value that already exists as a native Broker Name: the text element shows that key directly
/// (no runtime formatting, the format must be "{value}").</param>
public sealed record ActionInfo(string Id, string Title, ActionOwner Owner, bool IsAction, bool HasValue, string Description,
                                string? ValueExample = null, string? Args = null, string? LegacyId = null, string? BrokerName = null);

/// <summary>
/// Catalog of the game actions and values known to this builder version. The runtime implements the same table
/// (menu_builder_runtime.cpp, kCatalog); other modules extend it at run time through MRMenuRegisterActionV1 /
/// MRMenuRegisterValueV1 with IDs of the same form.
/// </summary>
public static class ActionCatalog
{
    public static readonly Regex IdPattern = new("^[a-z][a-z0-9_]*(\\.[a-z][a-z0-9_]*)+$", RegexOptions.CultureInvariant);

    public static readonly ActionInfo[] All =
    {
        new("vehicle.model_source", "MODEL SOURCE", ActionOwner.ExtraOptions, true, true,
            "Steps the PS2/PC/DEMO model choice of the car selected in Vehicle Select (same state as the native MODEL row).",
            "PS2", "1 = next, -1 = previous", LegacyId: "extra_options.model_source"),
        new("vehicle.tyres", "TYRES", ActionOwner.ExtraOptions, true, true,
            "Steps the tyre compound of the car selected in Vehicle Select (same state as the GENERAL page TYRE TYPE row).",
            "STANDARD", "1 = next, -1 = previous"),
        new("vehicle.build", "BUILD", ActionOwner.Planned, true, true,
            "Preparation level of the selected car (V-CONFIG1, not implemented).", "LEVEL 2"),
        new("vehicle.paint", "PAINT", ActionOwner.ExtraOptions, true, true,
            "Steps the paint of the car selected in Vehicle Select (vehicle-options.ini; unavailable when the car has fewer than two paints).",
            "RED", "1 = next, -1 = previous"),
        new("vehicle.model_label", "MODEL ROW CAPTION", ActionOwner.ExtraOptions, false, true,
            "Caption of the MODEL row of the car selected in Vehicle Select (MODEL, KIT, ...); unavailable when the car has nothing to switch.",
            "KIT"),
        new("vehicle.apply", "APPLY", ActionOwner.Planned, true, false,
            "Applies the pending vehicle configuration (V-CONFIG1, not implemented)."),
        new("game.quit", "QUIT GAME", ActionOwner.BuiltIn, true, false, "Quits the game (Broker Game/Quit)."),
    };

    static readonly Dictionary<string, ActionInfo> ById = All.SelectMany(a => a.LegacyId != null ? new[] { (a.Id, a), (a.LegacyId, a) } : new[] { (a.Id, a) })
        .ToDictionary(t => t.Item1, t => t.a, StringComparer.Ordinal);

    public static ActionInfo? Find(string? id) => id != null && ById.TryGetValue(id, out var a) ? a : null;

    /// <summary>Canonical ID (legacy names map to their current ID).</summary>
    public static string Canonical(string id) => Find(id)?.Id ?? id;

    public static bool IsValidId(string? id) => id != null && id.Length <= 63 && IdPattern.IsMatch(id);

    public static IEnumerable<ActionInfo> Actions => All.Where(a => a.IsAction);
    public static IEnumerable<ActionInfo> Values => All.Where(a => a.HasValue);
}

/// <summary>Identifier rules shared by the compiler, the validator and the editor.</summary>
public static class Ids
{
    static readonly Regex Egg = new("^[A-Za-z_][A-Za-z0-9_]*$", RegexOptions.CultureInvariant);
    static readonly Regex Screen = new("^[A-Za-z][A-Za-z0-9]*$", RegexOptions.CultureInvariant);
    static readonly Regex BrokerKey = new("^[A-Za-z][A-Za-z0-9_]*(/[A-Za-z0-9_]+)+$", RegexOptions.CultureInvariant);

    /// <summary>Names of new elements: native lookups are by name and the runtime table is tab/space separated.</summary>
    public static bool IsEggName(string? n) => n != null && n.Length is > 0 and <= 63 && Egg.IsMatch(n);
    /// <summary>Custom screen names (scene file MB_&lt;Name&gt;.xml).</summary>
    public static bool IsScreenName(string? n) => n != null && n.Length is > 0 and <= 32 && Screen.IsMatch(n);
    public static bool IsBrokerKey(string? k) => k != null && k.Length <= 127 && BrokerKey.IsMatch(k);
}
