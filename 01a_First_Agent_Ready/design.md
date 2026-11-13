# First story agent — six-scene exercise

## Objective

Implement `backend/story_agent/agent.py` for the six-scene StoryGen contract. The Ready snapshot intentionally contains `root_agent = None`; the completed implementation is in `01b_First_Agent_Done`.

## Required agent

- Import `LlmAgent` from `google.adk.agents`.
- Import `DEFAULT_STORY_MODEL`, `STORY_INSTRUCTION`, and `StoryOutput` from `.story_contract`.
- Read the model ID from `STORY_MODEL`, falling back to `DEFAULT_STORY_MODEL`.
- Name the agent `story_agent`; give it no tools (images are orchestrated by the application).
- Set `instruction=STORY_INSTRUCTION` and `output_schema=StoryOutput`.
- Export the instance as `root_agent`.

## Narrative contract

Exactly six scenes, indexed 1–6:

1. **Setup** — character, setting, and desire.
2. **Inciting Incident** — a discovery/problem changes the plan.
3. **First Attempt** — a concrete attempt to solve it.
4. **Setback** — a complication, emotion, and rethink.
5. **Climax** — a decisive attempt informed by the setback.
6. **Resolution** — consequences and emotional payoff.

Use 180–270 words total, 25–50 words per scene, one or two main characters, and language suitable for ages 4–8. The complete `story` must equal the six scene texts in order. Each scene declares its beat, descriptive title, visible action, and actual character cast.

`shared/backend/story_contract.py` is the source of truth. It is copied into this standalone backend by `python tools/sync_workshop.py`. The application calls `generate_validated_story`, which validates before image generation and permits one schema-repair turn. Do not pad missing scenes or silently truncate extra scenes.

## Acceptance checks

- Valid JSON/schema version 2 passes; four, five, or seven scenes fail.
- Indices and beats are ordered; character references are declared.
- The first attempt and setback lead causally to the climax.
- The resolution follows from the character's action, not an unexplained reset.
- Scene descriptions depict six distinct visual moments.
- No credentials are needed to run the contract tests.

See `SETUP.md` for credential placement and `REVIEW.md` for the design rationale.
