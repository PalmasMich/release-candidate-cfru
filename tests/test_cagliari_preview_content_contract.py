from pathlib import Path
import json
import unittest

ROOT = Path(__file__).resolve().parents[1]
CONTENT = ROOT / "content" / "cagliari_preview"


def load(name):
    return json.loads((CONTENT / name).read_text())


class CagliariPreviewContentContractTest(unittest.TestCase):
    def test_map_graph_references_existing_maps(self):
        maps = load("maps.yml")["maps"]
        ids = {item["id"] for item in maps}
        self.assertIn("RC_DELIVERY_HUB", ids)
        self.assertIn("RC_PORT_CONNECTION", ids)
        for item in maps:
            for target in item.get("connects_to", []):
                self.assertIn(target, ids, f"{item['id']} points to missing map {target}")

    def test_story_dialogue_references_exist(self):
        dialogue_ids = {scene["id"] for scene in load("dialogue.yml")["scenes"]}
        trainers = load("trainers.yml")
        for key in ("intro_dialogue", "outro_dialogue"):
            for trainer in trainers.values():
                if key in trainer:
                    self.assertIn(trainer[key], dialogue_ids)
        required = {
            "RC_DIALOGUE_OPENING", "RC_DIALOGUE_STARTER", "RC_DIALOGUE_RIVAL_INTRO",
            "RC_DIALOGUE_WILD_TUTORIAL_TRIGGER", "RC_DIALOGUE_DEPLOY_TEASER",
        }
        self.assertTrue(required <= dialogue_ids)

    def test_preview_species_symbols_are_consistent(self):
        custom_species = {
            "SPECIES_RC_TURTLE_01", "SPECIES_RC_FROG_01",
            "SPECIES_RC_FIREFOX_01", "SPECIES_RC_CAGLIARI_WILD_01",
        }
        trainers = load("trainers.yml")
        matrix = trainers["rival"]["starter_matrix"]
        self.assertEqual(set(matrix), custom_species - {"SPECIES_RC_CAGLIARI_WILD_01"})
        self.assertEqual(set(matrix.values()), custom_species - {"SPECIES_RC_CAGLIARI_WILD_01"})
        for trainer in (trainers["route_trainer"], trainers["release_manager"]):
            party = trainer.get("party", trainer.get("desired_party", []))
            for mon in party:
                species = mon["species"]
                if species.startswith("SPECIES_RC_"):
                    self.assertIn(species, custom_species)
        encounters = load("encounters.yml")["tables"]
        for table in encounters:
            for slot in table["slots"]:
                species = slot["species"]
                if species.startswith("SPECIES_RC_"):
                    self.assertIn(species, custom_species)

    def test_port_link_encounter_contract_is_complete(self):
        table = load("encounters.yml")["tables"][0]
        self.assertEqual(table["map"], "RC_PORT_CONNECTION")
        self.assertEqual(sum(slot["weight"] for slot in table["slots"]), 100)
        mistrillo = next(slot for slot in table["slots"] if slot["species"] == "SPECIES_RC_CAGLIARI_WILD_01")
        self.assertEqual(mistrillo, {
            "species": "SPECIES_RC_CAGLIARI_WILD_01",
            "min_level": 3,
            "max_level": 5,
            "weight": 60,
        })


if __name__ == "__main__":
    unittest.main()
