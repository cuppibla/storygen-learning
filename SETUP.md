# Setup and credential placement

No credentials are needed for the automated contract tests. A live story needs Google model access. **Do not paste keys into chat or commit them.**

## 1. Choose a snapshot

For the complete application:

```bash
cd 04b_Manual_Deployment_Done
```

Use Python 3.11+ and Node.js 22+. From the repository root:

```bash
python -m venv .venv
source .venv/bin/activate
pip install -r 04b_Manual_Deployment_Done/backend/requirements.txt
```

## 2. Backend credentials

Copy the root `env.template` into the **chosen snapshot's backend directory**:

```bash
cp env.template 04b_Manual_Deployment_Done/backend/.env
chmod 600 04b_Manual_Deployment_Done/backend/.env
```

Edit that file locally. `.env` is ignored by Git.

### Option A — Google AI Studio / Gemini Developer API (default)

```dotenv
GOOGLE_GENAI_USE_VERTEXAI=FALSE
GOOGLE_API_KEY=your_key_here
STORY_MODEL=gemini-3.8-flash
IMAGE_MODEL=gemini-nano-banana-2.1
```

Create a key in Google AI Studio and enable billing/quota as required by your account. Text and images both use this key. `GOOGLE_CLOUD_PROJECT_ID` and `GENMEDIA_BUCKET` are not required for inline images in this mode.

### Option B — Vertex AI / Gemini Enterprise Agent Platform

```dotenv
GOOGLE_GENAI_USE_VERTEXAI=TRUE
GOOGLE_CLOUD_PROJECT_ID=your_project_id
GOOGLE_CLOUD_LOCATION=us-central1
STORY_MODEL=gemini-3.8-flash
IMAGE_MODEL=gemini-nano-banana-2.1
```

Use Application Default Credentials rather than a downloaded key:

```bash
gcloud auth application-default login
gcloud auth application-default set-quota-project YOUR_PROJECT_ID
```

Enable the Vertex AI API and grant the runtime identity permission to use it. Verify that the chosen model IDs are available in your project/location. Model IDs are configuration, not credentials; override them if your project uses different supported models.

If you must use a service-account key file, store it **outside the repository**, restrict its permissions, and set `GOOGLE_APPLICATION_CREDENTIALS=/absolute/path/to/key.json`. On Cloud Run, prefer the service identity instead of key files.

## 3. Optional private image storage

Leave `GENMEDIA_BUCKET=` empty to send images inline. To store them:

```dotenv
GOOGLE_CLOUD_PROJECT_ID=your_project_id
GENMEDIA_BUCKET=your_private_bucket
IMAGE_URL_TTL_SECONDS=3600
```

The bucket must already exist. Grant the runtime identity `roles/storage.objectUser` on that bucket. Signed URLs also require signing permission; for Cloud Run IAM-based signing, grant the runtime service account `roles/iam.serviceAccountTokenCreator` on itself (or use an appropriately configured signing identity). If upload/signing fails, the generated image is still returned inline.

Do **not** grant `allUsers` access to generated images. Existing workshop buckets may already be public; audit and remove that access separately. Configure lifecycle deletion according to your privacy/retention policy. Signed URLs expire, but previously downloaded files cannot be recalled.

## 4. Frontend configuration

Each snapshot has `frontend/.env.example`. For local development:

```bash
cd 04b_Manual_Deployment_Done/frontend
cp .env.example .env.local
npm ci
```

```dotenv
NEXT_PUBLIC_BACKEND_URL=http://localhost:8000
```

This value is public and is compiled into the browser bundle. **Never put an API key in it.** For Docker/Cloud Run, pass `NEXT_PUBLIC_BACKEND_URL` as a **build argument**; setting only a runtime environment variable does not rebuild the bundle. The supplied frontend Dockerfile and Cloud Build config do this.

## 5. Run locally

Terminal 1, from the chosen backend directory with the virtual environment active:

```bash
uvicorn main:app --host 0.0.0.0 --port 8000 --reload
```

Terminal 2, from the chosen frontend directory:

```bash
npm run dev -- --hostname 0.0.0.0
```

Open the frontend URL, choose Free, select an adventure and optional fictional companion, and generate. The UI shows four scene slots. Upgrade is not available yet. The legacy six-scene keyword API is still available for workshop exercises but is not payment-protected. Image failures occupy the correct slot and do not discard the story. A disconnected WebSocket requires retrying generation after reconnect; unfinished jobs are not resumed.

For a remote/browser preview, set the frontend's public backend URL to the externally reachable HTTPS backend URL and rebuild/restart the frontend. Browser code must not use `localhost` to mean the remote sandbox. The backend must also permit the preview origin if you add an origin allowlist.

## 6. Production secret placement

The deployment workflow reads an **existing Secret Manager secret**, not a GitHub repository variable containing the key. Provision it locally without putting the value in shell history:

```bash
gcloud secrets create storygen-google-api-key --replication-policy=automatic
printf 'Paste key here locally: ' >&2
read -rs KEY; printf '\n' >&2
printf '%s' "$KEY" | gcloud secrets versions add storygen-google-api-key --data-file=-
unset KEY
```

Use the secret name in `SECRET_MANAGER` / the deployment config. Grant the **Cloud Run runtime service account** `roles/secretmanager.secretAccessor` on that secret. The deployment identity needs permission to read secret metadata and deploy; do not use a highly privileged deployment identity as the runtime identity.

In Vertex-only mode, the application can use the runtime service identity instead of `GOOGLE_API_KEY`; adjust the deployment's secret environment binding accordingly. The workshop's default deployment uses AI Studio plus Secret Manager.

### Stripe (integration not yet implemented)

The intended Stripe secret resource is `projects/296033530848/secrets/STRIPE_SECRET_KEY_STORYGEN`. This is a resource name, not the key itself. The existing deployment workflow does **not** bind it, and the application does not yet process payments. Do not accept payments until Checkout, server-side payment verification, durable entitlements, and refund/retry handling are implemented and tested.

When implementing deployment, grant the backend's Cloud Run runtime service account `roles/secretmanager.secretAccessor` on this secret and bind an enabled version to the backend as `STRIPE_SECRET_KEY`. If this is a different project from Cloud Run, use the fully qualified secret resource and configure cross-project access. Use a Stripe test-mode key for testing. A webhook signing secret, if webhooks are used, is a separate secret and must not be confused with the API key. Never expose either secret to frontend code, logs, GitHub files, or chat.

Before deploying, review `REVIEW.md`. The CI/CD template deploys `04b_Manual_Deployment_Done`, not the folder named `06_Final_Solution`. The backend request timeout is set to 600 seconds in the supplied deployment paths; six sequential image calls can still be slow. Add authentication, rate limits, spending caps/alerts, and monitoring before public use.

## 7. Verify

From the repository root:

```bash
pip install -r requirements-dev.txt
python -m pytest -q
npm test
python tools/sync_workshop.py --check
# After npm ci in 04b's frontend:
npm run test:render
```

These tests use fixtures/mocks and make no paid Google calls. After adding credentials, perform one live smoke test and inspect all six scenes for narrative causality, character continuity, age suitability, image/text alignment, and correct failure handling. Live model quality and project-specific model access are not established by the offline tests.
