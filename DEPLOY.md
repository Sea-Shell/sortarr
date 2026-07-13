# Deployment Guide

## Container Build

### Build with Podman

```bash
podman build -t docker.io/bateau/sortarr:v2.0.0 -f Dockerfile .
```

### Test Locally

```bash
# Run container
podman run --rm -d \
  --name sortarr-test \
  -p 8080:8080 \
  -e SORTARR_LOG_LEVEL=info \
  -e SORTARR_DATABASE_FILE=/tmp/test.db \
  docker.io/bateau/sortarr:v2.0.0

# Check health
curl http://localhost:8080/api/health

# View logs
podman logs sortarr-test

# Stop container
podman stop sortarr-test
```

### Push to Registry

```bash
# Login to Docker Hub
podman login docker.io

# Push image
podman push docker.io/bateau/sortarr:v2.0.0

# Optional: Tag as latest
podman tag docker.io/bateau/sortarr:v2.0.0 docker.io/bateau/sortarr:latest
podman push docker.io/bateau/sortarr:latest
```

## Kubernetes Deployment

### Prerequisites

1. **Namespace**: Ensure `seashell` namespace exists
   ```bash
   kubectl create namespace seashell
   ```

2. **Basic Auth Secret**: Create authentication secret for Traefik middleware
   ```bash
   # Generate htpasswd entry (username: admin, password: your-password)
   htpasswd -nb admin your-password | base64
   
   # Create secret
   kubectl create secret generic sortarr-auth \
     --from-literal=users='<base64-encoded-htpasswd>' \
     -n seashell
   ```

3. **Persistent Storage**: Ensure `/data/disk2/opt/sortarr` exists on the node
   ```bash
   # On the Kubernetes node:
   sudo mkdir -p /data/disk2/opt/sortarr
   sudo chown 1000:1000 /data/disk2/opt/sortarr
   ```

4. **Google OAuth Credentials**: Place `client_secret.json` in the persistent volume
   ```bash
   # Copy credentials to the node
   scp client_secret.json node:/data/disk2/opt/sortarr/
   ```

### Apply Manifests

```bash
# Apply all manifests
kubectl apply -f k8s/

# Or apply individually:
kubectl apply -f k8s/configmap.yaml
kubectl apply -f k8s/deployment.yaml
kubectl apply -f k8s/service.yaml
kubectl apply -f k8s/ingress.yaml

# Apply bootstrap resources (if not already done)
kubectl apply -f k8s-bootstrap/middleware.yaml
```

### Verify Deployment

```bash
# Check deployment status
kubectl get deployment sortarr -n seashell
kubectl get pods -n seashell -l app=sortarr

# Check service
kubectl get service sortarr -n seashell

# Check ingress
kubectl get ingress sortarr -n seashell

# View logs
kubectl logs -n seashell -l app=sortarr -f

# Check health endpoint
kubectl port-forward -n seashell svc/sortarr 8080:8080
curl http://localhost:8080/api/health
```

### Access the Application

Once deployed, access sortarr at: **https://sortarr.bateau.cloud**

You'll be prompted for basic auth credentials (configured in the `sortarr-auth` secret).

### Update Deployment

To update to a new version:

```bash
# Build and push new image
podman build -t docker.io/bateau/sortarr:v2.0.1 -f Dockerfile .
podman push docker.io/bateau/sortarr:v2.0.1

# Update deployment.yaml with new tag
# Then apply:
kubectl apply -f k8s/deployment.yaml

# Or use kubectl set image:
kubectl set image deployment/sortarr \
  sortarr=docker.io/bateau/sortarr:v2.0.1 \
  -n seashell

# Watch rollout
kubectl rollout status deployment/sortarr -n seashell
```

### Troubleshooting

#### Pod Not Starting

```bash
# Check pod status
kubectl describe pod -n seashell -l app=sortarr

# Check logs
kubectl logs -n seashell -l app=sortarr --previous
```

#### Health Check Failing

```bash
# Exec into pod
kubectl exec -it -n seashell deployment/sortarr -- /bin/bash

# Test health endpoint from inside pod
curl http://localhost:8080/api/health
```

#### Ingress Not Working

```bash
# Check ingress status
kubectl describe ingress sortarr -n seashell

# Check middleware
kubectl get middleware sortarr-auth -n seashell

# Check certificate
kubectl get certificate sortarr-tls -n seashell
kubectl describe certificate sortarr-tls -n seashell
```

#### Authentication Issues

```bash
# Verify secret exists
kubectl get secret sortarr-auth -n seashell

# Check middleware configuration
kubectl get middleware sortarr-auth -n seashell -o yaml
```

### Configuration Updates

To update runtime configuration:

1. Edit `k8s/configmap.yaml`
2. Apply changes: `kubectl apply -f k8s/configmap.yaml`
3. Restart deployment: `kubectl rollout restart deployment/sortarr -n seashell`

Note: Most configuration is now stored in the SQLite database and can be updated via the web UI at `/ui#config`.

### Backup and Restore

#### Backup Database

```bash
# Copy database from pod
kubectl cp seashell/$(kubectl get pod -n seashell -l app=sortarr -o jsonpath='{.items[0].metadata.name}'):/data/my.db ./backup-$(date +%Y%m%d).db
```

#### Restore Database

```bash
# Copy database to pod
kubectl cp ./backup.db seashell/$(kubectl get pod -n seashell -l app=sortarr -o jsonpath='{.items[0].metadata.name}'):/data/my.db

# Restart pod
kubectl rollout restart deployment/sortarr -n seashell
```

## Docker Compose (Alternative)

For local development or non-Kubernetes deployments:

```bash
docker-compose up -d
```

See `docker-compose.yml` for configuration.
