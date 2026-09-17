from pathlib import Path
import unittest

ROOT = Path(__file__).resolve().parents[1]


class ReleaseCandidateWorkspaceContractTest(unittest.TestCase):
    def test_rom_binary_is_git_ignored(self):
        ignore = (ROOT / ".gitignore").read_text(encoding="utf-8")
        self.assertIn("*.gba", ignore)

    def test_build_contract_exists(self):
        contract = ROOT / "docs/rom/BUILD_CONTRACT.md"
        self.assertTrue(contract.exists())
        text = contract.read_text(encoding="utf-8")
        self.assertIn("DPE -> CFRU", text)
        self.assertIn("BPRE0.gba", text)
        self.assertIn("must never be committed", text)

    def test_workspace_validator_exists(self):
        validator = ROOT / "scripts/validate_release_candidate_workspace.py"
        self.assertTrue(validator.exists())


if __name__ == "__main__":
    unittest.main()
