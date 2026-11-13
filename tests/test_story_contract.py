import copy
import json

import pytest

from shared.backend.story_contract import (
    EXAMPLE_STORY, SCENE_BEATS, StoryValidationError, build_image_prompt,
    format_story_text, parse_story_response, word_count,
)


def test_complete_example_is_valid_and_has_six_distinct_beats():
    story = parse_story_response(json.dumps(EXAMPLE_STORY))
    assert len(story["scenes"]) == 6
    assert tuple(scene["beat"] for scene in story["scenes"]) == SCENE_BEATS
    assert 180 <= word_count(story["story"]) <= 270
    assert len({scene["description"] for scene in story["scenes"]}) == 6


def test_accepts_one_complete_json_fence():
    raw = "```json\n" + json.dumps(EXAMPLE_STORY) + "\n```"
    assert parse_story_response(raw) == EXAMPLE_STORY


@pytest.mark.parametrize("count", [0, 4, 5, 7])
def test_rejects_wrong_scene_counts_without_padding_or_truncating(count):
    story = copy.deepcopy(EXAMPLE_STORY)
    story["scenes"] = (story["scenes"] * 2)[:count]
    story["story"] = "\n\n".join(scene["text"] for scene in story["scenes"])
    with pytest.raises(StoryValidationError):
        parse_story_response(json.dumps(story))


@pytest.mark.parametrize("mutation", ["index", "beat", "missing_text", "unknown_character", "duplicate_character", "story_mismatch", "short_scene", "extra_field", "boolean_index"])
def test_rejects_invalid_contract(mutation):
    story = copy.deepcopy(EXAMPLE_STORY)
    if mutation == "index":
        story["scenes"][2]["index"] = 4
    elif mutation == "beat":
        story["scenes"][3]["beat"] = "climax"
    elif mutation == "missing_text":
        del story["scenes"][0]["text"]
    elif mutation == "unknown_character":
        story["scenes"][0]["characters"] = ["Nobody"]
    elif mutation == "duplicate_character":
        story["scenes"][0]["characters"] = ["Pip", "Pip"]
    elif mutation == "story_mismatch":
        story["story"] += " An extra ending."
    elif mutation == "short_scene":
        story["scenes"][0]["text"] = "Too short."
        story["story"] = "\n\n".join(scene["text"] for scene in story["scenes"])
    elif mutation == "extra_field":
        story["secret"] = "not allowed"
    elif mutation == "boolean_index":
        story["scenes"][0]["index"] = True
    with pytest.raises(StoryValidationError):
        parse_story_response(json.dumps(story))


@pytest.mark.parametrize("raw", ["", "Here is your story: {}", "{} {}", "```json\n{}\n```\nExtra", "not json"])
def test_rejects_non_json_or_commentary(raw):
    with pytest.raises(StoryValidationError):
        parse_story_response(raw)


def test_marker_format_keeps_titles_and_order():
    text = format_story_text(EXAMPLE_STORY)
    assert text.count("[SCENE ") == 6
    assert text.index("[SCENE 3:") < text.index("[SCENE 4:")
    assert "[SCENE 4: A Splash and a Slide]" in text


def test_image_prompt_excludes_absent_characters_and_uses_reference_instruction():
    scene = copy.deepcopy(EXAMPLE_STORY["scenes"][2])
    scene["characters"] = ["Pip"]
    characters = {c["name"]: c["description"] for c in EXAMPLE_STORY["main_characters"]}
    prompt = build_image_prompt(scene, characters)
    assert "Pip:" in prompt
    assert "Marmalade:" not in prompt
    assert "reference image" in prompt
    assert "First Attempt" in prompt


def test_free_contract_requires_a_complete_four_scene_arc():
    story = copy.deepcopy(EXAMPLE_STORY)
    story["scenes"] = [story["scenes"][i] for i in (0, 1, 4, 5)]
    for index, scene in enumerate(story["scenes"], 1):
        scene["index"] = index
    story["story"] = "\n\n".join(scene["text"] for scene in story["scenes"])
    assert len(parse_story_response(json.dumps(story), plan="free")["scenes"]) == 4
    with pytest.raises(StoryValidationError):
        parse_story_response(json.dumps(story))
    story["scenes"][-1]["beat"] = "setback"
    with pytest.raises(StoryValidationError):
        parse_story_response(json.dumps(story), plan="free")


def test_unknown_plan_is_rejected():
    with pytest.raises(StoryValidationError):
        parse_story_response(json.dumps(EXAMPLE_STORY), plan="unknown")
