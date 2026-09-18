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


def make_fake_workspace(tmp):
    root = Path(tmp) / "cfru"
    dpe = Path(tmp) / "dpe"
    (root / "scripts").mkdir(parents=True)
    (dpe / "scripts").mkdir(parents=True)
    (root / "scripts" / "make.py").write_text("# test fixture\n", encoding="utf-8")
    (dpe / "scripts" / "make.py").write_text("# test fixture\n", encoding="utf-8")
    return root, dpe


class ReleaseCandidateBuildPipelineTest(unittest.TestCase):
    def test_validates_expected_pristine_rom_hash(self):
        builder = load_builder()
        self.assertEqual(builder.EXPECTED_SHA1, EXPECTED_SHA1)

    def test_pipeline_order_is_dpe_then_cfru_then_preview_patch(self):
        builder = load_builder()
        self.assertEqual(builder.PIPELINE, ("DPE", "CFRU", "RC_PREVIEW_PATCH"))

    def test_dpe_sync_targets_preview_branch(self):
        builder = load_builder()
        self.assertEqual(builder.DPE_BRANCH, "feature/cagliari-preview-0.1")

    def test_dpe_preview_symbol_gate_requires_tartrek_and_mistrillo_assets(self):
        builder = load_builder()
        with tempfile.TemporaryDirectory() as tmp:
            dpe = Path(tmp)
            (dpe / "offsets.ini").write_text(
                "gFrontSprite1294RCTartrekTiles: 09900000\n"
                "gBackShinySprite1294RCTartrekTiles: 09901000\n"
                "gIconSprite1294RCTartrekTiles: 09902000\n"
                "gFrontSprite1294RCTartrekPal: 09903000\n"
                "gBackShinySprite1294RCTartrekPal: 09903000\n"
                "gFrontSprite1297RCMistrilloTiles: 09904000\n"
                "gBackShinySprite1297RCMistrilloTiles: 09905000\n"
                "gIconSprite1297RCMistrilloTiles: 09906000\n"
                "gFrontSprite1297RCMistrilloPal: 09907000\n"
                "gBackShinySprite1297RCMistrilloPal: 09907000\n",
                encoding="utf-8",
            )
            builder.verify_dpe_tartrek_symbols(dpe)

    def test_dpe_tartrek_symbol_gate_rejects_stale_dpe_build(self):
        builder = load_builder()
        with tempfile.TemporaryDirectory() as tmp:
            dpe = Path(tmp)
            (dpe / "offsets.ini").write_text("gFrontSprite001BulbasaurTiles: 09900000\n", encoding="utf-8")
            with self.assertRaisesRegex(RuntimeError, "Tartrek"):
                builder.verify_dpe_tartrek_symbols(dpe)

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
            root, dpe = make_fake_workspace(tmp)
            base = root / "BPRE0.gba"
            base.write_bytes(pristine)

            def fake_verify(_path):
                return "test"

            def fake_run(label, cwd):
                if label == "DPE":
                    (cwd / "test.gba").write_bytes(b"dpe-expanded")
                    return
                (cwd / "test.gba").write_bytes(b"cfru-partial")
                raise RuntimeError("forced CFRU failure")

            with self.assertRaisesRegex(RuntimeError, "forced CFRU failure"):
                builder.run_pipeline(
                    cfru_root=root,
                    dpe_root=dpe,
                    output_path=root / "release_candidate_test.gba",
                    run_build=fake_run,
                    verify_rom=fake_verify,
                    sync_dpe=lambda _path: None,
                    verify_dpe_symbols=lambda _path: None,
                    apply_preview_patch=lambda source, output: output.write_bytes(source.read_bytes()),
                )

            self.assertEqual(base.read_bytes(), pristine)
            self.assertFalse((dpe / "BPRE0.gba").exists())

    def test_pipeline_consumes_test_gba_and_applies_preview_patch(self):
        builder = load_builder()
        with tempfile.TemporaryDirectory() as tmp:
            root, dpe = make_fake_workspace(tmp)
            base = root / "BPRE0.gba"
            base.write_bytes(b"pristine")
            output = root / "release_candidate_test.gba"

            def fake_verify(_path):
                return "test"

            def fake_run(label, cwd):
                source = (cwd / "BPRE0.gba").read_bytes()
                if label == "DPE":
                    self.assertEqual(source, b"pristine")
                    (cwd / "test.gba").write_bytes(b"dpe-expanded")
                else:
                    self.assertEqual(source, b"dpe-expanded")
                    (cwd / "test.gba").write_bytes(b"dpe-plus-cfru")

            def fake_preview_patch(source, destination):
                self.assertEqual(source.read_bytes(), b"dpe-plus-cfru")
                destination.write_bytes(source.read_bytes() + b"-tartrek")

            builder.run_pipeline(
                cfru_root=root,
                dpe_root=dpe,
                output_path=output,
                run_build=fake_run,
                verify_rom=fake_verify,
                sync_dpe=lambda _path: None,
                verify_dpe_symbols=lambda _path: None,
                apply_preview_patch=fake_preview_patch,
            )

            self.assertEqual(output.read_bytes(), b"dpe-plus-cfru-tartrek")
            self.assertEqual(base.read_bytes(), b"pristine")


if __name__ == "__main__":
    unittest.main()
