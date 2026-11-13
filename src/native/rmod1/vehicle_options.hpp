#pragma once
// Per-family Vehicle Select options (docs/vehicle-manager/VEHICLE_OPTIONS_DESIGN.md, revision 2).
//
// MRMods/Vehicles/active/vehicle-options.ini is written by the Vehicle Manager:
//
//   [Family:CalminiFrontier]          registry folder of the family (as the native registry row +0x24 stores it)
//   model_label = KIT                 caption of the MODEL row
//   model = BARE,STOCK,FULL           choices; empty = no model choice (row hidden); key absent = retail PS2/PC(/DEMO)
//   model_folders = CalminiFrontier_bare,CalminiFrontier,CalminiFrontier_full
//   model_default = 1
//   paint = GREY,SILVER,SAND          paint 0 is the family's own textures; fewer than two = no PAINT row
//   paint_default = 0
//
// A kit is a resource folder; paint n >= 1 of a kit is the virtual folder name "<kit>__p<n>". No such directory
// exists: the roster file overlay resolves DataGx/Vehicles/<kit>__p<n>/<file> to
// DataGx/VehiclePaints/<family>/<n>/<file>, then to DataGx/Vehicles/<kit>/<file> (both inside the overlay).
//
// Pure code (std only): shared by the loader (DllMain, file overlay), Extra Options and the tests.
#include <cctype>
#include <cstdlib>
#include <string>
#include <vector>

namespace vehicle_options {

inline constexpr size_t kMaxChoices = 8, kMaxPaints = 32, kMaxFamilies = 512, kMaxFolder = 45, kMaxLabel = 15;

struct Family {
    std::string name;                      // family folder
    bool model_declared = false;           // "model" key present (replaces PS2/PC/DEMO)
    std::string model_label = "MODEL";
    std::vector<std::string> model, folders;
    unsigned model_default = 0;
    std::vector<std::string> paints;
    unsigned paint_default = 0;
};

inline bool same(const std::string& a, const std::string& b) {
    if (a.size() != b.size()) return false;
    for (size_t i = 0; i < a.size(); ++i)
        if (std::tolower(static_cast<unsigned char>(a[i])) != std::tolower(static_cast<unsigned char>(b[i]))) return false;
    return true;
}
inline std::string lower(std::string s) { for (auto& c : s) c = char(std::tolower(static_cast<unsigned char>(c))); return s; }

// Folder names: [A-Za-z0-9_]{1,45} and never containing the virtual separator "__p".
inline bool valid_folder(const std::string& s) {
    if (s.empty() || s.size() > kMaxFolder || lower(s).find("__p") != std::string::npos) return false;
    for (char c : s) if (!(std::isalnum(static_cast<unsigned char>(c)) || c == '_')) return false;
    return true;
}
// Labels are shown in the native upper-case font.
inline bool valid_label(const std::string& s) {
    if (s.empty() || s.size() > kMaxLabel) return false;
    for (char c : s) if (!(std::isupper(static_cast<unsigned char>(c)) || std::isdigit(static_cast<unsigned char>(c)) || c == ' ' || c == '-' || c == '.')) return false;
    return true;
}

inline std::string virtual_name(const std::string& kit, unsigned paint) {
    return paint ? kit + "__p" + std::to_string(paint) : kit;
}
// "<kit>__p<n>" with n in 1..kMaxPaints-1 -> kit, n. Anything else -> false.
inline bool split_virtual(const std::string& name, std::string& kit, unsigned& paint) {
    const auto lo = lower(name);
    const auto at = lo.rfind("__p");
    if (at == std::string::npos || at == 0 || at + 3 >= name.size() || name.size() - at - 3 > 2) return false;
    unsigned n = 0;
    for (size_t i = at + 3; i < name.size(); ++i) {
        if (!std::isdigit(static_cast<unsigned char>(name[i]))) return false;
        n = n * 10 + unsigned(name[i] - '0');
    }
    if (n == 0 || n >= kMaxPaints || name[at + 3] == '0') return false;
    kit = name.substr(0, at); paint = n;
    return valid_folder(kit);
}

struct Table {
    std::vector<Family> families;
    const Family* find(const std::string& family) const {
        for (auto& f : families) if (same(f.name, family)) return &f;
        return nullptr;
    }
    // Family whose own folder or one of whose kit folders is `folder`.
    const Family* owner(const std::string& folder) const {
        for (auto& f : families) {
            if (same(f.name, folder)) return &f;
            for (auto& k : f.folders) if (same(k, folder)) return &f;
        }
        return nullptr;
    }
    // Family folder for any name the game may hold: the family, a kit folder or a virtual "<kit>__p<n>".
    std::string family_of(const std::string& name) const {
        std::string kit = name; unsigned paint = 0;
        if (split_virtual(name, kit, paint)) {
            const Family* f = owner(kit);
            return f && paint < f->paints.size() ? f->name : std::string();
        }
        const Family* f = owner(name);
        return f ? f->name : std::string();
    }
    // Overlay keys (lower case, forward slashes) that may serve a game-relative key of a virtual folder, in order.
    bool candidates(const std::string& key, std::vector<std::string>& out) const {
        out.clear();
        static const std::string root = "datagx/vehicles/";
        const auto k = lower(key);
        if (k.compare(0, root.size(), root) != 0) return false;
        const auto slash = k.find('/', root.size());
        if (slash == std::string::npos || slash + 1 >= k.size()) return false;
        std::string kit; unsigned paint = 0;
        if (!split_virtual(key.substr(root.size(), slash - root.size()), kit, paint)) return false;
        const Family* f = owner(kit);
        if (!f || paint >= f->paints.size()) return false;
        const auto rest = k.substr(slash + 1);
        out.push_back("datagx/vehiclepaints/" + lower(f->name) + "/" + std::to_string(paint) + "/" + rest);
        out.push_back(root + lower(kit) + "/" + rest);
        return true;
    }
};

inline std::string trim(const std::string& s) {
    size_t a = 0, b = s.size();
    while (a < b && std::isspace(static_cast<unsigned char>(s[a]))) ++a;
    while (b > a && std::isspace(static_cast<unsigned char>(s[b - 1]))) --b;
    return s.substr(a, b - a);
}
inline std::vector<std::string> list(const std::string& s) {
    std::vector<std::string> out;
    if (trim(s).empty()) return out;
    size_t at = 0;
    while (true) {
        const auto comma = s.find(',', at);
        out.push_back(trim(s.substr(at, comma == std::string::npos ? std::string::npos : comma - at)));
        if (comma == std::string::npos) break;
        at = comma + 1;
    }
    return out;
}
inline bool number(const std::string& s, unsigned& out) {
    if (s.empty() || s.size() > 3) return false;
    for (char c : s) if (!std::isdigit(static_cast<unsigned char>(c))) return false;
    out = unsigned(std::atoi(s.c_str()));
    return true;
}

// Whole-file validation: any error rejects the file (the caller keeps retail behaviour) and names the line.
inline bool parse(const std::string& text, Table& out, std::string& error) {
    Table t; Family* cur = nullptr; size_t line_no = 0, at = 0;
    auto fail = [&](const char* what) { error = "line " + std::to_string(line_no) + ": " + what; return false; };
    while (at <= text.size()) {
        auto end = text.find('\n', at); if (end == std::string::npos) end = text.size();
        std::string line = text.substr(at, end - at); at = end + 1; ++line_no;
        if (const auto c = line.find_first_of(";#"); c != std::string::npos) line.erase(c);
        line = trim(line);
        if (line.empty()) { if (end == text.size()) break; continue; }
        if (line.front() == '[') {
            if (line.back() != ']' || line.compare(0, 8, "[Family:") != 0) return fail("section must be [Family:<folder>]");
            Family f; f.name = trim(line.substr(8, line.size() - 9));
            if (!valid_folder(f.name)) return fail("invalid family folder");
            if (t.find(f.name)) return fail("duplicate family");
            if (t.families.size() >= kMaxFamilies) return fail("too many families");
            t.families.push_back(f); cur = &t.families.back();
        } else {
            const auto eq = line.find('=');
            if (eq == std::string::npos || !cur) return fail("key outside a family section");
            const auto k = lower(trim(line.substr(0, eq))), v = trim(line.substr(eq + 1));
            if (k == "model_label") { if (!valid_label(v)) return fail("invalid model_label"); cur->model_label = v; }
            else if (k == "model") { cur->model_declared = true; cur->model = list(v); }
            else if (k == "model_folders") cur->folders = list(v);
            else if (k == "model_default") { if (!number(v, cur->model_default)) return fail("invalid model_default"); }
            else if (k == "paint") cur->paints = list(v);
            else if (k == "paint_default") { if (!number(v, cur->paint_default)) return fail("invalid paint_default"); }
            else if (k == "paint_rgb") {}   // informational (names derived by the Vehicle Manager)
            else return fail("unknown key");
        }
        if (end == text.size()) break;
    }
    for (auto& f : t.families) {
        line_no = 0;
        auto bad = [&](const std::string& what) { error = "[Family:" + f.name + "] " + what; return false; };
        if (f.model.size() > kMaxChoices) return bad("too many model choices");
        for (auto& m : f.model) if (!valid_label(m)) return bad("invalid model choice label");
        if (f.model.size() >= 2 && f.folders.size() != f.model.size()) return bad("model_folders must list one folder per choice");
        if (f.model.size() < 2 && !f.folders.empty()) return bad("model_folders without choices");
        for (auto& k : f.folders) if (!valid_folder(k)) return bad("invalid kit folder");
        if (f.model_default >= (f.model.size() < 2 ? 1u : unsigned(f.model.size()))) return bad("model_default out of range");
        if (f.paints.size() > kMaxPaints) return bad("too many paints");
        for (auto& p : f.paints) if (!valid_label(p)) return bad("invalid paint label");
        if (f.paint_default >= (f.paints.empty() ? 1u : unsigned(f.paints.size()))) return bad("paint_default out of range");
    }
    // A kit folder belongs to exactly one family (the renderer maps it back by name).
    for (size_t i = 0; i < t.families.size(); ++i)
        for (auto& k : t.families[i].folders)
            for (size_t j = 0; j < t.families.size(); ++j)
                if (j != i && (same(t.families[j].name, k) || [&] { for (auto& o : t.families[j].folders) if (same(o, k)) return true; return false; }()))
                    { error = "kit folder " + k + " is shared by two families"; return false; }
    out = std::move(t);
    return true;
}

} // namespace vehicle_options
