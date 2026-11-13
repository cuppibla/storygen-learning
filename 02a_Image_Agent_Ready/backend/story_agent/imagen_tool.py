"""Google Gemini image adapter; the ImagenTool name is retained for lesson imports.

The retired Imagen predict API is intentionally not used. This adapter uses the
Google Gen AI SDK's generate_content API and supports either AI Studio or Vertex.
"""
from __future__ import annotations

import asyncio
import base64
import logging
import os
import uuid
from datetime import timedelta
from typing import Any

from google import genai
from google.adk.tools import BaseTool, ToolContext
from google.genai import types

from .story_contract import DEFAULT_IMAGE_MODEL

logger = logging.getLogger(__name__)
MAX_REFERENCE_BYTES = 10 * 1024 * 1024


class ImagenTool(BaseTool):
    def __init__(self, project_id: str | None = None, location: str | None = None, *, client=None, storage_client=None):
        super().__init__(name="generate_image", description="Generate one child-friendly story illustration with Google Gemini Image.")
        self._project_id = project_id or os.getenv("GOOGLE_CLOUD_PROJECT") or os.getenv("GOOGLE_CLOUD_PROJECT_ID")
        self._location = location or os.getenv("GOOGLE_CLOUD_LOCATION") or os.getenv("GOOGLE_CLOUD_REGION") or "us-central1"
        self._bucket_name = os.getenv("GENMEDIA_BUCKET", "").strip()
        self._model_name = os.getenv("IMAGE_MODEL", DEFAULT_IMAGE_MODEL).strip()
        if not self._model_name:
            raise ValueError("IMAGE_MODEL must not be empty.")
        use_vertex = os.getenv("GOOGLE_GENAI_USE_VERTEXAI", "FALSE").strip().lower() == "true"
        timeout_ms = max(10, min(300, int(os.getenv("IMAGE_TIMEOUT_SECONDS", "60")))) * 1000
        if client is not None:
            self._client = client
        elif use_vertex:
            if not self._project_id:
                raise ValueError("Vertex AI requires GOOGLE_CLOUD_PROJECT_ID and Application Default Credentials.")
            self._client = genai.Client(vertexai=True, project=self._project_id, location=self._location,
                                        http_options=types.HttpOptions(timeout=timeout_ms))
        else:
            api_key = os.getenv("GOOGLE_API_KEY", "").strip()
            if not api_key:
                raise ValueError("Set GOOGLE_API_KEY in the backend .env file, or enable Vertex AI with ADC.")
            self._client = genai.Client(api_key=api_key, http_options=types.HttpOptions(timeout=timeout_ms))
        self._storage_client = storage_client
        if self._bucket_name and self._storage_client is None:
            from google.cloud import storage
            self._storage_client = storage.Client(project=self._project_id) if self._project_id else storage.Client()

    def _get_declaration(self) -> types.FunctionDeclaration:
        return types.FunctionDeclaration(
            name=self.name,
            description=self.description,
            parameters_json_schema={
                "type": "object",
                "properties": {
                    "prompt": {"type": "string"},
                    "aspect_ratio": {"type": "string", "enum": ["16:9", "4:3", "1:1", "3:4", "9:16"]},
                },
                "required": ["prompt"],
            },
        )

    async def run_async(self, *, args: dict[str, Any], tool_context: ToolContext) -> dict:
        import json
        return json.loads(await self.run(ctx=tool_context, **args))

    async def run(self, ctx: ToolContext | None = None, **kwargs) -> str:
        import json
        try:
            prompt = str(kwargs.get("prompt", "")).strip()
            if not prompt:
                raise ValueError("An image prompt is required.")
            if kwargs.get("number_of_images", 1) != 1:
                raise ValueError("This adapter generates one image per call; use one call per scene.")
            reference = kwargs.get("reference_image_base64")
            reference_bytes = None
            if reference:
                reference_bytes = base64.b64decode(reference, validate=True)
                if not reference_bytes or len(reference_bytes) > MAX_REFERENCE_BYTES:
                    raise ValueError("Invalid character reference image size.")
            result = await asyncio.to_thread(self._generate_sync, prompt, kwargs.get("aspect_ratio", "16:9"), reference_bytes)
            data = result["data"]
            image = {"index": 0, "base64": base64.b64encode(data).decode("ascii"), "format": "png", "stored_in_bucket": False}
            if self._bucket_name and self._storage_client is not None:
                try:
                    image["gcs_url"] = await asyncio.to_thread(self._store, data)
                    image["stored_in_bucket"] = True
                except Exception as exc:
                    # Private storage/signing failures must not lose a paid generated image.
                    logger.warning("Image storage unavailable (%s); using inline image fallback.", type(exc).__name__)
                    image["bucket_error"] = "Storage unavailable; inline image supplied."
            result = {
                "success": True, "images_generated": 1,
                "images_in_bucket": int(image["stored_in_bucket"]),
                "bucket_name": self._bucket_name if image["stored_in_bucket"] else None,
                "images": [image], "reference_image_base64": image["base64"],
            }
            return json.dumps(result)
        except Exception as exc:
            logger.warning("Image generation failed (%s). Check credentials, quota and model access.", type(exc).__name__)
            return json.dumps({"success": False, "error": f"Image generation failed ({type(exc).__name__}). Check backend configuration and model access."})

    def _generate_sync(self, prompt: str, aspect_ratio: str, reference: bytes | None) -> dict:
        contents: list[Any] = [types.Part.from_text(text=prompt)]
        if reference:
            contents.append(types.Part.from_bytes(data=reference, mime_type="image/png"))
        response = self._client.models.generate_content(
            model=self._model_name,
            contents=contents,
            config=types.GenerateContentConfig(
                response_modalities=["IMAGE"],
                image_config=types.ImageConfig(aspect_ratio=aspect_ratio, output_mime_type="image/png"),
                safety_settings=[types.SafetySetting(category=category, threshold="BLOCK_MEDIUM_AND_ABOVE")
                                 for category in ("HARM_CATEGORY_HARASSMENT", "HARM_CATEGORY_HATE_SPEECH",
                                                  "HARM_CATEGORY_SEXUALLY_EXPLICIT", "HARM_CATEGORY_DANGEROUS_CONTENT")],
            ),
        )
        for candidate in response.candidates or []:
            if not candidate.content:
                continue
            for part in candidate.content.parts or []:
                if part.thought:
                    continue
                inline = part.inline_data
                if inline and inline.data and (inline.mime_type or "image/png").startswith("image/"):
                    return {"data": inline.data}
        raise ValueError("The image model returned no usable image (it may have been blocked by safety filters).")

    def _store(self, data: bytes) -> str:
        """Upload privately; return a short-lived read URL, never change bucket ACLs."""
        blob = self._storage_client.bucket(self._bucket_name).blob(f"generated_images/{uuid.uuid4().hex}.png")
        blob.upload_from_string(data, content_type="image/png")
        ttl = max(60, min(86400, int(os.getenv("IMAGE_URL_TTL_SECONDS", "3600"))))
        return blob.generate_signed_url(version="v4", expiration=timedelta(seconds=ttl), method="GET")
