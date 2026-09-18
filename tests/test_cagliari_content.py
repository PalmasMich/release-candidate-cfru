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

    def test_port_link_trainer_has_dialogue_and_party(self):
        dialogue = load("dialogue.yml")
        dialogue_ids = {scene["id"] for scene in dialogue["scenes"]}
        trainer = load("trainers.yml")["route_trainer"]
        self.assertEqual(trainer["id"], "RC_TRAINER_PORT_01")
        self.assertIn(trainer["intro_dialogue"], dialogue_ids)
        self.assertIn(trainer["outro_dialogue"], dialogue_ids)
        self.assertTrue(trainer["party"])

    def test_story_events_bind_wild_trainer_and_deploy_teaser(self):
        events = {item["id"]: item for item in load("events.yml")["flow"]}
        self.assertEqual(
            events["RC_EVENT_FIRST_WILD"]["encounter_table"],
            "RC_PORT_CONNECTION_GRASS",
        )
        self.assertEqual(
            events["RC_EVENT_RIVAL_BATTLE"]["trainer"],
            "RC_TRAINER_PORT_01",
        )
        self.assertEqual(
            events["RC_EVENT_DEPLOY_TEASER"]["dialogue"],
            "RC_DIALOGUE_DEPLOY_TEASER",
        )

    def test_story_flag_dependencies_form_linear_preview_flow(self):
        events = load("events.yml")
        produced = set()
        for event in events["flow"]:
            self.assertTrue(set(event.get("requires", [])).issubset(produced))
            produced.update(event.get("sets", []))
        self.assertTrue(set(events["flags"]).issubset(produced))


if __name__ == "__main__":
    unittest.main()
