# NodeOps Deployment Guide

This directory contains NodeOps-specific deployment configuration and assets.

## Quick Deploy

1. **Build and tag the Docker image:**
   ```bash
   docker build -t autodefi-ai:latest .
   docker tag autodefi-ai:latest registry.nodeops.xyz/autodefi-ai:latest
   ```

2. **Push to NodeOps registry:**
   ```bash
   docker push registry.nodeops.xyz/autodefi-ai:latest
   ```

3. **Deploy using NodeOps CLI:**
   ```bash
   nodeops deploy --manifest nodeops.yaml
   ```

## Configuration

Edit `nodeops.yaml` to configure:
- Resource limits (CPU, memory)
- Environment variables
- Port mappings
- Scaling policies

## Monitoring

Access logs and metrics through the NodeOps dashboard:
```bash
nodeops logs autodefi-ai
nodeops metrics autodefi-ai
```

## Updating

To update the deployment:
```bash
# Build new version
docker build -t autodefi-ai:v1.1 .

# Push to registry
docker push registry.nodeops.xyz/autodefi-ai:v1.1

# Update deployment
nodeops update autodefi-ai --image autodefi-ai:v1.1
```
