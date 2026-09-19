from pathlib import Path
import json
import unittest

ROOT = Path(__file__).resolve().parents[1]
SPEC = ROOT / "content/cagliari_preview/script_specs/RC_DELIVERY_HUB.json"


class DeliveryHubRivalContractTest(unittest.TestCase):
    def test_each_starter_triggers_the_matching_kpi_rival_party(self):
        spec = json.loads(SPEC.read_text(encoding="utf-8"))
        scripts = {script["id"]: script for script in spec["scripts"]}
        expected = {
            "RC_SCRIPT_STARTER_TARTREK": (328, "SPECIES_RC_TURTLE_01"),
            "RC_SCRIPT_STARTER_FROBYTE": (327, "SPECIES_RC_FROG_01"),
            "RC_SCRIPT_STARTER_EMBERFOX": (326, "SPECIES_RC_FIREFOX_01"),
        }
        for script_id, (trainer_id, starter_species) in expected.items():
            ops = scripts[script_id]["ops"]
            gifts = [op for op in ops if op.get("op") == "givemon"]
            battles = [op for op in ops if op.get("op") == "trainerbattle_single"]
            self.assertEqual(len(gifts), 1)
            self.assertEqual(gifts[0]["species"], starter_species)
            self.assertEqual(len(battles), 1)
            self.assertEqual(battles[0]["trainer_id"], trainer_id)
            self.assertEqual(battles[0]["intro_dialogue"], "RC_DIALOGUE_RIVAL_INTRO")
            self.assertEqual(battles[0]["defeat_dialogue"], "RC_DIALOGUE_RIVAL_REPEAT")
            battle_index = ops.index(battles[0])
            self.assertLess(ops.index(gifts[0]), battle_index)
            self.assertTrue(any(
                op.get("op") == "setflag" and op.get("flag") == "RC_FLAG_RIVAL_INTRO_DONE"
                for op in ops[battle_index + 1:]
            ))


if __name__ == "__main__":
    unittest.main()
