import logging
import os

from google.adk.agents import LlmAgent

from .imagen_tool import ImagenTool
from .story_contract import DEFAULT_STORY_MODEL

try:
    tools = [ImagenTool()]
except Exception as exc:
    logging.getLogger(__name__).warning("Image tool unavailable (%s); see SETUP.md.", type(exc).__name__)
    tools = []

root_agent = LlmAgent(
    model=os.getenv("STORY_MODEL", DEFAULT_STORY_MODEL),
    name="image_agent",
    description="Illustrates one story scene with the Google Gemini image tool.",
    instruction="""Call generate_image once for the supplied scene. Build a prompt from
    the scene description and only the characters present. Use the shared watercolor
    picture-book style and preserve supplied character identities. If a reference image
    is provided, the deterministic workflow passes it to the tool. Never claim identity
    is guaranteed. Return the tool result without inventing URLs or image data.""",
    tools=tools,
)
