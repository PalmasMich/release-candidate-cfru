from pathlib import Path
import importlib.util
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[1]
BUILD_SCRIPT = ROOT / "scripts" / "build_release_candidate.py"
SOURCE_TABLE = ROOT / "src" / "Tables" / "level_up_learnsets.c"


def load_builder():
    spec = importlib.util.spec_from_file_location("rc_builder", BUILD_SCRIPT)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


class RCLearnsetActivationTest(unittest.TestCase):
    def test_transactional_activation_adds_tartrek_to_active_pointer_tail(self):
        builder = load_builder()
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            table = root / builder.RC_LEARNSET_TABLE
            table.parent.mkdir(parents=True)
            source = (
                "\t[SPECIES_RC_TURTLE_01] = sRCTartrekLevelUpLearnset,\n"
                "};\n*/\n"
                "\t[SPECIES_RC_CAGLIARI_WILD_01] = sRCMistrilloLevelUpLearnset,\n"
                "\t[SPECIES_RC_FROG_01] = sRCFrobyteLevelUpLearnset,\n"
                "\t[SPECIES_RC_FIREFOX_01] = sRCEmberfoxLevelUpLearnset,\n"
                "};\n\n#endif"
            )
            table.write_text(source, encoding="utf-8")

            original = builder.activate_rc_learnset_pointers(root)
            patched = table.read_text(encoding="utf-8")

            self.assertEqual(original, source.encode("utf-8"))
            active_tail = patched.split("*/\n", 1)[1]
            for pointer in (
                "[SPECIES_RC_TURTLE_01] = sRCTartrekLevelUpLearnset",
                "[SPECIES_RC_CAGLIARI_WILD_01] = sRCMistrilloLevelUpLearnset",
                "[SPECIES_RC_FROG_01] = sRCFrobyteLevelUpLearnset",
                "[SPECIES_RC_FIREFOX_01] = sRCEmberfoxLevelUpLearnset",
            ):
                self.assertEqual(active_tail.count(pointer), 1, pointer)

            table.write_bytes(original)
            self.assertEqual(table.read_bytes(), source.encode("utf-8"))

    def test_activation_fails_closed_if_generated_tail_changes(self):
        builder = load_builder()
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            table = root / builder.RC_LEARNSET_TABLE
            table.parent.mkdir(parents=True)
            table.write_text("unexpected generated table", encoding="utf-8")
            with self.assertRaisesRegex(RuntimeError, "RC learnset pointer tail"):
                builder.activate_rc_learnset_pointers(root)

    def test_level_five_preview_species_have_usable_moves(self):
        text = SOURCE_TABLE.read_text(encoding="utf-8")
        expected = {
            "sRCTartrekLevelUpLearnset": ("MOVE_TACKLE", "MOVE_WITHDRAW", "MOVE_VINEWHIP"),
            "sRCFrobyteLevelUpLearnset": ("MOVE_POUND", "MOVE_GROWL", "MOVE_WATERGUN"),
            "sRCEmberfoxLevelUpLearnset": ("MOVE_SCRATCH", "MOVE_TAILWHIP", "MOVE_EMBER"),
            "sRCMistrilloLevelUpLearnset": ("MOVE_GUST", "MOVE_GROWL", "MOVE_QUICKATTACK"),
        }
        for learnset, moves in expected.items():
            start = text.index(f"static const struct LevelUpMove {learnset}[]")
            end = text.index("};", start)
            block = text[start:end]
            for move in moves:
                self.assertIn(move, block, f"{learnset} missing {move}")


if __name__ == "__main__":
    unittest.main()
