# StoryGen review and upgrade

**Scope:** all nine workshop snapshots, the runnable deployment application, evaluation fixtures, and documentation.
**Decision:** six scenes, a balanced adventure arc, Google Gemini text + Google Gemini Image, credentials outside Git.
**Review date:** 2026-11-13.

## Verdict

The original idea is sound: generate the story first, establish a visual identity, then illustrate each scene while showing progress. The implementation needed more than changing “4” to “6”: its prompt, validation, image protocol, UI layout, fixtures, and deployment assumptions all encoded the old structure or obsolete services.

The upgraded code now treats the story as a typed contract shared by the backend and frontend. It is suitable for a credentialed workshop/demo, **not yet an unauthenticated public children's service**.

**Monetisation is incomplete.** The UI now presents Free and Upgrade; Free requests a complete four-scene story, while Upgrade is clearly unavailable. All backend entrypoints support the free request; the existing six-scene keyword API remains a workshop demo and is not protected as a paid product. Personalised generation and exact-match payment verification have been added as isolated, tested building blocks, but are not exposed by the app. Stripe Checkout, durable orders and entitlements, webhook verification, refunds, purchase recovery and pricing in the UI are not implemented. Do not accept payments or deploy this as a paid service. The Secret Manager resource documented in SETUP.md has not been verified or bound to Cloud Run. A future implementation must fetch sessions from Stripe itself, preserve purchases across disconnects and retries, verify Stripe payment server-side, and prevent duplicate fulfilment before enabling checkout.

## Findings that drove the changes

| Priority | Finding | Resolution |
|---|---|---|
| High | Four-scene prompts and hardcoded UI assumptions would produce incomplete or misaligned six-scene output | One six-scene schema and one shared frontend constant; validation before image spend |
| High | Legacy Imagen endpoints/model IDs are no longer an appropriate implementation target | Gemini image `generate_content` adapter; configurable current model defaults |
| High | Public image access and inconsistent secret instructions increased privacy and credential risk | Private storage + signed URLs, inline fallback, Secret Manager/ADC instructions, ignored local env files |
| High | Workshop copies could drift and CI could deploy code that had not passed checks | Canonical shared modules, synchronization check, credential-free CI gate |
| Medium | Image arrival order could be mistaken for scene order | Explicit zero-based image indices and six fixed UI slots |
| Medium | An image failure could hide or discard useful story output | Story delivered first; per-scene error placeholders; remaining scenes continue |
| Medium | Frontend builds depended on downloading fonts and suppressed TypeScript errors | System fonts and strict TypeScript build checking |
| High | Deployment template specified a different image model from the shared default | Aligned the template and fallback with the configured default and added a regression test |
| High | Untagged WebSocket events could update the active story | Require the active request ID for story events |
| Critical | The original Next.js release was flagged by npm audit | Updated all nine snapshots to Next.js 15.5.29; further advisories remain |

## Narrative design

The selected arc is **Setup → Inciting Incident → First Attempt → Setback → Climax → Resolution**. The middle two scenes give the protagonist a concrete attempt and a recoverable complication rather than jumping directly from discovery to victory.

Contract rules:

- Exactly six scenes, indices 1–6, each with the prescribed beat.
- 180–270 words total; 25–50 words per scene.
- One or two recurring characters, at most two active characters per scene.
- Descriptive titles, visible actions, and text that joins back to the complete story.
- Gentle, age-appropriate content for ages 4–8; no moralizing epilogue outside the story.
- One bounded repair turn for invalid structure, not unlimited retries on provider failures.

This makes failures diagnosable and keeps illustration costs tied to validated output. It does not prove literary quality or child safety; live evaluation remains necessary.

## Google model decision

The default text model is `gemini-3.8-flash`, listed by Google as a stable model with structured-output support. [1](https://ai.google.dev/gemini-api/docs/models/gemini-3.8-flash)

The default image model is **`gemini-nano-banana-2.1`**, not the cheaper Lite image model. Google's image-generation guidance describes 2.1 as the high-efficiency model for generation/editing and improved multi-turn consistency; Lite is not optimized for multiple reference inputs or sequential editing. That distinction matters for a recurring story cast. [2](https://ai.google.dev/gemini-api/docs/generate-content/image-generation) Google's lifecycle page lists 2.1 with no announced shutdown date and recommends migrating from the deprecated `gemini-3.1-flash-image`. [1](https://ai.google.dev/gemini-api/docs/deprecations)

The adapter uses `client.models.generate_content`, requests image output with `ImageConfig`, and reads inline image parts. It can include the first successful illustration as a reference in subsequent calls. The historical class/file name `ImagenTool` / `imagen_tool.py` remains for lesson compatibility; it no longer calls Imagen.

Model IDs and availability are environment configuration. Verify access in the actual AI Studio account or Vertex project/location before deployment; the offline suite cannot establish that access.

## Implementation map

- `shared/backend/story_contract.py`: typed schema, arc, prompt, parser, image prompt, example story.
- `shared/backend/story_generation.py`: four-scene free and six-scene keyword/personalised generation paths, fresh session, timeout, one schema-repair turn. Personalised generation is not exposed by the app.
- `shared/backend/payment_verification.py`: exact-match checks for a server-fetched paid Stripe Checkout session; not a checkout integration or entitlement store.
- `shared/backend/imagen_tool.py`: Gemini image adapter, off-loop calls, private storage/fallback.
- `shared/backend/{direct_image_agent,custom_image_agent}.py`: compatible image-agent interfaces.
- `shared/frontend/`: Free/Upgrade chooser, four- or six-slot reader, marker parser, indexed image placement, request-scoped WebSocket hook.
- `tools/sync_workshop.py`: propagates shared code while preserving intentional learner stubs.
- `tools/update_eval_fixtures.py`: regenerates valid six-scene story goldens.
- `tests/`: Python contract/workflow/WebSocket checks, Node contract tests, React SSR checks.

The complete deployment snapshot is `04b_Manual_Deployment_Done`. The `06_Final_Solution` folder supplies CI/CD templates for that snapshot. Early static-export frontends are run locally; deployment Dockerfiles are supplied for the later application snapshots.

## Verification performed

| Check | Result |
|---|---|
| Python suite | **101 passed** (one Starlette/httpx deprecation warning) |
| Node story-contract tests | **9 passed** |
| React SSR regression | Passed: six cards, beats, indexed images, error/unsegmented states |
| Shared-copy consistency | Passed |
| `01a` frontend type-check + production build | Passed |
| `04b` frontend type-check + production build | Passed |
| Python compilation / shell syntax / workflow YAML parsing | Passed |

Tests cover missing/duplicate/out-of-order scenes, boolean indices, word counts, cast limits, repair behavior, image indexing, stale request IDs, partial image failures, and unconfigured image generation. Fixtures are deterministic and require no credentials.

**Not performed:** live Gemini calls, real image-quality/character-consistency evaluation, Docker image builds, Terraform apply, or cloud deployment. Docker/gcloud and project credentials were not available. One non-fatal Starlette/httpx deprecation warning remains in the Python test environment.

## Remaining production risks

1. **Unauthenticated paid endpoint.** Add authentication, per-user/IP quotas, concurrency limits, request cancellation, and budget alerts before public exposure. CORS is not authentication; credentialed wildcard CORS was removed, but WebSocket origin/access controls still need a production policy.
2. **Latency and cost.** Six images are generated sequentially to preserve a reference chain. Defaults are 60 seconds per text/image call and a 600-second Cloud Run request timeout; a repair plus six slow images can still approach that limit. Measure p50/p95 latency and consider a background job queue with resumable progress.
3. **Existing cloud access.** The manual deployment script still contains an `allUsers` Cloud Run invoker grant for the demo. Remove/replace it for a private deployment. Audit existing buckets separately; new application code does not make objects public.
4. **Tracked Terraform state.** `04a_Manual_Deployment_Ready/terraform_code/terraform.tfstate` was already tracked. It was not printed or rewritten here. Inspect it privately for sensitive values, migrate to a protected remote backend, and remove it from tracking/history according to the repository's security process. Ignore rules do not untrack existing files.
5. **Children's privacy and retention.** Keywords and generated images may contain personal information. Define consent, minimization, logging, retention/deletion, abuse handling, and regional requirements before collecting real children's input.
6. **Quality and continuity.** A reference image improves consistency but does not guarantee it. Run the updated evaluation cases with live credentials and add human review for age suitability, scene causality, visual alignment, and representation.
7. **Deployment identity.** The supplied templates still need project-specific IAM review, especially runtime versus deployer roles, secret access, signing permission, and Workload Identity Federation repository restrictions.
8. **Dependency advisories.** On 2026-11-13, `npm audit --omit=dev` reported zero advisories for each snapshot after dependency updates. A full audit of each snapshot still reported six moderate development-tool advisories involving minimatch and TypeScript ESLint. Monitor upstream fixes and review before deployment. Audits reflect known advisories at the time of the check, not a guarantee of safety. Dependency upgrades include major changes to Zod and its React Hook Form resolver, plus overrides for PostCSS and the selector parser; check workshop extensions that use them.

## Credential placement

See **[SETUP.md](SETUP.md)**. In short: backend `.env` locally, Secret Manager or Application Default Credentials in production, and only the public backend URL in frontend build configuration. Never place keys in chat, Git, Terraform variables/state, or `NEXT_PUBLIC_*` variables.

## Recommended next milestone

Run one live six-scene smoke test using the completed snapshot and record latency, cost and continuity failures. Then implement the four-scene free workflow and purchase flow with server-verified Stripe payments, durable entitlements and purchase recovery; test it in Stripe test mode before accepting real money. Add authentication, quotas and durable jobs before expanding access. Keep the workshop snapshots synchronized and credential-free checks as the merge gate.
