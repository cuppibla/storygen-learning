"""Validated story choices; these describe content, not payment entitlement.

The transport must verify a paid entitlement independently before accepting the
personalised plan. Client-provided options must never be treated as proof of payment.
"""
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field


class FreeStoryOptions(BaseModel):
    model_config = ConfigDict(extra="forbid", str_strip_whitespace=True)
    adventure: Literal["animals", "ocean", "space", "magic", "mystery"] = "animals"
    companion: Literal["none", "animal", "robot", "dragon", "teddy"] = "none"


class PersonalisedStoryOptions(FreeStoryOptions):
    nickname: str = Field(min_length=1, max_length=40)
    learning_theme: Literal["kindness", "friendship", "persistence", "curiosity", "asking_for_help"] = "kindness"
    reading_level: Literal["read_aloud", "beginning", "confident"] = "read_aloud"
    mood: Literal["calm", "funny", "gentle_adventure"] = "gentle_adventure"
    setting: Literal["garden", "space", "ocean", "forest"] = "garden"
    strength: Literal["curious", "creative", "helpful", "determined"] = "curious"
    appearance: str | None = Field(default=None, max_length=120)
    discussion_prompts: bool = False
