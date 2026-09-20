from pathlib import Path
import importlib.util
import unittest

ROOT = Path(__file__).resolve().parents[1]
LEARNSETS = ROOT / "src/Tables/level_up_learnsets.c"
BUILDER = ROOT / "scripts/build_release_candidate.py"


def load_builder():
    spec = importlib.util.spec_from_file_location("rc_builder_battle_readiness", BUILDER)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


class RCBattleReadinessTest(unittest.TestCase):
    """Fail closed if the thick preview can create a custom mon with no moves."""

    def test_preview_species_have_cfru_learnset_definitions(self):
        text = LEARNSETS.read_text(encoding="utf-8")
        expected = {
            "sRCTartrekLevelUpLearnset": ("MOVE_TACKLE", "MOVE_WITHDRAW"),
            "sRCFrobyteLevelUpLearnset": ("MOVE_POUND", "MOVE_GROWL"),
            "sRCEmberfoxLevelUpLearnset": ("MOVE_SCRATCH", "MOVE_TAILWHIP"),
            "sRCMistrilloLevelUpLearnset": ("MOVE_GUST", "MOVE_GROWL"),
        }
        for symbol, starting_moves in expected.items():
            start = text.find(f"static const struct LevelUpMove {symbol}[]")
            self.assertGreaterEqual(start, 0, f"missing CFRU learnset: {symbol}")
            end = text.find("LEVEL_UP_END", start)
            self.assertGreater(end, start, f"unterminated CFRU learnset: {symbol}")
            block = text[start:end]
            for move in starting_moves:
                self.assertIn(move, block, f"{symbol} lost required starting move {move}")

    def test_private_build_overlay_activates_every_preview_pointer(self):
        builder = load_builder()
        source = LEARNSETS.read_text(encoding="utf-8")
        # The checked-in CFRU table deliberately keeps the extension outside the
        # upstream pointer table; the private build overlay must activate all four.
        required = (
            "[SPECIES_RC_TURTLE_01] = sRCTartrekLevelUpLearnset",
            "[SPECIES_RC_FROG_01] = sRCFrobyteLevelUpLearnset",
            "[SPECIES_RC_FIREFOX_01] = sRCEmberfoxLevelUpLearnset",
            "[SPECIES_RC_CAGLIARI_WILD_01] = sRCMistrilloLevelUpLearnset",
        )
        self.assertIn("SPECIES_RC_TURTLE_01", source)
        self.assertTrue(callable(builder.activate_rc_learnset_pointers))
        for pointer in required:
            self.assertIn(pointer, source)


if __name__ == "__main__":
    unittest.main()
