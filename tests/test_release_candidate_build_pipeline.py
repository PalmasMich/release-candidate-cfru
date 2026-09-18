from pathlib import Path
import importlib.util
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[1]
SCRIPT = ROOT / "scripts" / "build_release_candidate.py"
EXPECTED_SHA1 = "41cb23d8dccc8ebd7c649cd8fbb58eeace6e2fdc"


def load_builder():
    spec = importlib.util.spec_from_file_location("rc_builder", SCRIPT)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


class ReleaseCandidateBuildPipelineTest(unittest.TestCase):
    def test_validates_expected_pristine_rom_hash(self):
        builder = load_builder()
        self.assertEqual(builder.EXPECTED_SHA1, EXPECTED_SHA1)

    def test_pipeline_order_is_dpe_then_cfru(self):
        builder = load_builder()
        self.assertEqual(builder.PIPELINE, ("DPE", "CFRU"))

    def test_default_output_is_git_ignored_gba(self):
        builder = load_builder()
        self.assertEqual(builder.DEFAULT_OUTPUT_NAME, "release_candidate_test.gba")
        ignore = (ROOT / ".gitignore").read_text(encoding="utf-8")
        self.assertIn("*.gba", ignore)

    def test_private_rom_guard_rejects_wrong_hash(self):
        builder = load_builder()
        with tempfile.TemporaryDirectory() as tmp:
            rom = Path(tmp) / "BPRE0.gba"
            rom.write_bytes(b"not-a-fire-red-rom")
            with self.assertRaisesRegex(ValueError, "SHA-1"):
                builder.verify_pristine_rom(rom)

    def test_pipeline_restores_pristine_cfru_input_after_failure(self):
        builder = load_builder()
        pristine = b"private-pristine-rom"
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp) / "cfru"
            dpe = Path(tmp) / "dpe"
            root.mkdir()
            dpe.mkdir()
            base = root / "BPRE0.gba"
            base.write_bytes(pristine)

            def fake_verify(_path):
                return "test"

            def fake_run(label, cwd):
                if label == "DPE":
                    (cwd / "BPRE0.gba").write_bytes(b"dpe-expanded")
                    return
                (cwd / "BPRE0.gba").write_bytes(b"cfru-partial")
                raise RuntimeError("forced CFRU failure")

            with self.assertRaisesRegex(RuntimeError, "forced CFRU failure"):
                builder.run_pipeline(
                    cfru_root=root,
                    dpe_root=dpe,
                    output_path=root / "release_candidate_test.gba",
                    run_build=fake_run,
                    verify_rom=fake_verify,
                )

            self.assertEqual(base.read_bytes(), pristine)
            self.assertFalse((dpe / "BPRE0.gba").exists())


if __name__ == "__main__":
    unittest.main()
