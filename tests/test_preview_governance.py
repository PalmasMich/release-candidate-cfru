from pathlib import Path
import json
import unittest

ROOT = Path(__file__).resolve().parents[1]
CONTENT = ROOT / "content" / "cagliari_preview"


class PreviewGovernanceTest(unittest.TestCase):
    def test_acceptance_contract_keeps_preview_on_feature_branch(self):
        acceptance = json.loads((CONTENT / "playable_acceptance.json").read_text(encoding="utf-8"))
        governance = acceptance["governance"]
        self.assertEqual(governance["branch"], "feature/cagliari-preview-0.1")
        self.assertTrue(governance["pr_must_remain_draft"])
        self.assertTrue(governance["rom_binary_must_not_be_committed"])

    def test_repository_does_not_track_full_rom_or_save_binaries(self):
        forbidden_suffixes = {".gba", ".sav", ".srm"}
        offenders = []
        for path in ROOT.rglob("*"):
            if not path.is_file():
                continue
            if ".git" in path.parts:
                continue
            if path.suffix.lower() in forbidden_suffixes:
                offenders.append(path.relative_to(ROOT).as_posix())
        self.assertEqual(offenders, [], f"private ROM/save binaries must not be tracked: {offenders}")

    def test_private_smoke_is_the_only_remaining_manual_gate(self):
        acceptance = json.loads((CONTENT / "playable_acceptance.json").read_text(encoding="utf-8"))
        self.assertTrue(acceptance["next_private_smoke"]["manual_only"])
        self.assertTrue(acceptance["next_private_smoke"]["minimum_route"])
        self.assertTrue(all(
            item["status"] == "implemented_pending_private_smoke"
            for item in acceptance["critical_path"]
        ))


if __name__ == "__main__":
    unittest.main()
