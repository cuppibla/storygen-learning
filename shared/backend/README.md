# StoryGen backend

FastAPI + Google ADK backend for the six-scene story contract. See the repository-level `SETUP.md` for credential placement and startup instructions.

## Flow

1. Validate keyword input (1–500 characters).
2. Generate structured text with `STORY_MODEL` and `StoryOutput`.
3. Validate exactly six ordered scenes; allow one schema-repair turn.
4. Send the complete story with `[SCENE N: title]` markers.
5. Generate one image per scene with `IMAGE_MODEL`; reuse the first successful image as a character reference.
6. Send each image/error with a zero-based scene index, then `turn_complete`.

The legacy filename `imagen_tool.py` / class `ImagenTool` now adapts the **Gemini image `generate_content` API**, not retired Imagen endpoints. Image calls run off the event loop. Storage is optional and private; inline image data is the fallback.

## WebSocket

`/ws/{user_id}` accepts:

```json
{"type":"generate_story","data":"tiny robot, rainy city, lost kitten"}
```

Server messages include `connected`, `processing`, `story_complete`, `image_generated`, `error`, and `turn_complete`. `image_generated.data` is an object containing `index`, image data or an error, and `format`. Raw model JSON is not streamed as story prose.

`GET /health` reports `scene_count: 6`. It is a process health check, not a paid model-access check.

## Tests

From the repository root, install `requirements-dev.txt` and run `python -m pytest -q`. Tests use mocks/fixtures and require no Google credentials. Live quality/consistency evaluation is a separate step after configuration.
