"""Windows preflight evidence for the opt-in input binding launcher."""
import subprocess
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
LAUNCHER = ROOT/'.research-output/vehicles/extra-set1/launcher-build/Release/mr-runtime-launcher.exe'
OLD_LAUNCHER = ROOT/'.research-output/vehicles/v-def4-1/delivery-final/32/workshop/builds/first/candidate/launcher/mr-runtime-launcher.exe'
BUNDLE = ROOT/'.research-output/vehicles/v-def4-1/delivery-final/32/workshop/builds/first/candidate/runtime'
DLL = ROOT.parent/'master-rallye-re-rmod1/.research-output/extra-set1/binding-07/dinput8.dll'
EXE = ROOT.parent/'corpora/retail/MRallye.exe'


class InputBindingPreflight(unittest.TestCase):
    def test_abi_admission_rejects_unknown_and_preserves_default(self):
        if not all(p.is_file() for p in (LAUNCHER, OLD_LAUNCHER, DLL, EXE)) or not BUNDLE.is_dir():
            self.skipTest('private compiler output or owner-supplied game corpus is unavailable')
        import shutil
        parent = ROOT/'.research-output/vehicles/extra-set1'
        with tempfile.TemporaryDirectory(dir=parent) as tmp:
            host = Path(tmp)
            shutil.copyfile(EXE, host/'MRallye.exe')
            proxy = host/'dinput8.dll'
            original = DLL.read_bytes()
            def check(launcher):
                return subprocess.run([str(launcher), '--verify-launch-environment', str(host/'MRallye.exe'), str(BUNDLE)],
                                      capture_output=True, text=True, timeout=30)
            proxy.write_bytes(original)
            self.assertEqual(check(LAUNCHER).returncode, 0)
            self.assertNotEqual(check(OLD_LAUNCHER).returncode, 0)
            # Unrelated PE overlay data changes SHA while preserving the ABI.
            proxy.write_bytes(original + b'non-code diagnostic overlay')
            self.assertEqual(check(LAUNCHER).returncode, 0)
            corrupt = original.replace(b'MRExtraSdkBindingAbi', b'MRExtraSdkBindingAbX')
            self.assertNotEqual(corrupt, original)
            proxy.write_bytes(corrupt)
            self.assertNotEqual(check(LAUNCHER).returncode, 0)
            proxy.write_bytes(b'MZ truncated')
            self.assertNotEqual(check(LAUNCHER).returncode, 0)
            proxy.unlink()
            self.assertEqual(check(LAUNCHER).returncode, 0)
