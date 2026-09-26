from pathlib import Path
import importlib.util
import sys
import unittest

ROOT = Path(__file__).resolve().parents[1]
SCRIPTS = ROOT / "scripts"
PATCHER = SCRIPTS / "patch_rc_intro_bypass.py"


def load_module():
    sys.path.insert(0, str(SCRIPTS))
    try:
        spec = importlib.util.spec_from_file_location("rc_intro_bypass_patcher", PATCHER)
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)
        return module
    finally:
        sys.path.remove(str(SCRIPTS))


def fixture(module):
    prompt = module.encode_text(module.PROMPT)
    anchor = 0x400
    prompt_offset = 0x700
    data = bytearray(b"\x00" * 0x1000)
    data[prompt_offset:prompt_offset + len(prompt)] = prompt
    data[anchor:anchor + 4] = (module.ROM_BASE + prompt_offset).to_bytes(4, "little")

    source_literal = anchor + module.SOURCE_LITERAL_DELTA
    reshow_literal = anchor + module.RESHOW_LITERAL_DELTA
    fade_in_entry = anchor + module.FADE_IN_ENTRY_DELTA
    reshow_entry = anchor + module.RESHOW_ENTRY_DELTA

    data[source_literal:source_literal + 4] = (
        module.ROM_BASE + fade_in_entry + 1
    ).to_bytes(4, "little")
    data[reshow_literal:reshow_literal + 4] = (
        module.ROM_BASE + reshow_entry + 1
    ).to_bytes(4, "little")
    return bytes(data), source_literal, module.ROM_BASE + reshow_entry + 1


class IntroBypassPatchTest(unittest.TestCase):
    def test_patches_fadeout_player_continuation_to_reshow(self):
        module = load_module()
        data, source_literal, expected_target = fixture(module)
        patched = module.apply_bypass(data)
        self.assertEqual(
            int.from_bytes(patched[source_literal:source_literal + 4], "little"),
            expected_target,
        )
        module.verify_bypass(patched)

    def test_fails_closed_on_unexpected_source_pointer(self):
        module = load_module()
        data, source_literal, _ = fixture(module)
        broken = bytearray(data)
        broken[source_literal:source_literal + 4] = (0x08123457).to_bytes(4, "little")
        with self.assertRaisesRegex(RuntimeError, "unexpected FadeOutPlayerPic"):
            module.apply_bypass(bytes(broken))

    def test_verify_rejects_unpatched_fixture(self):
        module = load_module()
        data, _, _ = fixture(module)
        with self.assertRaisesRegex(RuntimeError, "structural rival-name bypass"):
            module.verify_bypass(data)


if __name__ == "__main__":
    unittest.main()
