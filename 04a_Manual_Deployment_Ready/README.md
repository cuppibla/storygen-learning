# Manual deployment — six-scene StoryGen

This is the deployment exercise snapshot. The completed version is `../04b_Manual_Deployment_Done`; the CI/CD template deploys that completed snapshot.

The application now generates exactly six scenes: Setup → Inciting Incident → First Attempt → Setback → Climax → Resolution. Text uses Google Gemini; illustrations use the Google Gemini image API through the legacy `ImagenTool` adapter name.

Follow the repository-level `../SETUP.md` for credentials and local startup, and `../REVIEW.md` for deployment caveats. This folder contains standalone backend/frontend Dockerfiles; there is no Docker Compose file here.

Before deploying: configure the backend secret, private image bucket (optional), runtime IAM, and the frontend's public backend URL as a build argument. Review public endpoint access, quota, retention, and the tracked Terraform state noted in the review.
