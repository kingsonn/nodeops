#!/bin/bash
# Test NodeOps deployment locally

echo "=== AutoDeFi.AI NodeOps Deployment Test ==="

# Build Docker image
echo "Building Docker image..."
docker build -t autodefi-ai:test .

if [ $? -eq 0 ]; then
    echo "✓ Docker build successful"
    
    # Test run
    echo "Testing container..."
    docker run -d -p 8000:8000 --name autodefi-test autodefi-ai:test
    
    sleep 3
    
    # Health check
    echo "Checking health endpoint..."
    curl -f http://localhost:8000/health || echo "⚠️  Health check failed"
    
    # Cleanup
    echo "Cleaning up..."
    docker stop autodefi-test
    docker rm autodefi-test
    
    echo "✓ Test complete"
else
    echo "✗ Docker build failed"
    exit 1
fi
