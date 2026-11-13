#!/usr/bin/env python3
"""Sync shared six-scene code into every standalone workshop snapshot.

Run from any directory: python tools/sync_workshop.py
Use --check in CI. Empty 'Ready' agent exercises are deliberately left empty.
"""
from __future__ import annotations

import argparse
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SHARED = ROOT / "shared"


def agent_source(variable: str) -> str:
    return f'''import os

from google.adk.agents import LlmAgent

from .story_contract import DEFAULT_STORY_MODEL, STORY_INSTRUCTION, StoryOutput

tools = []

{variable} = LlmAgent(
    model=os.getenv("STORY_MODEL", DEFAULT_STORY_MODEL),
    name="story_agent",
    description="Creates a validated six-scene illustrated story for children.",
    instruction=STORY_INSTRUCTION,
    output_schema=StoryOutput,
    tools=tools,
)
'''


def image_llm_source() -> str:
    return '''import logging
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
'''


def targets():
    for backend in sorted(ROOT.glob("0*/backend")):
        package = backend / "story_agent"
        yield SHARED / "backend/story_contract.py", package / "story_contract.py"
        yield SHARED / "backend/story_generation.py", package / "story_generation.py"
        yield SHARED / "backend/story_options.py", package / "story_options.py"
        yield SHARED / "backend/payment_verification.py", package / "payment_verification.py"
        yield SHARED / "backend/requirements.txt", backend / "requirements.txt"
        yield SHARED / "backend/README.md", backend / "README.md"
        if (package / "agent.py").exists() and (package / "agent.py").read_text().strip() not in ("", "root_agent = None"):
            yield agent_source("root_agent"), package / "agent.py"
        if (package / "story_text_agent.py").exists():
            yield agent_source("story_agent") + "\nroot_agent = story_agent\n", package / "story_text_agent.py"
        for image_package in (package, backend / "story_image_agent"):
            if (image_package / "imagen_tool.py").exists():
                yield SHARED / "backend/story_contract.py", image_package / "story_contract.py"
                yield SHARED / "backend/imagen_tool.py", image_package / "imagen_tool.py"
        for name in ("story_image_agent.py", "story_image_function.py"):
            if (package / name).exists():
                yield SHARED / "backend/direct_image_agent.py", package / name
        if (package / "image_agent.py").exists():
            yield image_llm_source(), package / "image_agent.py"
        custom = backend / "story_image_agent/agent.py"
        if custom.exists() and custom.read_text().strip() not in ("", "root_agent = None"):
            yield SHARED / "backend/custom_image_agent.py", custom
        frontend = backend.parent / "frontend"
        if frontend.exists():
            yield SHARED / "frontend/story-contract.ts", frontend / "lib/story-contract.ts"
            yield SHARED / "frontend/use-story-socket.ts", frontend / "lib/use-story-socket.ts"
            yield SHARED / "frontend/story-frames.tsx", frontend / "components/story-frames.tsx"
            yield SHARED / "frontend/image-keyframes.tsx", frontend / "components/image-keyframes.tsx"
            yield SHARED / "frontend/page.tsx", frontend / "app/page.tsx"
            yield SHARED / "frontend/layout.tsx", frontend / "app/layout.tsx"
    yield SHARED / "backend/requirements.txt", ROOT / "00_Starting_Here/requirements.txt"


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--check", action="store_true")
    args = parser.parse_args()
    changed = []
    for source, destination in targets():
        content = source if isinstance(source, str) else source.read_text()
        if not destination.exists() or destination.read_text() != content:
            changed.append(str(destination.relative_to(ROOT)))
            if not args.check:
                destination.parent.mkdir(parents=True, exist_ok=True)
                destination.write_text(content)
    if changed:
        print(("Out of sync: " if args.check else "Updated: ") + ", ".join(changed))
    else:
        print("All workshop snapshots are in sync.")
    return int(args.check and bool(changed))


if __name__ == "__main__":
    raise SystemExit(main())
