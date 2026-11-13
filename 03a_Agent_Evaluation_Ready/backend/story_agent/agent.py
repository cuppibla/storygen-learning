import os

from google.adk.agents import LlmAgent

from .story_contract import DEFAULT_STORY_MODEL, STORY_INSTRUCTION, StoryOutput

tools = []

root_agent = LlmAgent(
    model=os.getenv("STORY_MODEL", DEFAULT_STORY_MODEL),
    name="story_agent",
    description="Creates a validated six-scene illustrated story for children.",
    instruction=STORY_INSTRUCTION,
    output_schema=StoryOutput,
    tools=tools,
)
