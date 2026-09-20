from pathlib import Path
import importlib.util
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[1]
PATCHER = ROOT / "scripts" / "apply_release_candidate_preview_patch.py"

def load_patcher():
    spec=importlib.util.spec_from_file_location("rc_preview_patcher",PATCHER); module=importlib.util.module_from_spec(spec); spec.loader.exec_module(module); return module

def build_preview_fixture(p):
    chunks=[b"RCFIXTURE",p.BULBASAUR_STARTER_SIGNATURE,b"|",p.SQUIRTLE_STARTER_SIGNATURE,b"|",p.CHARMANDER_STARTER_SIGNATURE,b"|",p.OAK_LAB_RIVAL_PARTIES_SIGNATURE]
    for old,_ in p.VISIBLE_TEXT_REPLACEMENTS: chunks.extend((b"|",old))
    chunks.extend((b"|",p.MAP_NAME_REPLACEMENT[0],b"|",p.LAB_SIGN_REPLACEMENT[0],b"|",p.ROUTE1_WILD_SIGNATURE,b"|END")); return b"".join(chunks)

def build_patched_fixture(p):
    payload=p.patch_preview_starters(bytearray(build_preview_fixture(p))); payload,_=p.patch_oak_lab_rival_parties(payload); payload,_,_,_=p.patch_visible_preview_text(payload); return p.patch_route1_wild_encounters(payload)

class ReleaseCandidatePreviewPatchTest(unittest.TestCase):
    def test_wires_all_three_original_starters(self):
        p=load_patcher(); payload=bytearray(b"prefix"+p.BULBASAUR_STARTER_SIGNATURE+b"|"+p.SQUIRTLE_STARTER_SIGNATURE+b"|"+p.CHARMANDER_STARTER_SIGNATURE+b"suffix"); patched=p.patch_preview_starters(payload)
        for signature,player,rival in ((p.BULBASAUR_STARTER_SIGNATURE,p.TARTREK_SPECIES_ID,p.EMBERFOX_SPECIES_ID),(p.SQUIRTLE_STARTER_SIGNATURE,p.FROBYTE_SPECIES_ID,p.TARTREK_SPECIES_ID),(p.CHARMANDER_STARTER_SIGNATURE,p.EMBERFOX_SPECIES_ID,p.FROBYTE_SPECIES_ID)): self.assertEqual(patched.count(p.patched_starter_signature(signature,player,rival)),1)

    def test_starter_patch_fails_closed_when_a_slot_is_missing(self):
        p=load_patcher()
        with self.assertRaisesRegex(ValueError,"Charmander starter"): p.patch_preview_starters(bytearray(p.BULBASAUR_STARTER_SIGNATURE+p.SQUIRTLE_STARTER_SIGNATURE))

    def test_patches_oak_lab_rival_parties_to_original_species(self):
        p=load_patcher(); patched,applied=p.patch_oak_lab_rival_parties(bytearray(b"prefix"+p.OAK_LAB_RIVAL_PARTIES_SIGNATURE+b"suffix")); self.assertTrue(applied); base=len(b"prefix")
        for rel,species in zip(p.RIVAL_PARTY_SPECIES_OFFSETS,(p.FROBYTE_SPECIES_ID,p.TARTREK_SPECIES_ID,p.EMBERFOX_SPECIES_ID)): self.assertEqual(patched[base+rel:base+rel+2],species.to_bytes(2,"little"))

    def test_visible_preview_text_replacements_are_size_preserving(self):
        p=load_patcher()
        for old,new in p.VISIBLE_TEXT_REPLACEMENTS: self.assertLessEqual(len(new),len(old))

    def test_visible_preview_labels_are_patched(self):
        p=load_patcher(); patched=build_patched_fixture(p)
        for old,new in p.VISIBLE_TEXT_REPLACEMENTS: self.assertIn(new,patched); self.assertNotIn(old,patched)
        self.assertIn(p.MAP_NAME_REPLACEMENT[1],patched); self.assertIn(p.LAB_SIGN_REPLACEMENT[1],patched)

    def test_thick_preview_exposes_cagliari_corporate_identity(self):
        p=load_patcher(); patched=build_patched_fixture(p)
        for text in ("Welcome to Release Candidate!","YOUR ID?","TEAMMATE ID?","LEAD: Hey! Wait!\nNo field test yet!","LEAD: Scope changed!\nField checks start today!","You need a resource for\nthe Port Link test.","Come on!\nDelivery Hub, now!","CAGLIARI\nFirst sprint starts here!","Delivery is incredible!","DELIVERY HUB - CAGLIARI","Three resources are ready.","I don't chase metrics.\nI just happen to lead them.","Let's benchmark our resources!","KPI check: show velocity!","KPI is GREEN!","See you at stand-up!","PORT LINK\nCAGLIARI - MARINA PORTO","See those shortcuts on Port Link?","MARINA PORTO \nDEPLOY BLOCKED - CHECK SCOPE","This deploy gate is still closed.","Stakeholder approval pending.","This scope is out of bounds!","Time is budget. Keep meetings\nshort and useful.","MARINA PORTO DEPLOY GATE","DEPLOY GATE locked: scope open."): self.assertIn(p.encode_text(text),patched)

    def test_required_identity_gate_covers_preview_pillars(self):
        p=load_patcher(); expected={p.encode_text(x) for x in ("Welcome to Release Candidate!","LEAD: Scope changed!\nField checks start today!","CAGLIARI\nFirst sprint starts here!","DELIVERY HUB - CAGLIARI","Three resources are ready.","Let's benchmark our resources!","KPI check: show velocity!","PORT LINK\nCAGLIARI - MARINA PORTO","MARINA PORTO \nDEPLOY BLOCKED - CHECK SCOPE","MARINA PORTO DEPLOY GATE")}; self.assertEqual(set(p.REQUIRED_VISIBLE_TEXTS),expected)

    def test_route1_wild_table_matches_preview_distribution_and_levels(self):
        p=load_patcher(); patched=p.patch_route1_wild_encounters(bytearray(b"prefix"+p.ROUTE1_WILD_SIGNATURE+b"suffix")); base=len(b"prefix")
        for record,(species,levels) in enumerate(zip(p.ROUTE1_PREVIEW_SPECIES,p.ROUTE1_PREVIEW_LEVELS)):
            pos=base+record*4; self.assertEqual(patched[pos:pos+2],bytes(levels)); self.assertEqual(patched[pos+2:pos+4],species.to_bytes(2,"little"))
        weighted={}
        for species,weight in zip(p.ROUTE1_PREVIEW_SPECIES,p.GRASS_SLOT_WEIGHTS): weighted[species]=weighted.get(species,0)+weight
        self.assertEqual((weighted[p.MISTRILLO_SPECIES_ID],weighted[p.WINGULL_SPECIES_ID],weighted[p.MEOWTH_SPECIES_ID]),(60,25,15))

    def test_validator_accepts_complete_playable_contract(self):
        p=load_patcher(); p.validate_preview_patch(build_patched_fixture(p))

    def test_file_patch_preserves_input_and_writes_complete_preview(self):
        p=load_patcher()
        with tempfile.TemporaryDirectory() as tmp:
            tmp=Path(tmp); source=tmp/"input.gba"; output=tmp/"output.gba"; original=build_preview_fixture(p); source.write_bytes(original); p.patch_rom(source,output); patched=output.read_bytes(); self.assertEqual(source.read_bytes(),original); self.assertNotEqual(patched,original); self.assertEqual(len(patched),len(original)); p.validate_preview_patch(bytearray(patched))

if __name__ == "__main__": unittest.main()
