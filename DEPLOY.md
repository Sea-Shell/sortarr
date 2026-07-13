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

## Database Migration (v1 → v2)

### When Migration is Needed

If you're upgrading from the legacy v1 sortarr (archive/main.py) to v2, you need to migrate your database. The v1 schema has 5 simple tables, while v2 has 14 tables with richer structure.

**Check if migration is needed:**

```bash
# Using the migration script
python scripts/migrate_db.py /data/sortarr.db --check-only
```

Expected output:
- `Schema version: v1 (legacy 5-table schema)` → Migration needed
- `Schema version: v2 (current 14-table schema)` → No migration needed

### Running the Migration

**Option 1: Manual migration (recommended for production)**

```bash
# Run migration script
python scripts/migrate_db.py /data/sortarr.db

# This will:
# 1. Create backup: sortarr.db.backup-TIMESTAMP
# 2. Migrate data from v1 to v2
# 3. Verify migration succeeded
# 4. Show migration summary
```

**Option 2: Automatic migration on startup**

Set environment variable to enable auto-migration:

```bash
SORTARR_AUTO_MIGRATE=true
```

Or in Kubernetes ConfigMap:

```yaml
data:
  SORTARR_AUTO_MIGRATE: "true"
```

**Warning**: Auto-migration runs on every startup if v1 is detected. Manual migration is safer for production.

### What Gets Migrated

**Preserved data:**
- ✅ Subscriptions (v1.subscription → v2.subscriptions)
- ✅ Videos audit trail (v1.videos → v2.videos)
- ✅ Last run timestamp (v1.last_run → v2.app_config)
- ✅ Playlist info (v1.playlist → default pipeline destination)

**Created during migration:**
- ✅ Default pipeline named "Migrated from v1" (disabled by default)
- ✅ Subscription tracking entries
- ✅ Schema version marker in app_config

**Not migrated (v1 didn't have these):**
- ❌ Ignore lists
- ❌ Pipeline selectors
- ❌ Activity cache
- ❌ Run history

### After Migration

1. **Verify the migration:**
   ```bash
   # Check schema version
   sqlite3 /data/sortarr.db "SELECT value FROM app_config WHERE key = 'schema_version'"
   # Should output: 2
   
   # Check subscriptions
   sqlite3 /data/sortarr.db "SELECT COUNT(*) FROM subscriptions"
   
   # Check videos
   sqlite3 /data/sortarr.db "SELECT COUNT(*) FROM videos"
   ```

2. **Configure pipelines:**
   - Access web UI at `/ui#pipelines`
   - Review the "Migrated from v1" pipeline
   - Enable it or create new pipelines
   - Configure selectors and ignore lists

3. **Test a dry run:**
   ```bash
   curl -X POST http://localhost:8080/api/run/dry
   ```

### Restoring from Backup

If migration fails or you need to rollback:

```bash
# List backups
ls -lh /data/sortarr.db.backup-*

# Restore from backup
cp /data/sortarr.db.backup-TIMESTAMP /data/sortarr.db

# Restart application
kubectl rollout restart deployment/sortarr -n seashell
```

### Migration in Kubernetes

**Before upgrading the deployment:**

```bash
# 1. Backup current database
kubectl cp seashell/$(kubectl get pod -n seashell -l app=sortarr -o jsonpath='{.items[0].metadata.name}'):/data/sortarr.db ./sortarr-pre-migration.db

# 2. Copy database locally and test migration
python scripts/migrate_db.py ./sortarr-pre-migration.db

# 3. If successful, copy migrated database back
kubectl cp ./sortarr-pre-migration.db seashell/$(kubectl get pod -n seashell -l app=sortarr -o jsonpath='{.items[0].metadata.name}'):/data/sortarr.db

# 4. Update deployment to v2
kubectl apply -f k8s/deployment.yaml
```

**Or enable auto-migration in ConfigMap:**

```yaml
# k8s/configmap.yaml
data:
  SORTARR_AUTO_MIGRATE: "true"
```

Then apply and restart:

```bash
kubectl apply -f k8s/configmap.yaml
kubectl rollout restart deployment/sortarr -n seashell
```

### Troubleshooting Migration

**Migration fails with "unknown schema":**
- Database might be corrupted
- Check tables: `sqlite3 sortarr.db ".tables"`
- Restore from backup

**Migration succeeds but data is missing:**
- Check migration summary output
- Verify backup was created
- Check logs for errors during migration

**Pod crashes after migration:**
- Check logs: `kubectl logs -n seashell -l app=sortarr`
- Verify schema version: `sqlite3 sortarr.db "SELECT value FROM app_config WHERE key = 'schema_version'"`
- Restore from backup if needed
