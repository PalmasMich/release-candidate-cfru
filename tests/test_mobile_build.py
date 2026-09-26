from pathlib import Path
import importlib.util
import tempfile
import unittest


ROOT = Path(__file__).resolve().parents[1]
SCRIPT = ROOT / "scripts" / "build_mobile.py"
WRAPPER = ROOT / "build-mobile.sh"


def load_mobile_build():
    spec = importlib.util.spec_from_file_location("rc_mobile_build", SCRIPT)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


class MobileBuildTest(unittest.TestCase):
    def test_sync_commands_are_fail_safe_fast_forward_only(self):
        module = load_mobile_build()
        commands = module.sync_commands("feature/example")
        self.assertEqual(commands[0], ["git", "fetch", "origin", "feature/example"])
        self.assertEqual(commands[1], ["git", "switch", "feature/example"])
        self.assertEqual(
            commands[2],
            ["git", "merge", "--ff-only", "origin/feature/example"],
        )

    def test_output_name_contains_short_sha1(self):
        module = load_mobile_build()
        with tempfile.TemporaryDirectory() as tmp:
            rom = Path(tmp) / "release_candidate_test.gba"
            rom.write_bytes(b"release-candidate")
            digest = module.sha1_file(rom)
            self.assertEqual(
                module.hashed_output_path(rom, digest).name,
                f"release_candidate_{digest[:8]}.gba",
            )

    def test_wrapper_invokes_python_orchestrator(self):
        text = WRAPPER.read_text(encoding="utf-8")
        self.assertIn("set -euo pipefail", text)
        self.assertIn("scripts/build_mobile.py", text)


if __name__ == "__main__":
    unittest.main()
