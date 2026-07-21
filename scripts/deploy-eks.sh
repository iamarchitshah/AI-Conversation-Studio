#!/bin/bash
# =============================================================================
# deploy-eks.sh — Deploy AI Conversation Studio to Amazon EKS
# =============================================================================
# Prerequisites:
#   1. kubectl installed & configured for your EKS cluster
#   2. eksctl or AWS CLI configured with the right context
#   3. Docker image already pushed to ECR (use build-and-push.sh first)
#
# Usage:
#   ./scripts/deploy-eks.sh <AWS_ACCOUNT_ID> <REGION> [IMAGE_TAG]
#
# Example:
#   ./scripts/deploy-eks.sh 123456789012 us-east-1 latest
# =============================================================================

set -euo pipefail

if [ "$#" -lt 2 ]; then
  echo "Usage: $0 <AWS_ACCOUNT_ID> <REGION> [IMAGE_TAG]"
  echo "Example: $0 123456789012 us-east-1 latest"
  exit 1
fi

AWS_ACCOUNT_ID="$1"
REGION="$2"
IMAGE_TAG="${3:-latest}"
REPO_NAME="ai-conversation-studio"
ECR_URI="${AWS_ACCOUNT_ID}.dkr.ecr.${REGION}.amazonaws.com/${REPO_NAME}:${IMAGE_TAG}"

# Detect EKS cluster context (first available)
CLUSTER_NAME=$(kubectl config current-context 2>/dev/null || echo "")
if [ -z "${CLUSTER_NAME}" ]; then
  echo "⚠️  No kubectl context detected. Trying to find an EKS cluster..."
  CLUSTER_NAME=$(aws eks list-clusters --region "${REGION}" --query "clusters[0]" --output text 2>/dev/null || echo "")
  if [ -z "${CLUSTER_NAME}" ] || [ "${CLUSTER_NAME}" == "None" ]; then
    echo "❌ No EKS cluster found. Please create one first or configure kubectl."
    echo ""
    echo "To create a cluster, you can use eksctl:"
    echo "  eksctl create cluster --name ai-conversation-studio --region ${REGION}"
    exit 1
  fi
  echo "Found cluster: ${CLUSTER_NAME}. Updating kubeconfig..."
  aws eks update-kubeconfig --name "${CLUSTER_NAME}" --region "${REGION}"
fi

echo ""
echo "=== Deploying AI Conversation Studio to EKS ==="
echo "  Cluster:  $(kubectl config current-context)"
echo "  Image:    ${ECR_URI}"
echo "  Region:   ${REGION}"
echo ""

# Apply namespace first
echo "--- Namespace ---"
kubectl apply -f k8s/namespace.yaml

# Apply ConfigMap
echo "--- ConfigMap ---"
kubectl apply -f k8s/configmap.yaml

# Apply PVC
echo "--- PersistentVolumeClaim ---"
kubectl apply -f k8s/pvc.yaml

# Update deployment.yaml with the actual ECR image
echo "--- Deployment ---"
sed "s|<YOUR_AWS_ACCOUNT_ID>|${AWS_ACCOUNT_ID}|g; s|<REGION>|${REGION}|g" k8s/deployment.yaml \
  | kubectl apply -f -

# Apply HPA
echo "--- HorizontalPodAutoscaler ---"
kubectl apply -f k8s/hpa.yaml

# Apply Service
echo "--- Service ---"
kubectl apply -f k8s/service.yaml

echo ""
echo "=== ✅ Deployment complete! ==="
echo ""
echo "Waiting for LoadBalancer to get an external IP..."
sleep 10

# Wait for the LoadBalancer hostname/ip
kubectl wait --namespace ai-conversation-studio \
  --for=condition=available \
  --timeout=120s \
  deployment/ai-conversation-studio || true

echo ""
echo "--- Service status ---"
kubectl get svc -n ai-conversation-studio ai-conversation-studio-service
echo ""
echo "--- Pods ---"
kubectl get pods -n ai-conversation-studio
echo ""
echo "To check the external URL, run:"
echo "  kubectl get svc -n ai-conversation-studio ai-conversation-studio-service -o jsonpath='{.status.loadBalancer.ingress[0].hostname}'"

