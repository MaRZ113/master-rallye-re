import copy,unittest
from tools.build_runtime_launcher import _header,LauncherBuildError

class NativeDataPageTests(unittest.TestCase):
    def test_exact_sealed_single_data_page(self):
        p={k:'a'*64 for k in ('addon_plan_sha256','native_patch_manifest_sha256','native_patch_operations_sha256','resource_manifest_sha256','resource_index_sha256','reconstructed_reference_file_sha256')}
        p.update(retail_exe={'sha256':'a'*64},resource_count=1,native_extension={'address':0x10000000,'size':16384,'allocation_size':65536,'sha256':'a'*64})
        legacy=_header(p,{'operations':[{}]});self.assertNotIn(b'MR_EXTENSION_RW_SIZE',legacy)
        p['native_extension']['writable_ranges']=[{'offset':8192,'size':4096}]
        self.assertIn(b'MR_EXTENSION_RW_OFFSET 8192u',_header(p,{'operations':[{}]}))
        for r in ([{'offset':0,'size':4096}],[{'offset':8193,'size':4096}],[{'offset':16384,'size':4096}],[{'offset':8192,'size':8192}],[{'offset':True,'size':4096}]):
            q=copy.deepcopy(p);q['native_extension']['writable_ranges']=r
            with self.assertRaises(LauncherBuildError):_header(q,{'operations':[{}]})
