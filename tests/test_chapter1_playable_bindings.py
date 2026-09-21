from pathlib import Path
import json
import unittest

ROOT = Path(__file__).resolve().parents[1]
MAPS = ROOT / "content" / "cagliari_preview" / "map_specs"


def load_map(name: str) -> dict:
    return json.loads((MAPS / f"{name}.json").read_text(encoding="utf-8"))


class Chapter1PlayableBindingsTest(unittest.TestCase):
    def test_delivery_hub_exposes_all_three_starter_interactions(self):
        hub = load_map("RC_DELIVERY_HUB")
        by_script = {item["script"]: item for item in hub["interactions"]}
        expected = {
            "RC_SCRIPT_STARTER_TARTREK": ("starter_tartrek", "SPECIES_RC_TURTLE_01"),
            "RC_SCRIPT_STARTER_FROBYTE": ("starter_frobyte", "SPECIES_RC_FROG_01"),
            "RC_SCRIPT_STARTER_EMBERFOX": ("starter_emberfox", "SPECIES_RC_FIREFOX_01"),
        }
        self.assertEqual(set(by_script), set(expected))
        for script, (anchor, species) in expected.items():
            self.assertEqual(by_script[script]["anchor"], anchor)
            self.assertEqual(by_script[script]["choice"], species)

    def test_delivery_hub_exit_is_gated_by_completed_kpi_rival_intro(self):
        hub = load_map("RC_DELIVERY_HUB")
        exits = [w for w in hub["warps"] if w["target_map"] == "RC_CAGLIARI_MARINA"]
        self.assertEqual(len(exits), 1)
        self.assertIn("RC_FLAG_RIVAL_INTRO_DONE", exits[0].get("requires", []))

    def test_port_link_first_custom_encounter_is_bound_to_a_coord_event(self):
        port = load_map("RC_PORT_CONNECTION")
        triggers = [e for e in port.get("coord_events", []) if e.get("script") == "RC_SCRIPT_WILD_TUTORIAL_TRIGGER"]
        self.assertEqual(len(triggers), 1)
        self.assertEqual(triggers[0]["anchor"], "field_test_trigger")
        self.assertEqual(triggers[0]["var_id"], "0x0000")
        self.assertEqual(int(triggers[0]["var_value"]), 0)

    def test_port_link_trainer_and_return_warp_are_reachable_content(self):
        port = load_map("RC_PORT_CONNECTION")
        trainers = [o for o in port["objects"] if o.get("script") == "RC_SCRIPT_PORT_TRAINER"]
        self.assertEqual(len(trainers), 1)
        self.assertEqual(trainers[0]["anchor"], "port_trainer")
        returns = [w for w in port["warps"] if w["target_map"] == "RC_CAGLIARI_MARINA"]
        self.assertEqual(len(returns), 1)
        self.assertEqual(returns[0]["anchor"], "marina_entrance")


if __name__ == "__main__":
    unittest.main()
