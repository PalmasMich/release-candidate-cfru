from pathlib import Path
import json
import unittest

ROOT = Path(__file__).resolve().parents[1]
CONTENT = ROOT / "content" / "cagliari_preview"

def load(name): return json.loads((CONTENT / name).read_text(encoding="utf-8"))
def load_map_spec(name): return json.loads((CONTENT / "map_specs" / name).read_text(encoding="utf-8"))
def load_script_spec(name): return json.loads((CONTENT / "script_specs" / name).read_text(encoding="utf-8"))

class CagliariPreviewContentContractTest(unittest.TestCase):
    def test_map_graph_references_existing_maps(self):
        maps=load("maps.yml")["maps"]; ids={item["id"] for item in maps}; self.assertIn("RC_DELIVERY_HUB",ids); self.assertIn("RC_PORT_CONNECTION",ids)
        for item in maps:
            for target in item.get("connects_to",[]): self.assertIn(target,ids,f"{item['id']} points to missing map {target}")

    def test_thick_preview_route_is_connected_hub_to_first_field_test(self):
        maps={item["id"]:item for item in load("maps.yml")["maps"]}; self.assertIn("RC_CAGLIARI_MARINA",maps["RC_DELIVERY_HUB"]["connects_to"]); self.assertIn("RC_PORT_CONNECTION",maps["RC_CAGLIARI_MARINA"]["connects_to"]); self.assertEqual(maps["RC_PORT_CONNECTION"]["bootstrap_source"],"FIRERED_ROUTE_1")

    def test_story_dialogue_references_exist(self):
        dialogue_ids={scene["id"] for scene in load("dialogue.yml")["scenes"]}; trainers=load("trainers.yml")
        for key in ("intro_dialogue","outro_dialogue"):
            for trainer in trainers.values():
                if key in trainer: self.assertIn(trainer[key],dialogue_ids)
        required={"RC_DIALOGUE_OPENING","RC_DIALOGUE_STARTER","RC_DIALOGUE_RIVAL_INTRO","RC_DIALOGUE_WILD_TUTORIAL_TRIGGER","RC_DIALOGUE_FIELD_TEST_NEEDS_PARTNER","RC_DIALOGUE_PORT_LINK_HINT","RC_DIALOGUE_DEPLOY_TEASER"}; self.assertTrue(required<=dialogue_ids)

    def test_preview_species_symbols_are_consistent(self):
        custom={"SPECIES_RC_TURTLE_01","SPECIES_RC_FROG_01","SPECIES_RC_FIREFOX_01","SPECIES_RC_CAGLIARI_WILD_01"}; trainers=load("trainers.yml"); matrix=trainers["rival"]["starter_matrix"]; starters=custom-{"SPECIES_RC_CAGLIARI_WILD_01"}; self.assertEqual(set(matrix),starters); self.assertEqual(set(matrix.values()),starters); self.assertTrue(all(p!=r for p,r in matrix.items())); self.assertEqual(trainers["rival"]["preview_level"],5)
        for trainer in (trainers["route_trainer"],trainers["release_manager"]):
            for mon in trainer.get("party",trainer.get("desired_party",[])):
                if mon["species"].startswith("SPECIES_RC_"): self.assertIn(mon["species"],custom)
        for table in load("encounters.yml")["tables"]:
            for slot in table["slots"]:
                if slot["species"].startswith("SPECIES_RC_"): self.assertIn(slot["species"],custom)

    def test_port_link_encounter_contract_is_complete(self):
        table=load("encounters.yml")["tables"][0]; self.assertEqual(table["map"],"RC_PORT_CONNECTION"); self.assertEqual(sum(slot["weight"] for slot in table["slots"]),100); mistrillo=next(slot for slot in table["slots"] if slot["species"]=="SPECIES_RC_CAGLIARI_WILD_01"); self.assertEqual(mistrillo,{"species":"SPECIES_RC_CAGLIARI_WILD_01","min_level":3,"max_level":5,"weight":60})

    def test_first_field_test_is_guarded_and_one_shot(self):
        port_map=load_map_spec("RC_PORT_CONNECTION.json"); trigger=next(event for event in port_map["coord_events"] if event["id"]=="RC_COORD_FIRST_FIELD_TEST"); self.assertEqual(trigger["var_id"],"0x0000"); self.assertEqual(trigger["script"],"RC_SCRIPT_WILD_TUTORIAL_TRIGGER")
        scripts=load_script_spec("RC_PORT_CONNECTION.json")["scripts"]; wild=next(script for script in scripts if script["id"]=="RC_SCRIPT_WILD_TUTORIAL_TRIGGER"); ops=wild["ops"]
        self.assertIn({"op":"checkflag","flag":"RC_FLAG_WILD_TUTORIAL_DONE"},ops); self.assertIn({"op":"checkflag","flag":"RC_FLAG_STARTER_CHOSEN"},ops); self.assertIn({"op":"goto_if","condition":False,"label":"no_partner"},ops); self.assertIn({"op":"msgbox","dialogue":"RC_DIALOGUE_FIELD_TEST_NEEDS_PARTNER","type":4},ops); self.assertIn({"op":"setwildbattle","species":"SPECIES_RC_CAGLIARI_WILD_01","level":3},ops); self.assertIn({"op":"dowildbattle"},ops); self.assertIn({"op":"setflag","flag":"RC_FLAG_WILD_TUTORIAL_DONE"},ops)

if __name__=="__main__": unittest.main()
