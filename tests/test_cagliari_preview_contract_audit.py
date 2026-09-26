from pathlib import Path
import importlib.util
import unittest

ROOT = Path(__file__).resolve().parents[1]
AUDITOR = ROOT / "scripts" / "audit_cagliari_preview_contract.py"


def load_auditor():
    spec = importlib.util.spec_from_file_location("rc_preview_auditor", AUDITOR)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


class CagliariPreviewContractAuditTest(unittest.TestCase):
    def test_static_preview_contract_is_release_candidate_ready(self):
        auditor = load_auditor()
        self.assertEqual(auditor.main(), 0)

    def test_private_rom_remains_the_only_manual_gate(self):
        auditor = load_auditor()
        acceptance = auditor.load("playable_acceptance.json")
        smoke = acceptance["next_private_smoke"]
        self.assertTrue(smoke["manual_only"])
        self.assertIn("boot", smoke["minimum_route"])
        self.assertTrue(any("Mistrillo" in step for step in smoke["minimum_route"]))

    def test_preview_acceptance_path_stays_thin_and_ordered(self):
        auditor = load_auditor()
        events = auditor.load("events.yml")
        self.assertEqual(
            events["preview_acceptance_path"],
            [
                "RC_EVENT_ARRIVAL",
                "RC_EVENT_STARTER_ASSIGNMENT",
                "RC_EVENT_RIVAL_INTRO",
                "RC_EVENT_FIRST_WILD",
                "RC_EVENT_DEPLOY_TEASER",
            ],
        )


if __name__ == "__main__":
    unittest.main()
