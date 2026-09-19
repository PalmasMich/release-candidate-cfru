from pathlib import Path
import importlib.util
import unittest

ROOT = Path(__file__).resolve().parents[1]
SCRIPT = ROOT / "scripts" / "compile_rc_dialogue.py"


def load_compiler():
    spec = importlib.util.spec_from_file_location("rc_dialogue_compiler", SCRIPT)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


class RcDialogueCompilerTest(unittest.TestCase):
    def test_encodes_italian_accents_with_verified_charmap(self):
        module = load_compiler()
        self.assertEqual(
            module.encode_text("àèéìòù"),
            bytes([0x16, 0x1A, 0x1B, 0x1E, 0x22, 0x26]),
        )

    def test_scene_joins_manifest_lines_with_newline_and_eos(self):
        module = load_compiler()
        scene = {
            "id": "RC_TEST",
            "speaker": "System",
            "lines": ["Prima riga.", "Seconda riga."],
        }

        compiled = module.compile_scene(scene)
        blob = bytes.fromhex(compiled["bytes_hex"])

        self.assertEqual(blob[-1], 0xFF)
        self.assertEqual(blob.count(bytes([0xFE])), 1)

    def test_all_current_cagliari_dialogue_compiles(self):
        module = load_compiler()
        ir = module.compile_file()
        ids = {scene["id"] for scene in ir["scenes"]}

        self.assertEqual(ir["format"], "RC_DIALOGUE_IR_V1")
        self.assertIn("RC_DIALOGUE_STARTER_TARTREK_CONFIRM", ids)
        self.assertIn("RC_DIALOGUE_STARTER_FROBYTE_CONFIRM", ids)
        self.assertIn("RC_DIALOGUE_STARTER_EMBERFOX_CONFIRM", ids)
        self.assertIn("RC_DIALOGUE_RIVAL_REPEAT", ids)

    def test_rejects_unknown_character_instead_of_silent_replacement(self):
        module = load_compiler()
        with self.assertRaisesRegex(ValueError, "unsupported FireRed text character"):
            module.encode_text("Test €")


if __name__ == "__main__":
    unittest.main()
