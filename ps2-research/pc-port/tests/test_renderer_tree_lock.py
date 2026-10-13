"""Corpus-independent tests of the immutable renderer staging admission gate."""
import importlib.util
from pathlib import Path
import subprocess
import tempfile
import unittest


SCRIPT = Path(__file__).resolve().parents[1] / "overlay" / "build_overlay.py"
spec = importlib.util.spec_from_file_location("renderer_overlay", SCRIPT)
overlay = importlib.util.module_from_spec(spec)
spec.loader.exec_module(overlay)


class RendererTreeLockTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        self.git("init", "-q", "-b", "master")
        self.git("config", "user.email", "test@example.invalid")
        self.git("config", "user.name", "Tree lock test")
        self.file = self.root / "modernization" / "renderer" / "source.cpp"
        self.file.parent.mkdir(parents=True)
        self.file.write_text("frozen source\n")
        self.commit()
        self.lock = {"baseline_branch": "master", "baseline_head": self.git("rev-parse", "HEAD"),
                     "renderer_tree": self.git("rev-parse", "HEAD:modernization/renderer")}

    def git(self, *args):
        return subprocess.check_output(["git", *args], cwd=self.root, text=True,
                                       stderr=subprocess.STDOUT).strip()

    def commit(self):
        self.git("add", ".")
        self.git("commit", "-q", "-m", "fixture")

    def verify(self):
        return overlay.verify_renderer_identity(self.root, self.lock)

    def test_unrelated_commits_permitted_but_staging_commit_is_unchanged(self):
        (self.root / "research.md").write_text("unrelated research\n")
        self.commit()
        result = self.verify()
        self.assertNotEqual(result["current_head"], result["baseline_head"])
        self.assertEqual(result["baseline_head"], self.lock["baseline_head"])
        self.assertEqual(result["renderer_tree"], self.lock["renderer_tree"])

    def test_committed_renderer_drift_rejected(self):
        self.file.write_text("changed source\n")
        self.commit()
        with self.assertRaisesRegex(RuntimeError, "tree mismatch"):
            self.verify()

    def test_tracked_worktree_and_index_drift_rejected(self):
        self.file.write_text("changed source\n")
        with self.assertRaisesRegex(RuntimeError, "tracked working-tree"):
            self.verify()
        self.git("add", ".")
        with self.assertRaisesRegex(RuntimeError, "tracked working-tree"):
            self.verify()

    def test_untracked_source_rejected(self):
        (self.file.parent / "new.cpp").write_text("untracked\n")
        with self.assertRaisesRegex(RuntimeError, "untracked source"):
            self.verify()

    def test_ignored_build_output_is_not_a_source_input(self):
        (self.root / ".gitignore").write_text("modernization/renderer/.build/\n")
        self.commit()
        folder = self.file.parent / ".build"
        folder.mkdir()
        (folder / "artifact.dll").write_bytes(b"synthetic")
        self.verify()

    def test_wrong_branch_rejected(self):
        self.git("switch", "-q", "-c", "fixture-other")
        with self.assertRaisesRegex(RuntimeError, "Expected branch"):
            self.verify()

    def test_tree_lock_cannot_be_rebound_to_changed_head(self):
        self.file.write_text("changed source\n")
        self.commit()
        self.lock["renderer_tree"] = self.git("rev-parse", "HEAD:modernization/renderer")
        with self.assertRaisesRegex(RuntimeError, "tree mismatch"):
            self.verify()

    def test_missing_tree_lock_rejected(self):
        self.lock.pop("renderer_tree")
        with self.assertRaisesRegex(RuntimeError, "Missing or invalid"):
            self.verify()


if __name__ == "__main__":
    unittest.main()
