from pathlib import Path
import json
import unittest

ROOT = Path(__file__).resolve().parents[1]


class CodespacesContractTest(unittest.TestCase):
    def test_codespaces_contract(self):
        devcontainer = ROOT / ".devcontainer" / "devcontainer.json"
        bootstrap = ROOT / ".devcontainer" / "bootstrap.sh"
        dockerfile = ROOT / ".devcontainer" / "Dockerfile"

        self.assertTrue(devcontainer.exists(), "missing .devcontainer/devcontainer.json")
        self.assertTrue(bootstrap.exists(), "missing .devcontainer/bootstrap.sh")
        self.assertTrue(dockerfile.exists(), "missing .devcontainer/Dockerfile")

        data = json.loads(devcontainer.read_text(encoding="utf-8"))
        serialized = json.dumps(data)
        self.assertIn("bootstrap.sh", serialized)

        docker = dockerfile.read_text(encoding="utf-8")
        self.assertIn("devkitpro/devkitarm", docker)
        self.assertIn("/opt/devkitpro/devkitARM/bin", docker)

        script = bootstrap.read_text(encoding="utf-8")
        self.assertIn("release-candidate-dpe", script)
        self.assertIn("BPRE0.gba", script)
        self.assertIn("validate_release_candidate_workspace.py", script)


if __name__ == "__main__":
    unittest.main()
