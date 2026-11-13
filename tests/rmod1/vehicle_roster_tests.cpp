// Offline checks of the VehicleRoster save guard (retail class table, no game process).
#include "../../src/native/rmod1/vehicle_roster.hpp"
#include <cstdio>
#include <fstream>
#include <sstream>

static int failures = 0;
#define CHECK(x) do { if (!(x)) { std::printf("FAIL %d: %s\n", __LINE__, #x); ++failures; } } while (0)

int main(int argc, char** argv) {
    if (argc < 2) return 2;
    auto& s = vehicle_roster::state();
    std::snprintf(s.game_dir, sizeof(s.game_dir), "%s\\", argv[1]);
    SetEnvironmentVariableA("MR_VEHICLE_REGISTRY_DESCRIPTOR", nullptr);
    vehicle_roster::load_classes();
    CHECK(s.id_class.size() == 25 && s.id_class[0] == 0 && s.id_class[13] == 1 && s.id_class[24] == 2);
    using vehicle_roster::car_key_scope;
    CHECK(car_key_scope("RallyeCup/PlayerT2Car0") == 1);
    CHECK(car_key_scope("MasterRallye/PlayerT3Car1") == 2);
    CHECK(car_key_scope("Frontend/QuickRace/Car0") == 4);
    CHECK(car_key_scope("Frontend/QuickRace/CarClass") == -1);
    CHECK(car_key_scope("MasterRallye/Car5/CarID") == 4);
    CHECK(car_key_scope("MasterRallye/Car5/CarClass") == -1);
    CHECK(car_key_scope("Settings/SpeedUnits") == -1);
    const std::string save = std::string(argv[1]) + "\\PlayerState.xml";
    {
        std::ofstream f(save, std::ios::binary);
        f << "<Game>\r\n"
             "<Value Name=\"Frontend/QuickRace/Car0\" Type=\"Int\" Value=\"30\" SaveOptions=\"False\" SavePlayerState=\"True\"/>\r\n"
             "<Value Name=\"Frontend/QuickRace/Car1\" Type=\"Int\" Value=\"3\" SaveOptions=\"False\" SavePlayerState=\"True\"/>\r\n"
             "<Value Name=\"RallyeCup/PlayerT2Car0\" Type=\"Int\" Value=\"2\" SaveOptions=\"False\" SavePlayerState=\"True\"/>\r\n"
             "<Value Name=\"MasterRallye/PlayerT3Car0\" Type=\"Int\" Value=\"19\" SaveOptions=\"False\" SavePlayerState=\"True\"/>\r\n"
             "<Value Name=\"Settings/SpeedUnits\" Type=\"Int\" Value=\"30\" SaveOptions=\"False\" SavePlayerState=\"True\"/>\r\n"
             "</Game>\r\n";
    }
    char out[MAX_PATH * 2]{};
    CHECK(vehicle_roster::sanitize_save(save.c_str(), out, sizeof(out)));
    std::ifstream in(out, std::ios::binary);
    std::stringstream text; text << in.rdbuf();
    const auto t = text.str();
    CHECK(t.find("Frontend/QuickRace/Car0\" Type=\"Int\" Value=\"0\"") != std::string::npos);    // not offered -> ID0
    CHECK(t.find("Frontend/QuickRace/Car1\" Type=\"Int\" Value=\"3\"") != std::string::npos);    // valid, kept
    CHECK(t.find("RallyeCup/PlayerT2Car0\" Type=\"Int\" Value=\"7\"") != std::string::npos);     // T1 car in T2 key -> first T2
    CHECK(t.find("MasterRallye/PlayerT3Car0\" Type=\"Int\" Value=\"19\"") != std::string::npos); // valid T3, kept
    CHECK(t.find("Settings/SpeedUnits\" Type=\"Int\" Value=\"30\"") != std::string::npos);      // not a car key
    // A clean save is served as is.
    { std::ofstream f(save, std::ios::binary); f << "<Value Name=\"Frontend/QuickRace/Car0\" Type=\"Int\" Value=\"5\"/>\r\n"; }
    CHECK(!vehicle_roster::sanitize_save(save.c_str(), out, sizeof(out)));
    // Vehicle options: virtual paint folders resolve to the paint's own file, else the kit's file (overlay only).
    std::snprintf(s.overlay_dir, sizeof(s.overlay_dir), "%s\\overlay\\", argv[1]);
    s.overlay = {"datagx/vehicles/calmini_full/body.dxt", "datagx/vehicles/calmini_full/car.dx", "datagx/vehiclepaints/calmini/2/body.dxt"};
    std::sort(s.overlay.begin(), s.overlay.end());
    {
        std::string error;
        CHECK(vehicle_options::parse("[Family:Calmini]\nmodel=BARE,FULL\nmodel_folders=Calmini,Calmini_full\npaint=A,B,C\n", s.options, error));
    }
    char target[MAX_PATH * 2]{};
    CHECK(vehicle_roster::redirect("DataGx\\Vehicles\\Calmini_full__p2\\body.dxt", target, sizeof(target)) &&
          std::string(target).find("overlay\\datagx\\vehiclepaints\\calmini\\2\\body.dxt") != std::string::npos);
    CHECK(vehicle_roster::redirect("DataGx\\Vehicles\\Calmini_full__p2\\car.dx", target, sizeof(target)) &&
          std::string(target).find("overlay\\datagx\\vehicles\\calmini_full\\car.dx") != std::string::npos);
    CHECK(vehicle_roster::redirect("DataGx/Vehicles/Calmini_full/car.dx", target, sizeof(target)));                  // real overlay file
    CHECK(!vehicle_roster::redirect("DataGx\\Vehicles\\Calmini_full__p3\\body.dxt", target, sizeof(target)));         // paint 3 not declared
    CHECK(!vehicle_roster::redirect("DataGx\\Vehicles\\Calmini_full__p1\\wheel.dx", target, sizeof(target)));        // no such file anywhere
    CHECK(!vehicle_roster::redirect("DataGx\\Vehicles\\Pajero__p1\\car.dx", target, sizeof(target)));                // undeclared family
    std::printf(failures ? "vehicle_roster_tests: %d FAILED\n" : "vehicle_roster_tests: PASS\n", failures);
    return failures ? 1 : 0;
}
