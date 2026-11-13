"""Deterministic image orchestration, without an extra LLM deciding tool calls."""
from __future__ import annotations

import json
from typing import Any

from .imagen_tool import ImagenTool
from .story_contract import build_image_prompt


class DirectImageAgent:
    def __init__(self, project_id: str | None = None):
        self.project_id = project_id
        self.imagen_tool = ImagenTool(project_id=project_id)

    async def generate_image_from_description(
        self, description: str, character_descriptions: dict[str, str] | None = None,
        *, scene: dict | None = None, reference_image_base64: str | None = None,
    ) -> dict[str, Any]:
        characters = character_descriptions or {}
        scene = scene or {"index": 1, "beat": "setup", "description": description, "characters": list(characters)}
        prompt = build_image_prompt(scene, characters)
        result = json.loads(await self.imagen_tool.run(
            ctx=None, prompt=prompt, aspect_ratio="16:9", number_of_images=1,
            reference_image_base64=reference_image_base64,
        ))
        return result


# Preserve the earlier lesson's public class name.
DirectImageFunction = DirectImageAgent
