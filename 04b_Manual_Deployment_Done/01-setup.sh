#!/bin/bash
set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

echo -e "${BLUE}🔧 StoryGen Setup - Prerequisites & Authentication${NC}"
echo "=================================================="

# Load environment variables
if [ -f "./load-env.sh" ]; then
    source ./load-env.sh
else
    echo -e "${YELLOW}⚠️ load-env.sh not found. Some environment variables may not be loaded.${NC}"
fi

echo ""
echo -e "${BLUE}🔐 Checking Authentication Status${NC}"
echo "================================="

# Check required tools
echo -e "${BLUE}🔍 Checking prerequisites...${NC}"

if ! command -v gcloud &> /dev/null; then
    echo -e "${RED}❌ gcloud CLI not found${NC}"
    echo "Please install: https://cloud.google.com/sdk/docs/install"
    exit 1
fi
echo -e "${GREEN}✅ gcloud CLI found${NC}"

if ! command -v terraform &> /dev/null; then
    echo -e "${RED}❌ terraform not found. Please install Terraform.${NC}"
    exit 1
fi
echo -e "${GREEN}✅ terraform found${NC}"

# Check authentication
echo -e "${BLUE}🔐 Checking authentication...${NC}"
if ! gcloud auth list --filter=status:ACTIVE --format="value(account)" | head -n1 > /dev/null 2>&1; then
    echo -e "${RED}❌ No active gcloud authentication found.${NC}"
    echo "Please run: gcloud auth login && gcloud auth application-default login"
    exit 1
fi

CURRENT_ACCOUNT=$(gcloud auth list --filter=status:ACTIVE --format="value(account)" | head -n1)
echo -e "${GREEN}✅ Authenticated as: ${CURRENT_ACCOUNT}${NC}"

# Validate project configuration
echo -e "${BLUE}⚙️ Setting up project configuration...${NC}"

# Check if PROJECT_ID is set from environment
if [ -z "$PROJECT_ID" ]; then
    # Try to get current project if not set in environment
    PROJECT_ID=$(gcloud config get-value project 2>/dev/null || echo "")
    if [ -z "$PROJECT_ID" ]; then
        echo -e "${RED}❌ No PROJECT_ID found in environment or gcloud config${NC}"
        echo "Please set PROJECT_ID in your .env file or run: gcloud config set project PROJECT_ID"
        exit 1
    fi
fi

echo -e "${GREEN}✅ Using project: ${PROJECT_ID}${NC}"

# Validate project access
echo "🔍 Validating project access..."
if ! gcloud projects describe "$PROJECT_ID" > /dev/null 2>&1; then
    echo -e "${RED}❌ Project '$PROJECT_ID' not accessible or doesn't exist${NC}"
    echo "Please check the project ID and ensure you have access."
    exit 1
fi
echo -e "${GREEN}✅ Project '$PROJECT_ID' is accessible${NC}"

# Set project
gcloud config set project "$PROJECT_ID"

# Set default values for environment variables if not already set
REGION=${REGION:-"us-central1"}
ARTIFACT_REPO=${ARTIFACT_REPO:-"storygen-repo"}
SECRET_NAME=${SECRET_NAME:-"google-api-key"}

# Enable required APIs
echo -e "${BLUE}🔌 Enabling required APIs...${NC}"
gcloud services enable \
    run.googleapis.com \
    cloudbuild.googleapis.com \
    artifactregistry.googleapis.com \
    aiplatform.googleapis.com \
    storage.googleapis.com \
    secretmanager.googleapis.com \
    --project="$PROJECT_ID"
echo -e "${GREEN}✅ APIs enabled${NC}"

# Create Artifact Registry repository
echo -e "${BLUE}🏗️ Setting up Artifact Registry...${NC}"
if gcloud artifacts repositories create "$ARTIFACT_REPO" \
    --repository-format=docker \
    --location="$REGION" \
    --description="Docker repository for StoryGen application" \
    --project="$PROJECT_ID" 2>/dev/null; then
    echo -e "${GREEN}✅ Artifact Registry repository created${NC}"
else
    echo -e "${YELLOW}✅ Repository already exists${NC}"
fi

# Configure Docker authentication
echo "🔐 Configuring Docker authentication..."
gcloud auth configure-docker "${REGION}-docker.pkg.dev"
echo -e "${GREEN}✅ Docker authentication configured${NC}"

# Create Secret Manager secret for API key
echo -e "${BLUE}🔐 Setting up Secret Manager...${NC}"
if ! gcloud secrets describe "$SECRET_NAME" --project="$PROJECT_ID" &>/dev/null; then
    echo "✨ Creating secret '$SECRET_NAME'..."
    gcloud secrets create "$SECRET_NAME" \
        --replication-policy="automatic" \
        --project="$PROJECT_ID"
    
    if [ -n "$GOOGLE_API_KEY" ]; then
        echo "🔑 Using API key from .env file..."
        echo "📦 Adding API key to secret..."
        printf '%s' "$GOOGLE_API_KEY" | gcloud secrets versions add "$SECRET_NAME" --data-file=- --project="$PROJECT_ID"
        echo -e "${GREEN}✅ API key added to Secret Manager successfully${NC}"
    else
        echo -e "${RED}❌ GOOGLE_API_KEY not found in .env file${NC}"
        echo "Please add GOOGLE_API_KEY to your .env file and run this script again."
        exit 1
    fi
else
    echo -e "${GREEN}✅ Secret '$SECRET_NAME' already exists.${NC}"
    
    # Update secret with current API key from .env
    if [ -n "$GOOGLE_API_KEY" ]; then
        echo "🔄 Updating secret with API key from .env file..."
        printf '%s' "$GOOGLE_API_KEY" | gcloud secrets versions add "$SECRET_NAME" --data-file=- --project="$PROJECT_ID"
        echo -e "${GREEN}✅ Secret updated with latest API key${NC}"
    else
        echo -e "${YELLOW}⚠️ GOOGLE_API_KEY not found in .env file - secret not updated${NC}"
    fi
fi

# Generate providers.tf from template
if [ -f "./terraform_code/providers.tf.tpl" ]; then
    echo -e "${BLUE}📝 Generating terraform providers file...${NC}"
    sed "s/PROJECT_ID_PLACEHOLDER/$PROJECT_ID/g" ./terraform_code/providers.tf.tpl > ./terraform_code/providers.tf
    echo -e "${GREEN}✅ Terraform providers file generated${NC}"
else
    echo -e "${YELLOW}⚠️ Terraform providers template not found at ./terraform_code/providers.tf.tpl${NC}"
fi

echo ""
echo -e "${GREEN}🎉 Setup complete!${NC}"
echo -e "${BLUE}📋 Configuration Summary:${NC}"
echo "   Account: $CURRENT_ACCOUNT"
echo "   Project ID: $PROJECT_ID"
echo "   Region: $REGION"
echo "   Artifact Repo: $ARTIFACT_REPO"
echo "   Secret: $SECRET_NAME"
echo ""
echo -e "${BLUE}🎯 Next step: Run ./02-build-images.sh${NC}"