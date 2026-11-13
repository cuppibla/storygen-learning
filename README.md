# StoryGen — six-scene illustrated stories

StoryGen creates gentle illustrated children's stories using Google Gemini for text, Google Gemini Image for illustrations, FastAPI/WebSockets for progress, and Next.js for the reader. The current UI offers a **four-scene free story**; the six-scene personalised upgrade is not yet available.

## The six-scene arc

| Scene | Beat | Purpose |
|---|---|---|
| 1 | Setup | Introduce the character, world, and what matters |
| 2 | Inciting Incident | A discovery or problem changes the plan |
| 3 | First Attempt | The character tries a concrete plan |
| 4 | Setback | The plan hits a complication; pause, feel, rethink |
| 5 | Climax | Use what was learned in the decisive attempt |
| 6 | Resolution | Show the result and emotional payoff |

The default story is 180–270 words for ages 4–8. Each scene has a stable index, beat, descriptive title, visible action, character cast, and 25–50 words of story text. The backend validates the complete contract before generating images and allows one corrective model turn for invalid structure.

Illustrations use a locked style, scene-specific character lists, and the first successful illustration as a reference for later scenes. This improves continuity but does **not** guarantee identical characters.

**Monetisation status:** Free four-scene generation is connected to the chooser; Upgrade is explicitly marked unavailable. The legacy six-scene keyword API still exists as an unauthenticated workshop demo, not a paid or protected product. Stripe Checkout, verified entitlements and purchase recovery are not implemented; do not accept payments or advertise those features yet. See [REVIEW.md](REVIEW.md).

## Start here

- **[SETUP.md](SETUP.md)** — where to put credentials, local startup, model settings, and deployment checklist.
- **[REVIEW.md](REVIEW.md)** — what changed, why, verification, and remaining production risks.
- **`04b_Manual_Deployment_Done/`** — the complete deployment snapshot used by the workshop CI/CD example.

There is no root Docker Compose application. Run a chosen snapshot directly, or use its Dockerfiles. The old root quick-start instructions referred to files that were not present.

## Workshop snapshots

| Folder | Purpose |
|---|---|
| `00_Starting_Here` | Shared Python requirements and authentication helpers |
| `01a` / `01b` | First story-agent exercise / completed agent |
| `02a` / `02b` | Image-agent exercise / completed agent |
| `03a` / `03b` | Evaluation exercise / completed evaluation fixtures |
| `04a` / `04b` | Manual deployment exercise / completed deployment |
| `05a` | CI/CD-ready application snapshot |
| `06_Final_Solution` | CI/CD configuration and deployment workflow templates |

The intentional `root_agent = None` exercises remain in the Ready snapshots. Shared contract/UI code is maintained in `shared/` and copied into each standalone snapshot so Docker build contexts remain self-contained:

```bash
python tools/sync_workshop.py
python tools/sync_workshop.py --check
```

## Checks

```bash
python -m pip install -r requirements-dev.txt
python -m pytest -q
npm test
python tools/sync_workshop.py --check
# After npm ci in 04b's frontend:
npm run test:render
```

Frontend type-check/build for the deployment snapshot:

```bash
cd 04b_Manual_Deployment_Done/frontend
npm ci
npx tsc --noEmit
npm run build
```

The root GitHub Actions workflow runs credential-free checks. The deployment workflow under `06_Final_Solution/.github/` is a workshop template; it is not activated merely by being nested in this repository. No cloud deployment is performed by the test workflow.

## Configuration and safety

Never put API keys in `NEXT_PUBLIC_*` variables, frontend files, Git, or chat. Use the backend `.env` file locally and Secret Manager/ADC in production. See [SETUP.md](SETUP.md).

Generated images are sent inline or stored privately with short-lived signed URLs. The application does not make image objects public. The demo backend is still unauthenticated: add authentication, rate limits, budget controls, and a retention policy before offering it to the public.
