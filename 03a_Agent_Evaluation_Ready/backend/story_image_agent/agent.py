"""ADK BaseAgent lesson: execute the image tool directly for one validated scene."""
from __future__ import annotations

import json
import logging
from typing import AsyncGenerator

from google.adk.agents import BaseAgent
from google.adk.agents.invocation_context import InvocationContext
from google.adk.events.event import Event
from google.genai.types import Content, Part

from .imagen_tool import ImagenTool
from .story_contract import build_image_prompt

logger = logging.getLogger(__name__)


class CustomImageAgent(BaseAgent):
    imagen_tool: ImagenTool | None = None

    async def _run_async_impl(self, ctx: InvocationContext) -> AsyncGenerator[Event, None]:
        try:
            if self.imagen_tool is None:
                raise ValueError("Image generation is not configured. See SETUP.md.")
            text = "".join(part.text or "" for part in (ctx.user_content.parts or [])) if ctx.user_content else ""
            try:
                data = json.loads(text)
            except json.JSONDecodeError:
                data = {"scene_description": text}
            characters = data.get("character_descriptions", {})
            scene = data.get("scene") or {
                "index": 1, "beat": "setup", "description": data.get("scene_description", ""),
                "characters": list(characters),
            }
            if not scene.get("description"):
                raise ValueError("A scene description is required.")
            result = await self.imagen_tool.run(
                ctx=None, prompt=build_image_prompt(scene, characters), aspect_ratio="16:9",
                number_of_images=1, reference_image_base64=data.get("reference_image_base64"),
            )
        except Exception as exc:
            logger.warning("Image agent failed (%s).", type(exc).__name__)
            result = json.dumps({"success": False, "error": "Image generation unavailable. Check backend configuration."})
        ctx.session.state["image_result"] = result
        yield Event(author=self.name, content=Content(role="model", parts=[Part(text=result)]))


def create_root_agent() -> CustomImageAgent:
    try:
        tool = ImagenTool()
    except Exception as exc:
        logger.warning("Image agent starts without credentials (%s); see SETUP.md.", type(exc).__name__)
        tool = None
    return CustomImageAgent(name="custom_image_agent", imagen_tool=tool)


root_agent = create_root_agent()
