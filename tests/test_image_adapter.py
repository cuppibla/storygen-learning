import asyncio
import base64
import json
from types import SimpleNamespace

import pytest

from shared.backend.imagen_tool import ImagenTool
from shared.backend.story_contract import DEFAULT_IMAGE_MODEL, EXAMPLE_STORY
from shared.backend.direct_image_agent import DirectImageAgent


class Models:
    def __init__(self, image=b"png-bytes"):
        self.image = image
        self.calls = []

    def generate_content(self, **kwargs):
        self.calls.append(kwargs)
        parts = [] if self.image is None else [SimpleNamespace(thought=False, inline_data=SimpleNamespace(data=self.image, mime_type="image/png"))]
        return SimpleNamespace(candidates=[SimpleNamespace(content=SimpleNamespace(parts=parts))])


@pytest.fixture
def api_key(monkeypatch):
    monkeypatch.setenv("GOOGLE_API_KEY", "test-key-never-log")
    monkeypatch.setenv("GENMEDIA_BUCKET", "")
    monkeypatch.delenv("IMAGE_MODEL", raising=False)


def test_uses_gemini_content_api_and_image_config(api_key):
    models = Models()
    tool = ImagenTool(client=SimpleNamespace(models=models))
    result = json.loads(asyncio.run(tool.run(prompt="A gentle scene")))
    assert result["success"] is True
    assert result["images_generated"] == 1
    assert base64.b64decode(result["images"][0]["base64"]) == b"png-bytes"
    call = models.calls[0]
    assert call["model"] == DEFAULT_IMAGE_MODEL
    assert call["config"].response_modalities == ["IMAGE"]
    assert call["config"].image_config.aspect_ratio == "16:9"
    assert call["config"].image_config.output_mime_type == "image/png"


def test_reference_image_is_passed_as_an_image_part(api_key):
    models = Models()
    tool = ImagenTool(client=SimpleNamespace(models=models))
    reference = base64.b64encode(b"reference-png").decode()
    result = json.loads(asyncio.run(tool.run(prompt="Next scene", reference_image_base64=reference)))
    assert result["success"]
    parts = models.calls[0]["contents"]
    assert len(parts) == 2
    assert parts[1].inline_data.data == b"reference-png"
    assert parts[1].inline_data.mime_type == "image/png"


def test_no_image_is_a_failure_not_a_fake_success(api_key):
    tool = ImagenTool(client=SimpleNamespace(models=Models(image=None)))
    result = json.loads(asyncio.run(tool.run(prompt="Blocked scene")))
    assert result["success"] is False
    assert "test-key-never-log" not in result["error"]


def test_batch_count_and_invalid_reference_fail_before_api_call(api_key):
    models = Models()
    tool = ImagenTool(client=SimpleNamespace(models=models))
    assert not json.loads(asyncio.run(tool.run(prompt="x", number_of_images=2)))["success"]
    assert not json.loads(asyncio.run(tool.run(prompt="x", reference_image_base64="%%%")))["success"]
    assert models.calls == []


def test_private_storage_uses_signed_url_and_falls_back_safely(api_key, monkeypatch):
    class Blob:
        def __init__(self, fail=False):
            self.fail = fail
            self.public_called = False
        def upload_from_string(self, data, content_type):
            self.data = data
            assert content_type == "image/png"
        def generate_signed_url(self, **kwargs):
            if self.fail:
                raise PermissionError("signing denied")
            assert kwargs["method"] == "GET"
            return "https://signed.example/image"
        def make_public(self):
            self.public_called = True
            raise AssertionError("Must not make children's images public")

    blob = Blob()
    storage = SimpleNamespace(bucket=lambda name: SimpleNamespace(blob=lambda name: blob))
    monkeypatch.setenv("GENMEDIA_BUCKET", "private-bucket")
    tool = ImagenTool(client=SimpleNamespace(models=Models()), storage_client=storage)
    result = json.loads(asyncio.run(tool.run(prompt="x")))
    assert result["images"][0]["gcs_url"] == "https://signed.example/image"
    assert result["images"][0]["stored_in_bucket"] is True
    assert not blob.public_called
    blob.fail = True
    result = json.loads(asyncio.run(tool.run(prompt="x")))
    assert result["success"] is True
    assert result["images"][0]["stored_in_bucket"] is False
    assert result["images"][0]["base64"]


def test_direct_adapter_only_prompts_for_visible_characters(api_key):
    class Tool:
        async def run(self, **kwargs):
            self.kwargs = kwargs
            return json.dumps({"success": True, "images": []})
    agent = DirectImageAgent.__new__(DirectImageAgent)
    agent.imagen_tool = Tool()
    scene = dict(EXAMPLE_STORY["scenes"][0], characters=["Pip"])
    characters = {c["name"]: c["description"] for c in EXAMPLE_STORY["main_characters"]}
    asyncio.run(agent.generate_image_from_description(scene["description"], characters, scene=scene, reference_image_base64="cmVm"))
    assert "Pip:" in agent.imagen_tool.kwargs["prompt"]
    assert "Marmalade:" not in agent.imagen_tool.kwargs["prompt"]
    assert agent.imagen_tool.kwargs["reference_image_base64"] == "cmVm"
