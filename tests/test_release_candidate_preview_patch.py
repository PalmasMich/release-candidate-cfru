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
        b"RCFIXTURE",
        patcher.BULBASAUR_STARTER_SIGNATURE,
        b"|",
        patcher.SQUIRTLE_STARTER_SIGNATURE,
        b"|",
        patcher.CHARMANDER_STARTER_SIGNATURE,
        b"|",
        patcher.OAK_LAB_RIVAL_PARTIES_SIGNATURE,
    ]
    for old_text, _ in patcher.VISIBLE_TEXT_REPLACEMENTS:
        chunks.extend((b"|", old_text))
    chunks.extend(
        (
            b"|",
            patcher.MAP_NAME_REPLACEMENT[0],
            b"|",
            patcher.LAB_SIGN_REPLACEMENT[0],
            b"|",
            patcher.ROUTE1_WILD_SIGNATURE,
            b"|END",
        )
    )
    return b"".join(chunks)


class ReleaseCandidatePreviewPatchTest(unittest.TestCase):
    def test_wires_all_three_original_starters(self):
        patcher = load_patcher()
        payload = bytearray(
            b"prefix"
            + patcher.BULBASAUR_STARTER_SIGNATURE
            + b"|"
            + patcher.SQUIRTLE_STARTER_SIGNATURE
            + b"|"
            + patcher.CHARMANDER_STARTER_SIGNATURE
            + b"suffix"
        )
        patched = patcher.patch_preview_starters(payload)
        for signature, player_species, rival_species in (
            (patcher.BULBASAUR_STARTER_SIGNATURE, patcher.TARTREK_SPECIES_ID, patcher.EMBERFOX_SPECIES_ID),
            (patcher.SQUIRTLE_STARTER_SIGNATURE, patcher.FROBYTE_SPECIES_ID, patcher.TARTREK_SPECIES_ID),
            (patcher.CHARMANDER_STARTER_SIGNATURE, patcher.EMBERFOX_SPECIES_ID, patcher.FROBYTE_SPECIES_ID),
        ):
            # The source signature has been changed, so locate the immutable
            # starter-index prefix and verify both species vars.
            prefix = signature[:5]
            pos = patched.find(prefix)
            self.assertGreaterEqual(pos, 0)
            self.assertEqual(
                patched[pos + patcher.PLAYER_SPECIES_VALUE_OFFSET:pos + patcher.PLAYER_SPECIES_VALUE_OFFSET + 2],
                player_species.to_bytes(2, "little"),
            )
            self.assertEqual(
                patched[pos + patcher.RIVAL_SPECIES_VALUE_OFFSET:pos + patcher.RIVAL_SPECIES_VALUE_OFFSET + 2],
                rival_species.to_bytes(2, "little"),
            )

    def test_patches_oak_lab_rival_parties_to_original_species(self):
        patcher = load_patcher()
        payload = bytearray(b"prefix" + patcher.OAK_LAB_RIVAL_PARTIES_SIGNATURE + b"suffix")
        patched = patcher.patch_oak_lab_rival_parties(payload)
        base = len(b"prefix")
        expected = (patcher.FROBYTE_SPECIES_ID, patcher.TARTREK_SPECIES_ID, patcher.EMBERFOX_SPECIES_ID)
        for rel, species in zip(patcher.RIVAL_PARTY_SPECIES_OFFSETS, expected):
            self.assertEqual(
                patched[base + rel:base + rel + 2],
                species.to_bytes(2, "little"),
            )

    def test_replaces_bulbasaur_slot_with_tartrek(self):
        patcher = load_patcher()
        payload = bytearray(b"prefix" + patcher.BULBASAUR_STARTER_SIGNATURE + b"suffix")
        patched, count = patcher.patch_tartrek_starter(payload)
        self.assertEqual(count, 1)

        start = len(b"prefix")
        species_offset = start + patcher.PLAYER_SPECIES_VALUE_OFFSET
        self.assertEqual(
            patched[species_offset:species_offset + 2],
            patcher.TARTREK_SPECIES_ID.to_bytes(2, "little"),
        )

    def test_requires_exactly_one_starter_signature(self):
        patcher = load_patcher()
        with self.assertRaisesRegex(ValueError, "exactly one"):
            patcher.patch_tartrek_starter(bytearray(b"no starter script here"))

    def test_visible_preview_text_replacements_are_size_preserving(self):
        patcher = load_patcher()
        for old_text, new_text in patcher.VISIBLE_TEXT_REPLACEMENTS:
            self.assertLessEqual(len(new_text), len(old_text))

    def test_visible_preview_labels_are_patched(self):
        patcher = load_patcher()
        payload = bytearray(build_preview_fixture(patcher))
        patched, _ = patcher.patch_tartrek_starter(payload)
        patched = patcher.patch_visible_preview_text(patched)
        for old_text, new_text in patcher.VISIBLE_TEXT_REPLACEMENTS:
            self.assertIn(new_text, patched)
            self.assertNotIn(old_text, patched)
        self.assertIn(patcher.MAP_NAME_REPLACEMENT[1], patched)
        self.assertIn(patcher.LAB_SIGN_REPLACEMENT[1], patched)

    def test_route1_wild_table_injects_mistrillo(self):
        patcher = load_patcher()
        payload = bytearray(b"prefix" + patcher.ROUTE1_WILD_SIGNATURE + b"suffix")
        patched = patcher.patch_route1_wild_encounters(payload)
        base = len(b"prefix")
        for record, species in enumerate(patcher.ROUTE1_PREVIEW_SPECIES):
            species_pos = base + (record * 4) + 2
            self.assertEqual(
                patched[species_pos:species_pos + 2],
                species.to_bytes(2, "little"),
            )

    def test_route1_preview_mix_matches_manifest_weights(self):
        patcher = load_patcher()
        self.assertEqual(patcher.ROUTE1_PREVIEW_SPECIES.count(patcher.MISTRILLO_SPECIES_ID), 4)
        self.assertEqual(patcher.ROUTE1_PREVIEW_SPECIES.count(patcher.WINGULL_SPECIES_ID), 3)
        self.assertEqual(patcher.ROUTE1_PREVIEW_SPECIES.count(patcher.MEOWTH_SPECIES_ID), 5)

    def test_file_patch_preserves_input_and_writes_complete_preview(self):
        patcher = load_patcher()
        with tempfile.TemporaryDirectory() as tmp:
            tmp = Path(tmp)
            source = tmp / "input.gba"
            output = tmp / "output.gba"
            original = build_preview_fixture(patcher)
            source.write_bytes(original)

            patcher.patch_rom(source, output)
            patched = output.read_bytes()

            self.assertEqual(source.read_bytes(), original)
            self.assertNotEqual(patched, original)
            self.assertEqual(len(patched), len(original))
            self.assertIn(patcher.TARTREK_SPECIES_ID.to_bytes(2, "little"), patched)
            self.assertIn(patcher.MISTRILLO_SPECIES_ID.to_bytes(2, "little"), patched)
            self.assertIn(patcher.MAP_NAME_REPLACEMENT[1], patched)
            self.assertIn(patcher.LAB_SIGN_REPLACEMENT[1], patched)


if __name__ == "__main__":
    unittest.main()
