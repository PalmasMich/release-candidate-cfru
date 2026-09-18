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


class ReleaseCandidatePreviewPatchTest(unittest.TestCase):
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
        old_choice, new_choice = patcher.VISIBLE_TEXT_REPLACEMENTS[0]
        old_city, new_city = patcher.MAP_NAME_REPLACEMENT
        payload = bytearray(b"prefix" + old_choice + b"middle" + old_city + b"suffix")
        patched = patcher.patch_visible_preview_text(payload)
        self.assertIn(new_choice, patched)
        self.assertIn(new_city, patched)
        self.assertNotIn(old_choice, patched)

    def test_route1_wild_table_injects_mistrillo(self):
        patcher = load_patcher()
        payload = bytearray(b"prefix" + patcher.ROUTE1_WILD_SIGNATURE + b"suffix")
        patched = patcher.patch_route1_wild_encounters(payload)
        self.assertIn(patcher.MISTRILLO_SPECIES_ID.to_bytes(2, "little"), patched)
        self.assertNotEqual(
            patched[len(b"prefix"):len(b"prefix") + len(patcher.ROUTE1_WILD_SIGNATURE)],
            patcher.ROUTE1_WILD_SIGNATURE,
        )

    def test_file_patch_preserves_input_and_writes_output(self):
        patcher = load_patcher()
        with tempfile.TemporaryDirectory() as tmp:
            tmp = Path(tmp)
            source = tmp / "input.gba"
            output = tmp / "output.gba"
            original = b"prefix" + patcher.BULBASAUR_STARTER_SIGNATURE + b"suffix"
            source.write_bytes(original)

            patcher.patch_rom(source, output)

            self.assertEqual(source.read_bytes(), original)
            self.assertNotEqual(output.read_bytes(), original)
            self.assertEqual(len(output.read_bytes()), len(original))


if __name__ == "__main__":
    unittest.main()
