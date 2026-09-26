from pathlib import Path
import json
import unittest

ROOT = Path(__file__).resolve().parents[1]
SPEC = ROOT / "content/cagliari_preview/script_specs/RC_PORT_CONNECTION.json"
TRAINERS = ROOT / "content/cagliari_preview/trainers.yml"


class PortConnectionContractTest(unittest.TestCase):
    def setUp(self):
        spec = json.loads(SPEC.read_text(encoding="utf-8"))
        self.scripts = {script["id"]: script for script in spec["scripts"]}
        self.trainers = json.loads(TRAINERS.read_text(encoding="utf-8"))

    def test_first_field_test_is_guaranteed_mistrillo_once(self):
        ops = self.scripts["RC_SCRIPT_WILD_TUTORIAL_TRIGGER"]["ops"]
        battles = [op for op in ops if op.get("op") == "setwildbattle"]
        self.assertEqual(battles, [{"op": "setwildbattle", "species": "SPECIES_RC_CAGLIARI_WILD_01", "level": 3}])
        self.assertTrue(any(op.get("op") == "checkflag" and op.get("flag") == "RC_FLAG_WILD_TUTORIAL_DONE" for op in ops))
        battle_index = next(i for i, op in enumerate(ops) if op.get("op") == "dowildbattle")
        flag_index = next(i for i, op in enumerate(ops) if op.get("op") == "setflag" and op.get("flag") == "RC_FLAG_WILD_TUTORIAL_DONE")
        self.assertLess(battle_index, flag_index)

    def test_port_trainer_script_uses_manifest_bootstrap_id(self):
        ops = self.scripts["RC_SCRIPT_PORT_TRAINER"]["ops"]
        battles = [op for op in ops if op.get("op") == "trainerbattle_single"]
        self.assertEqual(len(battles), 1)
        self.assertEqual(battles[0]["trainer_id"], self.trainers["route_trainer"]["bootstrap_trainer_id"])
        self.assertEqual(battles[0]["intro_dialogue"], self.trainers["route_trainer"]["intro_dialogue"])
        self.assertEqual(battles[0]["defeat_dialogue"], "RC_DIALOGUE_PORT_TRAINER_DEFEAT")
        self.assertTrue(any(op.get("op") == "setflag" and op.get("flag") == "RC_FLAG_PORT_TRAINER_DONE" for op in ops))


if __name__ == "__main__":
    unittest.main()
