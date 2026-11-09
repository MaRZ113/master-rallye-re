#define RMOD_EXTRA_OPTIONS 1
#include "../../src/native/rmod1/runtime_core.cpp"
#include <iostream>
std::vector<std::string> reports;
int main() {
    g_generation_config.logging_enabled=true;g_generation_config.config_version=2;
    g_generation_config.mode_policies[0]=rmod1::Policy::Stock;
    g_registered={{33,1,true,true,true,true,7},{34,1,true,true,true,true,7}};
    g_final_roster_reader=[](int& player,std::vector<int>& ai){player=7;ai={33,34};return true;};
    g_final_roster_sink=[](const char* line){reports.emplace_back(line);};
    MRSetStartPhaseV1(4);
    g_ai_observations.push_back({1,{7,33,34},{7,33,34}});
    MRSetStartPhaseV1(5);MRSetStartPhaseV1(5);
    if(reports.size()!=1)return 1;
    for(const auto* term:{"policy=Stock","player=7","ai=[33,34]","addon=33:selected","addon=34:selected","before=[7,33,34]","after=[7,33,34]"})if(reports[0].find(term)==std::string::npos)return 2;
    MRSetStartPhaseV1(4);g_final_roster_reader=[](int& player,std::vector<int>& ai){player=34;ai={33};return true;};MRSetStartPhaseV1(5);
    if(reports.size()!=2||reports[1].find("addon=34:human-excluded")==std::string::npos)return 3;
    std::cout<<"AI_FINAL_REPORT_PASS production phase code; native snapshot/sink replaced by fixtures; final33/34, human exclusion and duplicate phase5 suppressed\n";
}
