#!/bin/bash

# 🔧 StoryGen CI/CD Configuration Generator
# =========================================
# This script generates the deployment configuration file for GitHub Actions CI/CD
# 
# Prerequisites:
# 1. Run ./setup-direct.sh first (sets up GCP infrastructure)
# 2. Run ./setup-api-key.sh (sets up Gemini API key)
# 3. Have a .env file in parent directory with your configuration
#
# Usage:
#   ./setup-cicd-config.sh
#
# What this script does:
# • Reads your .env configuration
# • Validates that infrastructure exists 
# • Generates .github/config/deployment.yml for CI/CD
# • Enables environment-based CI/CD (no GitHub variables needed!)

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
CYAN='\033[0;36m'
NC='\033[0m' # No Color

echo -e "${CYAN}🔧 StoryGen CI/CD Configuration Generator${NC}"
echo -e "${CYAN}==========================================${NC}"
echo ""

# Load .env file
ENV_FILE="../.env"
if [ ! -f "$ENV_FILE" ]; then
    echo -e "${RED}❌ Environment file not found: $ENV_FILE${NC}"
    echo "Please ensure you have a .env file in the parent directory."
    echo "You can copy from .env.template and customize for your project."
    exit 1
fi

echo -e "${GREEN}🔧 Loading configuration from $ENV_FILE${NC}"
# Load environment variables, ignoring comments and empty lines
# export $(grep -v '^#' "$ENV_FILE" | grep -v '^$' | xargs)
export $(grep -E '^[a-zA-Z_]+\w*=' "$ENV_FILE")

# Validate required variables
if [ -z "$GOOGLE_CLOUD_PROJECT_ID" ]; then
    echo -e "${RED}❌ GOOGLE_CLOUD_PROJECT_ID not found in .env file${NC}"
    exit 1
fi

if [ -z "$GITHUB_USERNAME" ]; then
    echo -e "${RED}❌ GITHUB_USERNAME not found in .env file${NC}"
    exit 1
fi

if [ -z "$GITHUB_REPO" ]; then
    echo -e "${RED}❌ GITHUB_REPO not found in .env file${NC}"
    exit 1
fi

if [ -z "$GENMEDIA_BUCKET" ]; then
    echo -e "${RED}❌ GENMEDIA_BUCKET not found in .env file${NC}"
    exit 1
fi

if [ -z "$SECRET_MANAGER" ]; then
    echo -e "${RED}❌ SECRET_MANAGER not found in .env file${NC}"
    exit 1
fi

PROJECT_ID="$GOOGLE_CLOUD_PROJECT_ID"
REGION="${REGION:-us-central1}"
BUCKET_NAME="$GENMEDIA_BUCKET"
SECRET_NAME="$SECRET_MANAGER"

echo -e "${BLUE}📋 Configuration Summary:${NC}"
echo "  Project ID: $PROJECT_ID"
echo "  GitHub: $GITHUB_USERNAME/$GITHUB_REPO"
echo "  Region: $REGION"
echo "  Bucket: $BUCKET_NAME"
echo "  Secret: $SECRET_NAME"
echo ""

# Prerequisites check
echo -e "${BLUE}📋 Checking Prerequisites${NC}"
echo "=========================="

# Check gcloud CLI
if ! command -v gcloud &> /dev/null; then
    echo -e "${RED}❌ gcloud CLI not found${NC}"
    echo "Please install: https://cloud.google.com/sdk/docs/install"
    exit 1
fi
echo -e "${GREEN}✅ gcloud CLI found${NC}"

# Check authentication
if ! gcloud auth list --filter=status:ACTIVE --format="value(account)" | head -n1 > /dev/null 2>&1; then
    echo -e "${RED}❌ Not authenticated with gcloud${NC}"
    echo "Please run: gcloud auth login"
    exit 1
fi

CURRENT_ACCOUNT=$(gcloud auth list --filter=status:ACTIVE --format="value(account)" | head -n1)
echo -e "${GREEN}✅ Authenticated as: ${CURRENT_ACCOUNT}${NC}"

# Validate project access
echo "🔍 Validating project access..."
if ! gcloud projects describe "$PROJECT_ID" > /dev/null 2>&1; then
    echo -e "${RED}❌ Project '$PROJECT_ID' not accessible or doesn't exist${NC}"
    echo "Please check the project ID and ensure you have access."
    exit 1
fi
echo -e "${GREEN}✅ Project '$PROJECT_ID' is accessible${NC}"

# Get project number for Workload Identity Provider
PROJECT_NUMBER=$(gcloud projects describe "$PROJECT_ID" --format="value(projectNumber)" 2>/dev/null || echo "")

if [ -z "$PROJECT_NUMBER" ]; then
    echo -e "${RED}❌ Could not get project number${NC}"
    exit 1
fi

echo -e "${GREEN}✅ Project number: $PROJECT_NUMBER${NC}"

# Check if infrastructure exists (from setup-direct.sh)
echo ""
echo -e "${BLUE}🔍 Validating Infrastructure${NC}"
echo "============================="

# Check Workload Identity Pool
if ! gcloud iam workload-identity-pools describe "github-pool" \
   --project="$PROJECT_ID" --location="global" > /dev/null 2>&1; then
    echo -e "${RED}❌ Workload Identity Pool 'github-pool' not found${NC}"
    echo "Please run: ./setup-direct.sh first"
    exit 1
fi
echo -e "${GREEN}✅ Workload Identity Pool exists${NC}"

# Check Workload Identity Provider
PROVIDER_NAME="github-provider-fixed"
if ! gcloud iam workload-identity-pools providers describe "$PROVIDER_NAME" \
   --project="$PROJECT_ID" --location="global" \
   --workload-identity-pool="github-pool" > /dev/null 2>&1; then
    echo -e "${RED}❌ Workload Identity Provider '$PROVIDER_NAME' not found${NC}"
    echo "Please run: ./setup-direct.sh first"
    exit 1
fi
echo -e "${GREEN}✅ Workload Identity Provider exists${NC}"

# Check service account
SERVICE_ACCOUNT_EMAIL="github-actions@${PROJECT_ID}.iam.gserviceaccount.com"
if ! gcloud iam service-accounts describe "$SERVICE_ACCOUNT_EMAIL" \
   --project="$PROJECT_ID" > /dev/null 2>&1; then
    echo -e "${RED}❌ Service Account '$SERVICE_ACCOUNT_EMAIL' not found${NC}"
    echo "Please run: ./setup-direct.sh first"
    exit 1
fi
echo -e "${GREEN}✅ Service Account exists${NC}"

# Check storage bucket
if ! gsutil ls -b gs://"$BUCKET_NAME" > /dev/null 2>&1; then
    echo -e "${RED}❌ Storage bucket 'gs://$BUCKET_NAME' not found${NC}"
    echo "Please run: ./setup-direct.sh first"
    exit 1
fi
echo -e "${GREEN}✅ Storage bucket exists${NC}"

# Check secret manager
if ! gcloud secrets describe "$SECRET_NAME" --project="$PROJECT_ID" > /dev/null 2>&1; then
    echo -e "${RED}❌ Secret '$SECRET_NAME' not found in Secret Manager${NC}"
    echo "Please run: ./setup-direct.sh first"
    exit 1
fi
echo -e "${GREEN}✅ Secret Manager secret exists${NC}"

# Check if API key is set in Secret Manager
if ! gcloud secrets versions list "$SECRET_NAME" --project="$PROJECT_ID" --format="value(name)" | head -n1 > /dev/null 2>&1; then
    echo -e "${YELLOW}⚠️ No API key versions found in Secret Manager${NC}"
    echo "Please run: ./setup-api-key.sh to add your Gemini API key"
    echo ""
else
    echo -e "${GREEN}✅ API key exists in Secret Manager${NC}"
fi

# Generate CI/CD deployment configuration file
echo ""
echo -e "${BLUE}📝 Generating CI/CD Configuration${NC}"
echo "=================================="

CONFIG_FILE="../.github/config/deployment.yml"
mkdir -p "$(dirname "$CONFIG_FILE")"

WORKLOAD_IDENTITY_PROVIDER="projects/$PROJECT_NUMBER/locations/global/workloadIdentityPools/github-pool/providers/$PROVIDER_NAME"

cat > "$CONFIG_FILE" << EOF
# StoryGen CI/CD Deployment Configuration
# Generated by setup-cicd-config.sh on $(date)
# DO NOT edit manually - regenerate using: ./00_Starting_Here/setup-cicd-config.sh
#
# This configuration deploys from: 04b_Manual_Deployment_Done/
# - Backend: 04b_Manual_Deployment_Done/backend/
# - Frontend: 04b_Manual_Deployment_Done/frontend/

# Project-specific authentication values
project_id: "$PROJECT_ID"
workload_identity_provider: "$WORKLOAD_IDENTITY_PROVIDER"
service_account_email: "$SERVICE_ACCOUNT_EMAIL"

# Resource names
genmedia_bucket: "$BUCKET_NAME"
secret_manager: "$SECRET_NAME"

# Optional configuration (can be overridden with GitHub variables)
gcp_region: "$REGION"
story_model: "${STORY_MODEL:-gemini-3.8-flash}"
image_model: "${IMAGE_MODEL:-gemini-nano-banana-2.1}"
artifact_repo: "storygen-repo"
backend_service_name: "genai-backend"
frontend_service_name: "genai-frontend"
backend_image_name: "storygen-backend"
frontend_image_name: "storygen-frontend"
backend_memory: "2Gi"
backend_cpu: "2000m"
frontend_memory: "1Gi"
frontend_cpu: "1000m"
min_instances: "0"
max_instances: "2"
EOF

echo -e "${GREEN}✅ CI/CD configuration saved to: $CONFIG_FILE${NC}"

# Display what was generated
echo ""
echo -e "${CYAN}📋 Generated Configuration:${NC}"
echo "=========================="
cat "$CONFIG_FILE"

echo ""
echo -e "${GREEN}🎉 CI/CD Configuration Complete!${NC}"
echo "=================================="
echo ""
echo -e "${YELLOW}🚀 Next Steps:${NC}"
echo "1. Commit and push the configuration file:"
echo -e "   ${BLUE}git add .github/config/deployment.yml${NC}"
echo -e "   ${BLUE}git commit -m \"Add CI/CD deployment configuration\"${NC}"
echo -e "   ${BLUE}git push origin main${NC}"
echo ""
echo "2. Your CI/CD pipeline will now work automatically!"
echo "   • ✅ No GitHub variables needed!"
echo "   • ✅ No manual configuration required!"
echo "   • ✅ Just push to main branch to deploy!"
echo ""
echo -e "${CYAN}📖 Benefits of this approach:${NC}"
echo "• 🔄 Portable: Works for any new user who runs the setup scripts"
echo "• 🔐 Secure: Uses Workload Identity (no secrets in GitHub)"
echo "• 🎯 Simple: No manual GitHub repository configuration needed"
echo "• 📝 Versioned: Configuration is tracked in git"
echo ""
echo -e "${GREEN}🎯 Ready to deploy! Push your changes and watch the magic! ✨${NC}"
