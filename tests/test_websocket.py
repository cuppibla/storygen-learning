import json
import sys
from pathlib import Path

import pytest
from fastapi.testclient import TestClient

from shared.backend.story_contract import EXAMPLE_STORY

ROOT = Path(__file__).resolve().parents[1]


@pytest.fixture
def backend(monkeypatch):
    monkeypatch.setenv("GOOGLE_API_KEY", "")
    monkeypatch.setenv("GOOGLE_GENAI_USE_VERTEXAI", "FALSE")
    monkeypatch.syspath_prepend(str(ROOT / "04b_Manual_Deployment_Done/backend"))
    import main
    return main


def test_websocket_delivers_six_scenes_and_six_indexed_images(backend, monkeypatch):
    calls = []

    async def story(*args):
        return EXAMPLE_STORY

    class Images:
        async def generate_image_from_description(self, description, characters, *, scene, reference_image_base64):
            calls.append((scene["index"], reference_image_base64))
            return {"success": True, "images": [{"base64": "cG5n", "format": "png"}], "reference_image_base64": "cmVm"}

    monkeypatch.setattr(backend, "generate_validated_story", story)
    monkeypatch.setattr(backend, "direct_image_agent", Images())
    with TestClient(backend.app) as client:
        with client.websocket_connect("/ws/test") as ws:
            assert ws.receive_json()["type"] == "connected"
            ws.send_json({"type": "generate_story", "data": "tiny robot, rainy city, lost kitten"})
            assert ws.receive_json()["type"] == "processing"
            complete = ws.receive_json()
            assert complete["type"] == "story_complete"
            assert complete["data"].count("[SCENE ") == 6
            indices = []
            for _ in range(6):
                message = ws.receive_json()
                assert message["type"] == "image_generated"
                indices.append(message["data"]["index"])
                assert "reference_image_base64" not in message["data"]
            assert indices == list(range(6))
            assert ws.receive_json()["type"] == "turn_complete"
    assert calls == [(1, None)] + [(index, "cmVm") for index in range(2, 7)]


def test_invalid_story_sends_error_and_spends_no_image_calls(backend, monkeypatch):
    async def invalid(*args):
        raise backend.StoryValidationError("Exactly six scenes are required.")

    class Images:
        async def generate_image_from_description(self, *args, **kwargs):
            pytest.fail("Invalid stories must not generate images")

    monkeypatch.setattr(backend, "generate_validated_story", invalid)
    monkeypatch.setattr(backend, "direct_image_agent", Images())
    with TestClient(backend.app) as client:
        with client.websocket_connect("/ws/test") as ws:
            ws.receive_json()
            ws.send_json({"type": "generate_story", "data": "robot"})
            assert ws.receive_json()["type"] == "processing"
            error = ws.receive_json()
            assert error["type"] == "error"
            assert "six scenes" in error["message"]


def test_request_id_is_echoed_on_workflow_events(backend, monkeypatch):
    async def story(*args):
        return EXAMPLE_STORY

    monkeypatch.setattr(backend, "generate_validated_story", story)
    monkeypatch.setattr(backend, "direct_image_agent", None)
    with TestClient(backend.app) as client:
        with client.websocket_connect("/ws/test") as ws:
            ws.receive_json()
            ws.send_json({"type": "generate_story", "data": "robot", "request_id": "req-123"})
            for _ in range(9):  # processing + story + six image placeholders + completion
                assert ws.receive_json()["request_id"] == "req-123"


def test_health_declares_scene_count(backend):
    with TestClient(backend.app) as client:
        assert client.get("/health").json()["scene_count"] == 6


def test_missing_image_configuration_keeps_story_and_marks_all_six_slots(backend, monkeypatch):
    async def story(*args):
        return EXAMPLE_STORY

    monkeypatch.setattr(backend, "generate_validated_story", story)
    monkeypatch.setattr(backend, "direct_image_agent", None)
    with TestClient(backend.app) as client:
        with client.websocket_connect("/ws/test") as ws:
            ws.receive_json()
            ws.send_json({"type": "generate_story", "data": "robot"})
            assert ws.receive_json()["type"] == "processing"
            assert ws.receive_json()["type"] == "story_complete"
            for index in range(6):
                message = ws.receive_json()
                assert message["data"]["index"] == index
                assert message["data"]["placeholder"] is True
                assert "SETUP.md" in message["data"]["error"]
            assert ws.receive_json()["type"] == "turn_complete"


def test_one_image_failure_does_not_abort_remaining_scenes(backend, monkeypatch):
    async def story(*args):
        return EXAMPLE_STORY

    class Images:
        async def generate_image_from_description(self, description, characters, *, scene, reference_image_base64):
            if scene["index"] == 3:
                raise RuntimeError("quota")
            return {"success": True, "images": [{"base64": "cG5n", "format": "png"}], "reference_image_base64": "cmVm"}

    monkeypatch.setattr(backend, "generate_validated_story", story)
    monkeypatch.setattr(backend, "direct_image_agent", Images())
    with TestClient(backend.app) as client:
        with client.websocket_connect("/ws/test") as ws:
            ws.receive_json()
            ws.send_json({"type": "generate_story", "data": "robot"})
            ws.receive_json()
            ws.receive_json()
            messages = [ws.receive_json() for _ in range(6)]
            assert [m["data"]["index"] for m in messages] == list(range(6))
            assert messages[2]["data"]["placeholder"] is True
            assert "base64" in messages[5]["data"]
            assert ws.receive_json()["type"] == "turn_complete"


def test_workflow_exception_is_not_exposed_or_logged(backend, monkeypatch, caplog):
    async def fail(*args, **kwargs):
        raise RuntimeError("private-provider-detail")

    monkeypatch.setattr(backend, "run_two_agent_workflow", fail)
    with TestClient(backend.app) as client:
        with client.websocket_connect("/ws/test") as ws:
            ws.receive_json()
            ws.send_json({"type": "generate_story", "data": "robot", "request_id": "req-private"})
            assert ws.receive_json()["type"] == "processing"
            error = ws.receive_json()
            assert error["type"] == "error"
            assert error["request_id"] == "req-private"
            assert "private-provider-detail" not in error["message"]
    assert "private-provider-detail" not in caplog.text


def test_free_websocket_sends_four_scene_story_and_placeholders(backend, monkeypatch):
    import copy
    free = copy.deepcopy(EXAMPLE_STORY)
    free["scenes"] = [free["scenes"][i] for i in (0, 1, 4, 5)]
    for i, scene in enumerate(free["scenes"], 1):
        scene["index"] = i
    free["story"] = "\n\n".join(scene["text"] for scene in free["scenes"])
    seen = []

    async def generate_free(runner, user_id, options, app):
        seen.append(options)
        return free

    monkeypatch.setattr(backend, "create_free_story_runner", lambda app: object())
    monkeypatch.setattr(backend, "generate_free_story", generate_free)
    monkeypatch.setattr(backend, "direct_image_agent", None)
    with TestClient(backend.app) as client:
        with client.websocket_connect("/ws/test") as ws:
            ws.receive_json()
            ws.send_json({"type": "generate_free_story", "data": {"adventure": "ocean"}, "request_id": "free-1"})
            assert ws.receive_json()["type"] == "processing"
            story = ws.receive_json()
            assert story["request_id"] == "free-1"
            assert story["data"].count("[SCENE ") == 4
            assert [ws.receive_json()["data"]["index"] for _ in range(4)] == [0, 1, 2, 3]
            assert ws.receive_json()["type"] == "turn_complete"
    assert seen == [{"adventure": "ocean"}]


def test_free_websocket_rejects_personal_fields_without_images(backend, monkeypatch):
    monkeypatch.setattr(backend, "create_free_story_runner", lambda app: object())
    class Images:
        async def generate_image_from_description(self, *args, **kwargs):
            pytest.fail("Invalid choices must not generate images")
    monkeypatch.setattr(backend, "direct_image_agent", Images())
    with TestClient(backend.app) as client:
        with client.websocket_connect("/ws/test") as ws:
            ws.receive_json()
            ws.send_json({"type": "generate_free_story", "data": {"nickname": "Maya"}, "request_id": "bad-free"})
            assert ws.receive_json()["type"] == "processing"
            assert ws.receive_json()["type"] == "error"
