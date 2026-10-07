#pragma once
#include "sdk.hpp"
#include <string>
#include <vector>
#include <cstdint>
namespace gfx2 {
// A restricted, decoded instruction recipe, not an arbitrary AOB wildcard.
struct FingerprintInstruction {uint16_t offset,length;bool relative_call=false;std::vector<unsigned char> callee_prefix;};
struct FeatureFingerprint {
 std::string id,section=".text";uint32_t known_rva=0,target_offset=0;
 std::vector<unsigned char> bytes;std::vector<FingerprintInstruction> instructions;
 size_t anchor_size=0;bool freeze_branch=false;
};
struct CodeSection {std::string name;uint32_t rva=0;std::vector<unsigned char> bytes;};
struct FeatureCapability {
 std::string id,method="unsupported",status="UNSUPPORTED",reason="owner_not_found";
 uint32_t candidate_rva=0;unsigned matches=0;bool fast_path=false,bytes_valid=false,instructions_valid=false;
 bool supported() const noexcept {return status=="SUPPORTED"||status=="ALREADY_PATCHED";}
 std::string json() const;
};
FeatureFingerprint freeze_fingerprint();
FeatureFingerprint ui_fingerprint();
FeatureCapability verify_feature(const std::vector<CodeSection>&,const FeatureFingerprint&,bool known);
struct Compatibility {
 FeatureCapability freeze,ui,margins,fov,shadow,vehicle;
 std::string json(const std::string& sha,bool known) const;
};
Compatibility inspect_compatibility(bool known) noexcept;
bool ui_owner(const FeatureCapability&,bool exe,uint32_t return_rva) noexcept;
}
