#!/bin/bash
# =============================================================================
# build-and-push.sh — Build Docker image & push to Amazon ECR
# =============================================================================
# Prerequisites:
#   1. AWS CLI installed & configured (aws configure)
#   2. Docker installed
#   3. An ECR repository named "ai-conversation-studio" exists in your account
#
# Usage:
#   ./scripts/build-and-push.sh <AWS_ACCOUNT_ID> <REGION>
#
# Example:
#   ./scripts/build-and-push.sh 123456789012 us-east-1
# =============================================================================

set -euo pipefail

if [ "$#" -ne 2 ]; then
  echo "Usage: $0 <AWS_ACCOUNT_ID> <REGION>"
  echo "Example: $0 123456789012 us-east-1"
  exit 1
fi

AWS_ACCOUNT_ID="$1"
REGION="$2"
REPO_NAME="ai-conversation-studio"
IMAGE_TAG="latest"

# Full ECR image URI
ECR_URI="${AWS_ACCOUNT_ID}.dkr.ecr.${REGION}.amazonaws.com/${REPO_NAME}:${IMAGE_TAG}"

echo "=== Logging into Amazon ECR ==="
aws ecr get-login-password --region "${REGION}" \
  | docker login --username AWS --password-stdin "${AWS_ACCOUNT_ID}.dkr.ecr.${REGION}.amazonaws.com"

echo "=== Building Docker image ==="
docker build -t "${REPO_NAME}:${IMAGE_TAG}" -f Dockerfile .

echo "=== Tagging image ==="
docker tag "${REPO_NAME}:${IMAGE_TAG}" "${ECR_URI}"

echo "=== Pushing to ECR ==="
docker push "${ECR_URI}"

echo ""
echo "✅ Done! Image pushed to: ${ECR_URI}"
echo ""
echo "Next step: Update k8s/deployment.yaml with your ECR URI, then run:"
echo "  kubectl apply -f k8s/"

