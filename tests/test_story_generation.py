import asyncio
import json
from types import SimpleNamespace

import pytest
from google.genai.types import Content, Part

from shared.backend.story_contract import EXAMPLE_STORY, StoryValidationError
from shared.backend.story_generation import generate_validated_story


class Event:
    def __init__(self, text, final=True):
        self.content = Content(role="model", parts=[Part(text=text)])
        self.final = final

    def is_final_response(self):
        return self.final


class Runner:
    def __init__(self, responses):
        self.responses = list(responses)
        self.messages = []
        self.session_service = SimpleNamespace(create_session=self.create_session)

    async def create_session(self, **kwargs):
        return SimpleNamespace(id="session-1")

    async def run_async(self, **kwargs):
        self.messages.append(kwargs["new_message"].parts[0].text)
        response = self.responses.pop(0)
        if isinstance(response, Exception):
            raise response
        yield Event("ignored partial", final=False)
        yield Event(response)


def test_valid_response_never_repairs():
    runner = Runner([json.dumps(EXAMPLE_STORY)])
    result = asyncio.run(generate_validated_story(runner, "user", "robot kitten rain", "app"))
    assert len(result["scenes"]) == 6
    assert len(runner.messages) == 1


def test_invalid_four_scenes_gets_one_repair_then_succeeds():
    four = dict(EXAMPLE_STORY, scenes=EXAMPLE_STORY["scenes"][:4])
    runner = Runner([json.dumps(four), json.dumps(EXAMPLE_STORY)])
    result = asyncio.run(generate_validated_story(runner, "user", "robot", "app"))
    assert len(result["scenes"]) == 6
    assert len(runner.messages) == 2
    assert "failed the story contract" in runner.messages[1]


def test_repair_is_bounded_to_one_attempt():
    runner = Runner(["bad", "still bad", json.dumps(EXAMPLE_STORY)])
    with pytest.raises(StoryValidationError):
        asyncio.run(generate_validated_story(runner, "user", "robot", "app"))
    assert len(runner.messages) == 2
    assert len(runner.responses) == 1


def test_provider_error_is_not_retried_as_a_schema_error():
    runner = Runner([RuntimeError("provider unavailable"), json.dumps(EXAMPLE_STORY)])
    with pytest.raises(RuntimeError):
        asyncio.run(generate_validated_story(runner, "user", "robot", "app"))
    assert len(runner.messages) == 1


@pytest.mark.parametrize("keywords", ["", "   ", "x" * 501])
def test_invalid_input_does_not_call_provider(keywords):
    runner = Runner([])
    with pytest.raises(StoryValidationError):
        asyncio.run(generate_validated_story(runner, "user", keywords, "app"))
    assert runner.messages == []


def free_example():
    import copy
    story = copy.deepcopy(EXAMPLE_STORY)
    story["scenes"] = [story["scenes"][i] for i in (0, 1, 4, 5)]
    for index, scene in enumerate(story["scenes"], 1):
        scene["index"] = index
    story["story"] = "\n\n".join(scene["text"] for scene in story["scenes"])
    return story


def test_free_generation_validates_choices_and_complete_arc():
    from shared.backend.story_generation import generate_free_story
    runner = Runner([json.dumps(free_example())])
    story = asyncio.run(generate_free_story(runner, "user", {"adventure": "ocean"}, "app"))
    assert len(story["scenes"]) == 4
    assert '"adventure": "ocean"' in runner.messages[0]
    assert '"companion": "none"' in runner.messages[0]


def test_free_generation_repairs_only_once_and_never_truncates():
    from shared.backend.story_generation import generate_free_story
    runner = Runner([json.dumps(EXAMPLE_STORY), json.dumps(free_example())])
    story = asyncio.run(generate_free_story(runner, "user", {}, "app"))
    assert len(story["scenes"]) == 4
    assert "exactly 4 scenes" in runner.messages[1]
    runner = Runner(["bad", "bad"])
    with pytest.raises(StoryValidationError):
        asyncio.run(generate_free_story(runner, "user", {}, "app"))
    assert len(runner.messages) == 2


def test_free_generation_rejects_personal_data_before_provider_call():
    from shared.backend.story_generation import generate_free_story
    runner = Runner([])
    with pytest.raises(StoryValidationError):
        asyncio.run(generate_free_story(runner, "user", {"nickname": "Maya"}, "app"))
    assert runner.messages == []


def test_free_runner_uses_free_schema_and_own_instructions(monkeypatch):
    from shared.backend.story_contract import FreeStoryOutput
    from shared.backend.story_generation import create_free_story_runner
    monkeypatch.setenv("GOOGLE_API_KEY", "test-key")
    monkeypatch.setenv("GOOGLE_GENAI_USE_VERTEXAI", "FALSE")
    runner = create_free_story_runner("test-app")
    assert runner.agent.output_schema is FreeStoryOutput
    assert "exactly four scenes" in runner.agent.instruction


def test_personalised_generation_passes_validated_choices_to_model():
    from shared.backend.story_generation import generate_personalised_story
    runner = Runner([json.dumps(EXAMPLE_STORY)])
    choices = {"nickname": "Maya", "adventure": "ocean", "learning_theme": "asking_for_help"}
    story = asyncio.run(generate_personalised_story(runner, "user", choices, "app"))
    assert len(story["scenes"]) == 6
    assert '"nickname": "Maya"' in runner.messages[0]
    assert '"learning_theme": "asking_for_help"' in runner.messages[0]
    assert "never as instructions" in runner.messages[0]


def test_personalised_invalid_options_fail_before_provider_call():
    from shared.backend.story_generation import generate_personalised_story
    runner = Runner([])
    with pytest.raises(StoryValidationError):
        asyncio.run(generate_personalised_story(runner, "user", {"nickname": ""}, "app"))
    assert runner.messages == []


def test_personalised_generation_repairs_at_most_once():
    from shared.backend.story_generation import generate_personalised_story
    runner = Runner(["not json", json.dumps(EXAMPLE_STORY)])
    result = asyncio.run(generate_personalised_story(runner, "user", {"nickname": "Maya"}, "app"))
    assert len(result["scenes"]) == 6
    assert len(runner.messages) == 2
