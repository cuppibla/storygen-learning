# -*- coding: utf-8 -*-
import os
import json
import asyncio
import logging
from pathlib import Path
from dotenv import load_dotenv

from google.genai.types import Content, Part
from google.adk.runners import InMemoryRunner
from google.adk.sessions.in_memory_session_service import InMemorySessionService

from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager

from story_agent.agent import root_agent as story_agent
from story_agent.story_image_function import DirectImageFunction

from story_agent.story_contract import SCENE_COUNT, StoryValidationError, format_story_text
from story_agent.story_generation import create_free_story_runner, generate_free_story, generate_validated_story

# Load environment variables
load_dotenv()

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Application constants
APP_NAME = "storygen_app"

# Initialize FastAPI app
app = FastAPI(title="StoryGen Backend", description="ADK-powered story generation backend")

# Add CORS middleware to allow frontend connections
app.add_middleware(
    CORSMiddleware,
    allow_origin_regex="https?://.*(localhost|run\.app)(:\d+)?|https?://.*\.run\.app",  # Allow localhost and all Cloud Run domains
    allow_origins=["http://localhost:3000", "http://127.0.0.1:3000"],  # Next.js default ports
    allow_credentials=False,  # No cookie auth; do not combine credentialed CORS with wildcard origins.
    allow_methods=["*"],
    allow_headers=["*"],
)

# Initialize session service and agents
project_id = os.getenv("GOOGLE_CLOUD_PROJECT") or os.getenv("GOOGLE_CLOUD_PROJECT_ID")

# AI Studio needs only GOOGLE_API_KEY; Vertex uses project + ADC.
direct_image_function = None
try:
    direct_image_function = DirectImageFunction(project_id=project_id)
except Exception as exc:
    logger.warning("Image generation unavailable (%s); see SETUP.md.", type(exc).__name__)

async def run_two_agent_workflow(websocket: WebSocket, user_id: str, keywords: str | dict, request_id: str | None = None, *, free: bool = False):
    """
    Clean two-agent workflow:
    1. StoryAgent generates structured story with scene data
    2. ImageAgent generates images for each scene
    3. Stream results to frontend as they're ready
    """
    logger.info(f"Starting two-agent workflow for user for user {user_id}")

    # Step 1: Generate and validate all six scenes before spending image quota.
    try:
        story_runner = InMemoryRunner(app_name=APP_NAME, agent=story_agent)
        if free:
            free_runner = create_free_story_runner(APP_NAME)
            story_data = await generate_free_story(free_runner, user_id, keywords, APP_NAME)
        else:
            story_data = await generate_validated_story(story_runner, user_id, keywords, APP_NAME)
        await websocket.send_text(json.dumps({
            "type": "story_complete",
            "request_id": request_id,
            "data": format_story_text(story_data),
        }))
    except StoryValidationError as exc:
        logger.warning("Story contract validation failed: %s", exc)
        await websocket.send_text(json.dumps({
            "type": "error",
            "request_id": request_id,
            "message": f"The story needs a small rewrite: {exc}",
        }))
        return
    except Exception as exc:
        logger.error("Story generation failed (%s). Check credentials, quota and model access.", type(exc).__name__)
        await websocket.send_text(json.dumps({
            "type": "error",
            "request_id": request_id,
            "message": "Story generation is unavailable. Check the backend configuration and try again.",
        }))
        return

    # Step 2: Generate images using DirectImageAgent
    if story_data and direct_image_function and story_data.get("scenes"):
        logger.info("🎨 Starting image generation...")

        # Extract character descriptions from story data
        character_descriptions = {}
        if story_data.get("main_characters"):
            for character in story_data["main_characters"]:
                char_name = character.get("name", "")
                char_desc = character.get("description", "")
                if char_name and char_desc:
                    character_descriptions[char_name] = char_desc
            logger.info("Identified %d story characters", len(character_descriptions))

        reference_image_base64 = None
        for scene in story_data["scenes"]:
            scene_index = scene.get("index", 1) - 1  # Convert to 0-based index
            scene_description = scene.get("description", "")
            scene_title = scene.get("title", "Unknown")

            try:
                logger.info("Generating image for scene %d", scene_index + 1)

                # Use the DirectImageFunction
                image_data = await direct_image_function.generate_image_from_description(
                    scene_description, character_descriptions,
                    scene=scene, reference_image_base64=reference_image_base64,
                )

                if image_data and image_data.get("success") and reference_image_base64 is None:
                    reference_image_base64 = image_data.get("reference_image_base64")
                if image_data and image_data.get("images"):
                    for img_data in image_data["images"]:
                        image_payload = {
                            "index": scene_index,
                            "scene_title": scene.get("title", ""),
                            "format": img_data.get("format", "png"),
                            "stored_in_bucket": img_data.get("stored_in_bucket", False)
                        }

                        # Include GCS URL if available
                        if img_data.get("gcs_url"):
                            image_payload["gcs_url"] = img_data["gcs_url"]
                            logger.info(f"✅ Generated image for scene {scene_index + 1} with GCS URL")

                        # Include base64 if available (for fallback)
                        if img_data.get("base64"):
                            image_payload["base64"] = img_data["base64"]

                        await websocket.send_text(json.dumps({
                            "type": "image_generated",
                            "request_id": request_id,
                            "data": image_payload
                        }))
                        logger.info(f"📤 Sent image for scene {scene_index + 1} to frontend")
                else:
                    raise Exception(f"Image generation failed: {image_data.get('error', 'Unknown error')}")

            except Exception as e:
                logger.error("Image generation failed for scene %d (%s)", scene_index + 1, type(e).__name__)
                # Send error placeholder so frontend knows this slot exists
                error_payload = {
                    "index": scene_index,
                    "scene_title": scene.get("title", ""),
                    "format": "png",
                    "stored_in_bucket": False,
                    "error": "Illustration unavailable. Please try again.",
                    "placeholder": True
                }
                await websocket.send_text(json.dumps({
                    "type": "image_generated",
                    "request_id": request_id,
                    "data": error_payload
                }))
                logger.info(f"📤 Sent error placeholder for scene {scene_index + 1}")


        logger.info("🎨 All image generation completed")
    else:
        if not direct_image_function:
            logger.warning("⚠️ DirectImageFunction not available, skipping image generation")
        elif not story_data.get("scenes"):
            logger.warning("⚠️ No scenes found in story data, skipping image generation")

    # Missing image configuration is visible per scene; keep the validated story.
    if story_data and not direct_image_function:
        for scene in story_data["scenes"]:
            await websocket.send_text(json.dumps({
                "type": "image_generated",
                "request_id": request_id,
                "data": {
                    "index": scene["index"] - 1,
                    "scene_title": scene["title"],
                    "format": "png",
                    "placeholder": True,
                    "error": "Images are not configured. See SETUP.md.",
                },
            }))

    # Send completion notification
    await websocket.send_text(json.dumps({"type": "turn_complete", "turn_complete": True, "request_id": request_id}))



@app.websocket("/ws/{user_id}")
async def websocket_endpoint(websocket: WebSocket, user_id: str):
    """
    WebSocket endpoint for real-time story generation

    Args:
        websocket: WebSocket connection
        user_id: Unique user identifier
    """
    await websocket.accept()
    request_id = None
    logger.info(f"Client #{user_id} connected")

    try:
        # Send connection confirmation
        await websocket.send_text(json.dumps({
            "type": "connected",
            "message": "Connected to StoryGen backend"
        }))

        while True:
            # Receive message from client
            message_json = await websocket.receive_text()
            message = json.loads(message_json)
            if not isinstance(message, dict):
                await websocket.send_text(json.dumps({"type": "error", "message": "Expected a JSON object.", "request_id": request_id}))
                continue
            raw_request_id = message.get("request_id")
            request_id = raw_request_id if isinstance(raw_request_id, str) and 0 < len(raw_request_id) <= 100 else None

            message_type = message.get("type")
            data = message.get("data", "")

            if message_type in ("generate_story", "generate_free_story"):
                try:
                    # Send processing notification
                    await websocket.send_text(json.dumps({
                        "type": "processing",
                        "request_id": request_id,
                        "message": "Generating story and images..."
                    }))

                    # Run the clean two-agent workflow
                    if message_type == "generate_free_story":
                        await run_two_agent_workflow(websocket, user_id, data, request_id=request_id, free=True)
                    else:
                        await run_two_agent_workflow(websocket, user_id, data, request_id=request_id)

                except Exception as e:
                    logger.error("Workflow error (%s)", type(e).__name__)
                    await websocket.send_text(json.dumps({
                        "type": "error",
                        "request_id": request_id,
                        "message": "Story generation is unavailable. Please try again."
                    }))

            elif message_type == "ping":
                # Handle ping/keepalive messages
                await websocket.send_text(json.dumps({"type": "pong"}))

            else:
                logger.warning(f"Unknown message type: {message_type}")

    except WebSocketDisconnect:
        logger.info(f"Client #{user_id} disconnected")
    except Exception as e:
        logger.error("Workflow error (%s)", type(e).__name__)
        try:
            await websocket.send_text(json.dumps({
                "type": "error",
                "request_id": request_id,
                "message": "Story generation is unavailable. Please try again."
            }))
        except:
            pass
    finally:
        logger.info(f"Client #{user_id} connection closed")

@app.get("/health")
async def health_check():
    """Health check endpoint"""
    return {"status": "healthy", "service": "storygen-backend", "scene_count": SCENE_COUNT}



# Serve frontend
STATIC_FILES_DIR = os.environ.get("STATIC_FILES_DIR", "../frontend/out")
try:
    app.mount("/", StaticFiles(directory=STATIC_FILES_DIR, html=True), name="static")
except RuntimeError:
    print("Frontend build not found. Run `npm run build` in the `frontend` directory.")


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
