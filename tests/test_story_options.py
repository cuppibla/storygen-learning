import pytest
from pydantic import ValidationError

from shared.backend.story_options import FreeStoryOptions, PersonalisedStoryOptions


def test_free_options_reject_personal_data():
    assert FreeStoryOptions(adventure="ocean").adventure == "ocean"
    with pytest.raises(ValidationError):
        FreeStoryOptions(nickname="Maya")


def test_personalised_options_are_bounded_and_validated():
    assert PersonalisedStoryOptions(nickname=" Maya ").nickname == "Maya"
    with pytest.raises(ValidationError):
        PersonalisedStoryOptions(nickname=" ")
    with pytest.raises(ValidationError):
        PersonalisedStoryOptions(nickname="x" * 41)
    with pytest.raises(ValidationError):
        PersonalisedStoryOptions(nickname="Maya", learning_theme="unknown")
