#!/bin/bash
# NodeOps Deployment Script

set -e

echo "=== AutoDeFi.AI NodeOps Deployment ==="

# Configuration
IMAGE_NAME="autodefi-ai"
REGISTRY="registry.nodeops.xyz"
VERSION=${1:-latest}

# Build
echo "Building Docker image..."
docker build -t ${IMAGE_NAME}:${VERSION} ..

# Tag for registry
echo "Tagging image..."
docker tag ${IMAGE_NAME}:${VERSION} ${REGISTRY}/${IMAGE_NAME}:${VERSION}

# Push to registry
echo "Pushing to NodeOps registry..."
docker push ${REGISTRY}/${IMAGE_NAME}:${VERSION}

# Deploy
echo "Deploying to NodeOps..."
nodeops deploy --manifest ../nodeops.yaml --image ${REGISTRY}/${IMAGE_NAME}:${VERSION}

echo "✓ Deployment complete!"
echo "Access your app at: https://autodefi-ai.nodeops.app"
