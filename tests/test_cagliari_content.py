from pathlib import Path
import json
import unittest

ROOT = Path(__file__).resolve().parents[1]
CONTENT = ROOT / "content" / "cagliari_preview"


def load(name: str):
    return json.loads((CONTENT / name).read_text(encoding="utf-8"))


class CagliariPreviewContentTest(unittest.TestCase):
    def test_required_maps_exist(self):
        maps = load("maps.yml")
        ids = {item["id"] for item in maps["maps"]}
        self.assertTrue({
            "RC_DELIVERY_HUB",
            "RC_CAGLIARI_MARINA",
            "RC_PORT_CONNECTION",
        }.issubset(ids))

    def test_required_story_flags_exist(self):
        events = load("events.yml")
        flags = set(events["flags"])
        self.assertTrue({
            "RC_FLAG_STARTER_CHOSEN",
            "RC_FLAG_RIVAL_INTRO_DONE",
            "RC_FLAG_WILD_TUTORIAL_DONE",
            "RC_FLAG_RIVAL_BATTLE_DONE",
            "RC_FLAG_DEPLOY_TEASER_SEEN",
        }.issubset(flags))

    def test_approved_opening_line_is_present(self):
        dialogue = load("dialogue.yml")
        lines = [line for scene in dialogue["scenes"] for line in scene["lines"]]
        self.assertIn(
            "Benvenuto a Cagliari. Il progetto era già iniziato quando sei arrivato.",
            lines,
        )

    def test_original_wild_species_is_in_encounters(self):
        encounters = load("encounters.yml")
        species = {
            slot["species"]
            for table in encounters["tables"]
            for slot in table["slots"]
        }
        self.assertIn("SPECIES_RC_CAGLIARI_WILD_01", species)

    def test_rival_uses_unchosen_starter_matrix(self):
        trainers = load("trainers.yml")
        matrix = trainers["rival"]["starter_matrix"]
        self.assertEqual(matrix["SPECIES_RC_TURTLE_01"], "SPECIES_RC_FIREFOX_01")
        self.assertEqual(matrix["SPECIES_RC_FROG_01"], "SPECIES_RC_TURTLE_01")
        self.assertEqual(matrix["SPECIES_RC_FIREFOX_01"], "SPECIES_RC_FROG_01")


if __name__ == "__main__":
    unittest.main()
