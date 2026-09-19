from pathlib import Path
import json
import unittest

ROOT = Path(__file__).resolve().parents[1]
CONTENT = ROOT / "content" / "cagliari_preview"


def load(name: str):
    return json.loads((CONTENT / name).read_text(encoding="utf-8"))


class CagliariPreviewContentTest(unittest.TestCase):
    def test_chapter_one_has_permanent_original_world_maps(self):
        maps = load("maps.yml")
        self.assertEqual(maps["chapter"]["id"], "RC_CHAPTER_01_CAGLIARI")

        by_id = {item["id"]: item for item in maps["maps"]}
        required = {
            "RC_CAGLIARI_ARRIVAL",
            "RC_DELIVERY_HUB",
            "RC_CAGLIARI_MARINA",
            "RC_PORT_CONNECTION",
            "RC_CASTELLO_ASCENT",
            "RC_DEPLOY_DISTRICT",
            "RC_DEPLOY_ROOM_01",
        }
        self.assertTrue(required.issubset(by_id))
        self.assertEqual(
            by_id["RC_PORT_CONNECTION"]["status"],
            "bootstrap_replacement_pending",
        )
        self.assertEqual(
            by_id["RC_PORT_CONNECTION"]["bootstrap_source"],
            "FIRERED_ROUTE_1",
        )
        permanent = {
            map_id
            for map_id, item in by_id.items()
            if item.get("status") == "permanent"
        }
        self.assertTrue({
            "RC_CAGLIARI_ARRIVAL",
            "RC_DELIVERY_HUB",
            "RC_CAGLIARI_MARINA",
            "RC_CASTELLO_ASCENT",
            "RC_DEPLOY_DISTRICT",
            "RC_DEPLOY_ROOM_01",
        }.issubset(permanent))

    def test_required_story_flags_cover_preview_and_chapter_climax(self):
        events = load("events.yml")
        flags = set(events["flags"])
        self.assertTrue({
            "RC_FLAG_ARRIVAL_DONE",
            "RC_FLAG_STARTER_CHOSEN",
            "RC_FLAG_RIVAL_INTRO_DONE",
            "RC_FLAG_WILD_TUTORIAL_DONE",
            "RC_FLAG_PORT_TRAINER_DONE",
            "RC_FLAG_DEPLOY_TEASER_SEEN",
            "RC_FLAG_SCOPE_CHANGE_REVEALED",
            "RC_FLAG_CASTELLO_UNLOCKED",
            "RC_FLAG_GO_NO_GO_STARTED",
            "RC_FLAG_RELEASE_MANAGER_DEFEATED",
            "RC_FLAG_DEPLOY_01_COMPLETE",
        }.issubset(flags))

    def test_approved_opening_line_is_present(self):
        dialogue = load("dialogue.yml")
        lines = [line for scene in dialogue["scenes"] for line in scene["lines"]]
        self.assertIn(
            "Benvenuto a Cagliari. Il progetto era già iniziato quando sei arrivato.",
            lines,
        )

    def test_chapter_one_dialogue_is_full_rewrite_scaffold(self):
        dialogue = load("dialogue.yml")
        ids = {scene["id"] for scene in dialogue["scenes"]}
        required = {
            "RC_DIALOGUE_OPENING",
            "RC_DIALOGUE_PLAYER_NAME",
            "RC_DIALOGUE_DELIVERY_HUB_WELCOME",
            "RC_DIALOGUE_STARTER",
            "RC_DIALOGUE_RIVAL_CHALLENGE",
            "RC_DIALOGUE_FIRST_ASSIGNMENT",
            "RC_DIALOGUE_MARINA_ARRIVAL",
            "RC_DIALOGUE_PORT_TRAINER_INTRO",
            "RC_DIALOGUE_SCOPE_CHANGE",
            "RC_DIALOGUE_CASTELLO_NPC_STAKEHOLDER",
            "RC_DIALOGUE_DEPLOY_DISTRICT_ARRIVAL",
            "RC_DIALOGUE_GO_NO_GO_START",
            "RC_DIALOGUE_RELEASE_MANAGER_INTRO",
            "RC_DIALOGUE_DEPLOY_COMPLETE",
            "RC_DIALOGUE_NEXT_CHAPTER_TEASER",
        }
        self.assertTrue(required.issubset(ids))
        self.assertGreaterEqual(len(dialogue["scenes"]), 45)

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

    def test_preview_story_binds_wild_trainer_and_deploy_teaser(self):
        events = {item["id"]: item for item in load("events.yml")["flow"]}
        self.assertEqual(
            events["RC_EVENT_FIRST_WILD"]["encounter_table"],
            "RC_PORT_CONNECTION_GRASS",
        )
        self.assertEqual(
            events["RC_EVENT_PORT_TRAINER"]["trainer"],
            "RC_TRAINER_PORT_01",
        )
        self.assertEqual(
            events["RC_EVENT_DEPLOY_TEASER"]["dialogue"],
            "RC_DIALOGUE_DEPLOY_TEASER",
        )
        self.assertEqual(
            events["RC_EVENT_PORT_TRAINER"]["implementation_status"],
            "bootstrap_route1",
        )

    def test_story_continues_beyond_preview_into_deploy_one(self):
        events = {item["id"]: item for item in load("events.yml")["flow"]}
        self.assertIn("RC_FLAG_SCOPE_CHANGE_REVEALED", events["RC_EVENT_SCOPE_CHANGE"]["sets"])
        self.assertIn("RC_FLAG_CASTELLO_UNLOCKED", events["RC_EVENT_SCOPE_CHANGE"]["sets"])
        self.assertIn("RC_FLAG_GO_NO_GO_STARTED", events["RC_EVENT_GO_NO_GO"]["sets"])
        self.assertIn(
            "RC_FLAG_RELEASE_MANAGER_DEFEATED",
            events["RC_EVENT_RELEASE_MANAGER"]["sets"],
        )
        self.assertIn(
            "RC_FLAG_DEPLOY_01_COMPLETE",
            events["RC_EVENT_DEPLOY_01_COMPLETE"]["sets"],
        )

    def test_story_flag_dependencies_form_linear_chapter_flow(self):
        events = load("events.yml")
        produced = set()
        for event in events["flow"]:
            self.assertTrue(set(event.get("requires", [])).issubset(produced))
            produced.update(event.get("sets", []))
        self.assertTrue(set(events["flags"]).issubset(produced))


if __name__ == "__main__":
    unittest.main()
