from pathlib import Path
import importlib.util
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[1]
PATCHER = ROOT / "scripts" / "apply_release_candidate_preview_patch.py"


def load_patcher():
    spec = importlib.util.spec_from_file_location("rc_preview_patcher", PATCHER)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def build_preview_fixture(patcher):
    chunks = [
        b"RCFIXTURE", patcher.BULBASAUR_STARTER_SIGNATURE, b"|",
        patcher.SQUIRTLE_STARTER_SIGNATURE, b"|",
        patcher.CHARMANDER_STARTER_SIGNATURE, b"|",
        patcher.OAK_LAB_RIVAL_PARTIES_SIGNATURE,
    ]
    for old_text, _ in patcher.VISIBLE_TEXT_REPLACEMENTS:
        chunks.extend((b"|", old_text))
    chunks.extend((b"|", patcher.MAP_NAME_REPLACEMENT[0], b"|",
                   patcher.LAB_SIGN_REPLACEMENT[0], b"|",
                   patcher.ROUTE1_WILD_SIGNATURE, b"|END"))
    return b"".join(chunks)


def build_patched_fixture(patcher):
    payload = bytearray(build_preview_fixture(patcher))
    payload = patcher.patch_preview_starters(payload)
    payload, _ = patcher.patch_oak_lab_rival_parties(payload)
    payload, _, _, _ = patcher.patch_visible_preview_text(payload)
    return patcher.patch_route1_wild_encounters(payload)


class ReleaseCandidatePreviewPatchTest(unittest.TestCase):
    def test_wires_all_three_original_starters(self):
        patcher = load_patcher()
        payload = bytearray(
            b"prefix" + patcher.BULBASAUR_STARTER_SIGNATURE + b"|"
            + patcher.SQUIRTLE_STARTER_SIGNATURE + b"|"
            + patcher.CHARMANDER_STARTER_SIGNATURE + b"suffix"
        )
        patched = patcher.patch_preview_starters(payload)
        for signature, player_species, rival_species in (
            (patcher.BULBASAUR_STARTER_SIGNATURE, patcher.TARTREK_SPECIES_ID, patcher.EMBERFOX_SPECIES_ID),
            (patcher.SQUIRTLE_STARTER_SIGNATURE, patcher.FROBYTE_SPECIES_ID, patcher.TARTREK_SPECIES_ID),
            (patcher.CHARMANDER_STARTER_SIGNATURE, patcher.EMBERFOX_SPECIES_ID, patcher.FROBYTE_SPECIES_ID),
        ):
            expected = patcher.patched_starter_signature(
                signature, player_species, rival_species
            )
            self.assertEqual(patched.count(expected), 1)

    def test_starter_patch_fails_closed_when_a_slot_is_missing(self):
        patcher = load_patcher()
        payload = bytearray(patcher.BULBASAUR_STARTER_SIGNATURE + patcher.SQUIRTLE_STARTER_SIGNATURE)
        with self.assertRaisesRegex(ValueError, "Charmander starter"):
            patcher.patch_preview_starters(payload)

    def test_patches_oak_lab_rival_parties_to_original_species(self):
        patcher = load_patcher()
        payload = bytearray(b"prefix" + patcher.OAK_LAB_RIVAL_PARTIES_SIGNATURE + b"suffix")
        patched, applied = patcher.patch_oak_lab_rival_parties(payload)
        self.assertTrue(applied)
        base = len(b"prefix")
        expected = (patcher.FROBYTE_SPECIES_ID, patcher.TARTREK_SPECIES_ID, patcher.EMBERFOX_SPECIES_ID)
        for rel, species in zip(patcher.RIVAL_PARTY_SPECIES_OFFSETS, expected):
            self.assertEqual(patched[base + rel:base + rel + 2], species.to_bytes(2, "little"))

    def test_visible_preview_text_replacements_are_size_preserving(self):
        patcher = load_patcher()
        for old_text, new_text in patcher.VISIBLE_TEXT_REPLACEMENTS:
            self.assertLessEqual(len(new_text), len(old_text))

    def test_visible_preview_labels_are_patched(self):
        patcher = load_patcher()
        patched = build_patched_fixture(patcher)
        for old_text, new_text in patcher.VISIBLE_TEXT_REPLACEMENTS:
            self.assertIn(new_text, patched)
            self.assertNotIn(old_text, patched)
        self.assertIn(patcher.MAP_NAME_REPLACEMENT[1], patched)
        self.assertIn(patcher.LAB_SIGN_REPLACEMENT[1], patched)

    def test_route1_wild_table_matches_preview_distribution(self):
        patcher = load_patcher()
        payload = bytearray(b"prefix" + patcher.ROUTE1_WILD_SIGNATURE + b"suffix")
        patched = patcher.patch_route1_wild_encounters(payload)
        base = len(b"prefix")
        for record, species in enumerate(patcher.ROUTE1_PREVIEW_SPECIES):
            species_pos = base + (record * 4) + 2
            self.assertEqual(patched[species_pos:species_pos + 2], species.to_bytes(2, "little"))
        self.assertEqual(patcher.ROUTE1_PREVIEW_SPECIES.count(patcher.MISTRILLO_SPECIES_ID), 4)
        self.assertEqual(patcher.ROUTE1_PREVIEW_SPECIES.count(patcher.WINGULL_SPECIES_ID), 3)
        self.assertEqual(patcher.ROUTE1_PREVIEW_SPECIES.count(patcher.MEOWTH_SPECIES_ID), 5)

    def test_validator_accepts_complete_playable_contract(self):
        patcher = load_patcher()
        patcher.validate_preview_patch(build_patched_fixture(patcher))

    def test_validator_rejects_corrupted_starter_wiring(self):
        patcher = load_patcher()
        patched = build_patched_fixture(patcher)
        expected = patcher.patched_starter_signature(
            patcher.BULBASAUR_STARTER_SIGNATURE,
            patcher.TARTREK_SPECIES_ID,
            patcher.EMBERFOX_SPECIES_ID,
        )
        pos = patched.find(expected)
        patched[pos + patcher.PLAYER_SPECIES_VALUE_OFFSET:pos + patcher.PLAYER_SPECIES_VALUE_OFFSET + 2] = b"\x01\x00"
        with self.assertRaisesRegex(RuntimeError, "Tartrek starter wiring"):
            patcher.validate_preview_patch(patched)

    def test_validator_rejects_corrupted_rival_party(self):
        patcher = load_patcher()
        patched = build_patched_fixture(patcher)
        party = b"".join(b"\x00\x00\x05\x00" + s.to_bytes(2, "little") for s in (patcher.FROBYTE_SPECIES_ID, patcher.TARTREK_SPECIES_ID, patcher.EMBERFOX_SPECIES_ID))
        pos = patched.find(party)
        patched[pos + 4:pos + 6] = b"\x07\x00"
        with self.assertRaisesRegex(RuntimeError, "KPI-rival party"):
            patcher.validate_preview_patch(patched)

    def test_validator_rejects_corrupted_port_link_encounter(self):
        patcher = load_patcher()
        patched = build_patched_fixture(patcher)
        expected = bytearray(patcher.ROUTE1_WILD_SIGNATURE)
        for record, species in enumerate(patcher.ROUTE1_PREVIEW_SPECIES):
            expected[record * 4 + 2:record * 4 + 4] = species.to_bytes(2, "little")
        pos = patched.find(expected)
        patched[pos + 2:pos + 4] = b"\x10\x00"
        with self.assertRaisesRegex(RuntimeError, "Port Link custom encounter"):
            patcher.validate_preview_patch(patched)

    def test_file_patch_preserves_input_and_writes_complete_preview(self):
        patcher = load_patcher()
        with tempfile.TemporaryDirectory() as tmp:
            tmp = Path(tmp)
            source, output = tmp / "input.gba", tmp / "output.gba"
            original = build_preview_fixture(patcher)
            source.write_bytes(original)
            patcher.patch_rom(source, output)
            patched = output.read_bytes()
            self.assertEqual(source.read_bytes(), original)
            self.assertNotEqual(patched, original)
            self.assertEqual(len(patched), len(original))
            patcher.validate_preview_patch(bytearray(patched))


if __name__ == "__main__":
    unittest.main()
