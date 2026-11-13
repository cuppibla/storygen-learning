import json
import os
import subprocess
import sys
from pathlib import Path

import pytest

from shared.backend.story_contract import parse_story_response

ROOT = Path(__file__).resolve().parents[1]
BACKENDS = sorted(ROOT.glob("0*/backend"))
MAINS = sorted(p for backend in BACKENDS for p in backend.glob("main*.py"))


def test_shared_copies_are_in_sync():
    result = subprocess.run([sys.executable, "tools/sync_workshop.py", "--check"], cwd=ROOT, capture_output=True, text=True)
    assert result.returncode == 0, result.stdout + result.stderr


@pytest.mark.parametrize("path", MAINS, ids=lambda p: str(p.relative_to(ROOT)))
def test_every_backend_entrypoint_imports_without_credentials(path):
    env = dict(os.environ, GOOGLE_API_KEY="", GOOGLE_GENAI_USE_VERTEXAI="FALSE")
    result = subprocess.run([sys.executable, "-c", "import main"], cwd=path.parent, env=env, capture_output=True, text=True, timeout=45)
    assert result.returncode == 0, result.stderr


@pytest.mark.parametrize("path", MAINS, ids=lambda p: str(p.relative_to(ROOT)))
def test_every_workflow_uses_validation_and_reference_images(path):
    text = path.read_text()
    assert "generate_validated_story" in text
    assert "reference_image_base64" in text
    assert "await asyncio.sleep(2)" not in text


def test_all_story_goldens_pass_the_same_runtime_contract():
    folder = ROOT / "03b_Agent_Evaluation_Done/backend/story_agent"
    count = 0
    for path in folder.glob("*.json"):
        data = json.loads(path.read_text())
        for case in data.get("eval_cases", []):
            for turn in case["conversation"]:
                story = parse_story_response(turn["final_response"]["parts"][0]["text"])
                assert len(story["scenes"]) == 6
                count += 1
    assert count == 7
    config = json.loads((folder / "test_config.json").read_text())
    assert config["custom_evaluators"]["json_structure_validator"]["scene_count"] == 6


def test_full_story_image_evaluation_has_six_turns():
    path = ROOT / "03b_Agent_Evaluation_Done/backend/story_image_agent/image_agent_eval.evalset.json"
    data = json.loads(path.read_text())
    case = next(case for case in data["eval_cases"] if case["eval_id"] == "multi_turn_story_visualization")
    assert len(case["conversation"]) == 6


def test_no_stale_four_scene_or_retired_model_assumptions_in_application_code():
    for path in ROOT.glob("0*/backend/**/*.py"):
        text = path.read_text()
        # Plan-aware contract/generator may deliberately describe the free four-scene arc.
        if path.name not in {"story_contract.py", "story_generation.py"}:
            assert "exactly four" not in text
        assert "imagegeneration@006" not in text
        assert "gemini-1.5-flash" not in text
    for path in ROOT.glob("0*/frontend/app/page.tsx"):
        assert "Array(4)" not in path.read_text()
        assert "expectedFrames={4}" not in path.read_text()


def test_deployment_template_image_model_matches_shared_default():
    import yaml
    from shared.backend.story_contract import DEFAULT_IMAGE_MODEL

    config = yaml.safe_load((ROOT / "06_Final_Solution/.github/config/deployment.yml").read_text())
    assert config["image_model"] == DEFAULT_IMAGE_MODEL
    action = (ROOT / "06_Final_Solution/.github/actions/load-config/action.yml").read_text()
    assert f'.image_model // "{DEFAULT_IMAGE_MODEL}"' in action
