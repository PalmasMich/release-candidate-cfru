from pathlib import Path
import importlib.util
import unittest

ROOT = Path(__file__).resolve().parents[1]
PATCHER = ROOT / "scripts" / "apply_release_candidate_preview_patch.py"


def load_patcher():
    spec = importlib.util.spec_from_file_location("rc_preview_text_codec", PATCHER)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


class ReleaseCandidateTextCodecTest(unittest.TestCase):
    def test_player_placeholder_uses_firered_control_bytes(self):
        patcher = load_patcher()
        self.assertEqual(patcher.encode_text("{PLAYER}"), b"\xFD\x01")

    def test_rival_placeholder_uses_firered_control_bytes(self):
        patcher = load_patcher()
        self.assertEqual(patcher.encode_text("{RIVAL}"), b"\xFD\x06")

    def test_mixed_dynamic_dialogue_is_encoded_without_literal_braces(self):
        patcher = load_patcher()
        encoded = patcher.encode_text("{RIVAL}: KPI check, {PLAYER}!")
        self.assertTrue(encoded.startswith(b"\xFD\x06"))
        self.assertIn(b"\xFD\x01", encoded)
        self.assertNotIn(b"{", encoded)
        self.assertNotIn(b"}", encoded)

    def test_every_preview_replacement_is_size_safe(self):
        patcher = load_patcher()
        for old, new in patcher.VISIBLE_TEXT_REPLACEMENTS:
            self.assertLessEqual(len(new), len(old))


if __name__ == "__main__":
    unittest.main()
