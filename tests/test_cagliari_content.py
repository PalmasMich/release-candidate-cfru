from pathlib import Path
import copy
import importlib.util
import json
import unittest

ROOT = Path(__file__).resolve().parents[1]
CONTENT = ROOT / "content" / "cagliari_preview"
VALIDATOR = ROOT / "scripts" / "validate_cagliari_content.py"


def load(name: str):
    return json.loads((CONTENT / name).read_text(encoding="utf-8"))


def load_validator():
    spec = importlib.util.spec_from_file_location("rc_content_validator", VALIDATOR)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


class CagliariPreviewContentTest(unittest.TestCase):
    def test_content_validator_accepts_canonical_graph(self):
        load_validator().validate()

    def test_content_validator_rejects_map_graph_drift(self):
        validator = load_validator()
        maps = load("maps.yml")
        broken = copy.deepcopy(maps)
        broken["maps"][0]["connects_to"] = []
        specs = [
            json.loads(path.read_text(encoding="utf-8"))
            for path in (CONTENT / "map_specs").glob("RC_*.json")
        ]
        with self.assertRaisesRegex(ValueError, "compiled warp targets"):
            validator.validate_map_graph(broken, specs)

    def test_chapter_one_has_permanent_original_world_maps(self):
        maps = load("maps.yml")
        self.assertEqual(maps["chapter"]["id"], "RC_CHAPTER_01_CAGLIARI")

        by_id = {item["id"]: item for item in maps["maps"]}
        compiled = {
            path.stem
            for path in (CONTENT / "map_specs").glob("RC_*.json")
        }
        self.assertEqual(set(by_id), compiled)
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
            "RC_DELIVERY_HUB",
            "RC_CAGLIARI_MARINA",
            "RC_CASTELLO_ASCENT",
            "RC_DEPLOY_DISTRICT",
            "RC_DEPLOY_ROOM",
        }.issubset(permanent))

    def test_every_story_event_targets_a_compiled_map(self):
        compiled = {
            path.stem
            for path in (CONTENT / "map_specs").glob("RC_*.json")
        }
        events = load("events.yml")
        targets = {
            item["map"]
            for section in ("flow", "optional_flow")
            for item in events.get(section, [])
        }
        self.assertTrue(targets.issubset(compiled), sorted(targets - compiled))

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
            "Benvenuto su Release Candidate.",
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

    def test_kpi_rival_uses_fixed_authored_speaker_name(self):
        dialogue = load("dialogue.yml")
        speakers = {scene["speaker"] for scene in dialogue["scenes"]}
        self.assertNotIn("Rivale", speakers)
        self.assertIn("KPI Rival", speakers)
        self.assertEqual(load("trainers.yml")["rival"]["display_name"], "KPI Rival")

    def test_all_custom_script_dialogue_refs_resolve(self):
        dialogue_ids = {scene["id"] for scene in load("dialogue.yml")["scenes"]}
        script_dir = CONTENT / "script_specs"
        refs = set()
        for path in script_dir.glob("*.json"):
            spec = json.loads(path.read_text(encoding="utf-8"))
            for script in spec.get("scripts", []):
                for op in script.get("ops", []):
                    for key in ("dialogue", "intro_dialogue", "defeat_dialogue"):
                        if key in op:
                            refs.add(op[key])
        self.assertTrue(refs)
        self.assertTrue(refs.issubset(dialogue_ids), sorted(refs - dialogue_ids))

    def test_custom_chapter_dialogue_contains_no_visible_firered_story_terms(self):
        dialogue = load("dialogue.yml")
        text = "\n".join(line for scene in dialogue["scenes"] for line in scene["lines"])
        forbidden = ("PALLET", "VIRIDIAN", "OAK", "BULBASAUR", "SQUIRTLE", "CHARMANDER")
        for term in forbidden:
            self.assertNotIn(term, text.upper())

    def test_optional_chapter_activities_are_non_blocking_and_stateful(self):
        events = load("events.yml")
        optional = {item["id"]: item for item in events.get("optional_flow", [])}
        self.assertEqual(set(optional), {
            "RC_OPTIONAL_MARINA_BUG_HUNT",
            "RC_OPTIONAL_RAMEN_STOP",
            "RC_OPTIONAL_CASTELLO_VIEWPOINT",
        })
        for item in optional.values():
            self.assertFalse(item["blocks_main_story"])
            self.assertTrue(item["sets"])

        flags = load("flags.json")["flags"]
        self.assertEqual(flags["RC_FLAG_MARINA_BUG_REPORT_DONE"], "0x0BA")
        self.assertEqual(flags["RC_FLAG_RAMEN_STOP_VISITED"], "0x0BB")
        self.assertEqual(flags["RC_FLAG_CASTELLO_VIEWPOINT_SEEN"], "0x0BC")

    def test_optional_exploration_dialogues_are_wired_to_custom_maps(self):
        marina = json.loads((CONTENT / "map_specs" / "RC_CAGLIARI_MARINA.json").read_text(encoding="utf-8"))
        castello = json.loads((CONTENT / "map_specs" / "RC_CASTELLO_ASCENT.json").read_text(encoding="utf-8"))
        marina_scripts = {item["script"] for item in marina.get("interactions", [])}
        castello_scripts = {item["script"] for item in castello.get("interactions", [])}
        self.assertIn("RC_SCRIPT_MARINA_BUG_TERMINAL", marina_scripts)
        self.assertIn("RC_SCRIPT_RAMEN_STOP", marina_scripts)
        self.assertIn("RC_SCRIPT_CASTELLO_VIEWPOINT", castello_scripts)

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

    def test_delivery_hub_first_entry_runs_custom_arrival_once(self):
        hub_map = json.loads((CONTENT / "map_specs" / "RC_DELIVERY_HUB.json").read_text(encoding="utf-8"))
        hub_scripts = json.loads((CONTENT / "script_specs" / "RC_DELIVERY_HUB.json").read_text(encoding="utf-8"))
        coord = {item["id"]: item for item in hub_map.get("coord_events", [])}
        scripts = {item["id"]: item for item in hub_scripts["scripts"]}
        self.assertIn("RC_COORD_HUB_ARRIVAL", coord)
        self.assertEqual(coord["RC_COORD_HUB_ARRIVAL"]["script"], "RC_SCRIPT_HUB_ARRIVAL")
        ops = scripts["RC_SCRIPT_HUB_ARRIVAL"]["ops"]
        self.assertIn({"op": "checkflag", "flag": "RC_FLAG_ARRIVAL_DONE"}, ops)
        self.assertIn({"op": "msgbox", "dialogue": "RC_DIALOGUE_OPENING", "type": 4}, ops)
        self.assertIn({"op": "setflag", "flag": "RC_FLAG_ARRIVAL_DONE"}, ops)

    def test_conditioned_warps_use_real_flagged_blockers(self):
        hub = load("map_specs/RC_DELIVERY_HUB.json")
        marina = load("map_specs/RC_CAGLIARI_MARINA.json")
        district = load("map_specs/RC_DEPLOY_DISTRICT.json")
        for spec in (hub, marina, district):
            self.assertFalse(any(warp.get("requires") for warp in spec["warps"]))

        blockers = {
            obj["id"]: obj
            for spec in (hub, marina, district)
            for obj in spec["objects"]
            if obj.get("visibility_flag")
        }
        self.assertEqual(
            blockers["RC_NPC_HUB_EXIT_GATE"]["visibility_flag"],
            "RC_FLAG_RIVAL_INTRO_DONE",
        )
        self.assertEqual(
            blockers["RC_NPC_PORT_LINK_GATE"]["visibility_flag"],
            "RC_FLAG_RIVAL_INTRO_DONE",
        )
        self.assertEqual(
            blockers["RC_NPC_CASTELLO_GATE"]["visibility_flag"],
            "RC_FLAG_CASTELLO_UNLOCKED",
        )
        self.assertEqual(
            blockers["RC_NPC_RELEASE_GATE"]["visibility_flag"],
            "RC_FLAG_GO_NO_GO_STARTED",
        )

    def test_custom_starter_assignment_is_single_and_flagged_after_givemon(self):
        hub = json.loads((CONTENT / "script_specs" / "RC_DELIVERY_HUB.json").read_text(encoding="utf-8"))
        scripts = {item["id"]: item for item in hub["scripts"]}
        expected = {
            "RC_SCRIPT_STARTER_TARTREK": "SPECIES_RC_TURTLE_01",
            "RC_SCRIPT_STARTER_FROBYTE": "SPECIES_RC_FROG_01",
            "RC_SCRIPT_STARTER_EMBERFOX": "SPECIES_RC_FIREFOX_01",
        }
        for script_id, species in expected.items():
            ops = scripts[script_id]["ops"]
            givemon_positions = [i for i, op in enumerate(ops) if op.get("op") == "givemon"]
            self.assertEqual(len(givemon_positions), 1, script_id)
            give_pos = givemon_positions[0]
            self.assertEqual(ops[give_pos]["species"], species)
            flag_positions = [
                i for i, op in enumerate(ops)
                if op.get("op") == "setflag" and op.get("flag") == "RC_FLAG_STARTER_CHOSEN"
            ]
            self.assertEqual(len(flag_positions), 1, script_id)
            self.assertGreater(flag_positions[0], give_pos, script_id)

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
            "custom_port_link_pending_smoke",
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
