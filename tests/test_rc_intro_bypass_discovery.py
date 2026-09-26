from pathlib import Path
import importlib.util
import sys
import unittest

ROOT = Path(__file__).resolve().parents[1]
SCRIPTS = ROOT / "scripts"
DISCOVERY = SCRIPTS / "discover_rc_intro_bypass.py"


def load_module():
    sys.path.insert(0, str(SCRIPTS))
    try:
        spec = importlib.util.spec_from_file_location("rc_intro_bypass_discovery", DISCOVERY)
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)
        return module
    finally:
        sys.path.remove(str(SCRIPTS))


class IntroBypassDiscoveryTest(unittest.TestCase):
    def test_discovers_unique_prompt_and_pointer_reference(self):
        module = load_module()
        prompt = module.encode_text(module.PROMPT)
        prompt_offset = 0x240
        data = bytearray(b"\x00" * 0x600)
        data[prompt_offset:prompt_offset + len(prompt)] = prompt
        ptr_offset = 0x100
        ptr = (module.ROM_BASE + prompt_offset).to_bytes(4, "little")
        data[ptr_offset:ptr_offset + 4] = ptr

        found_offset, refs = module.discover_prompt_pointer_refs(bytes(data))

        self.assertEqual(found_offset, prompt_offset)
        self.assertEqual([ref.literal_offset for ref in refs], [ptr_offset])

    def test_rejects_ambiguous_prompt(self):
        module = load_module()
        prompt = module.encode_text(module.PROMPT)
        data = prompt + b"|" + prompt
        with self.assertRaisesRegex(RuntimeError, "exactly one"):
            module.discover_prompt_pointer_refs(data)

    def test_collects_nearby_thumb_literals_only(self):
        module = load_module()
        data = bytearray(b"\x00" * 0x400)
        center = 0x180
        thumb_ptr = 0x08123457
        even_rom_ptr = 0x08123456
        data[0x140:0x144] = thumb_ptr.to_bytes(4, "little")
        data[0x144:0x148] = even_rom_ptr.to_bytes(4, "little")

        values = module.nearby_thumb_literals(bytes(data), center)

        self.assertIn((0x140, thumb_ptr), values)
        self.assertNotIn((0x144, even_rom_ptr), values)


if __name__ == "__main__":
    unittest.main()
