from pathlib import Path
import json

ROOT = Path(__file__).resolve().parents[1]


def test_codespaces_contract():
    devcontainer = ROOT / ".devcontainer" / "devcontainer.json"
    bootstrap = ROOT / ".devcontainer" / "bootstrap.sh"
    dockerfile = ROOT / ".devcontainer" / "Dockerfile"

    assert devcontainer.exists(), "missing .devcontainer/devcontainer.json"
    assert bootstrap.exists(), "missing .devcontainer/bootstrap.sh"
    assert dockerfile.exists(), "missing .devcontainer/Dockerfile"

    data = json.loads(devcontainer.read_text(encoding="utf-8"))
    serialized = json.dumps(data)
    assert "bootstrap.sh" in serialized

    docker = dockerfile.read_text(encoding="utf-8")
    assert "devkitpro/devkitarm" in docker
    assert "/opt/devkitpro/devkitARM/bin" in docker

    script = bootstrap.read_text(encoding="utf-8")
    assert "release-candidate-dpe" in script
    assert "BPRE0.gba" in script
    assert "validate_release_candidate_workspace.py" in script
