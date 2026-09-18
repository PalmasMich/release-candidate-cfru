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
