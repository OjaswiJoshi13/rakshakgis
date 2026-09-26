# RakshakGIS — Production Deployment & Operations Guide

This document establishes the operational deployment guide, environment configuration, secrets management policies, container lifecycle procedures, map tile provider audit, and cloud deployment runbook for **RakshakGIS**.

---

## 1. System Architecture Overview

RakshakGIS uses a containerized three-tier architecture optimized for single-node production deployment on Docker Compose and cloud virtual machines (e.g., AWS EC2):

```
                        [ Internet / Client Browser ]
                                     |
                        HTTP: 3000 / HTTPS: 443
                                     v
                 +---------------------------------------+
                 |       Frontend (Next.js Standalone)   |
                 |       Container: unprivileged 'nextjs'|
                 |       - Serves UI / MapLibre GL       |
                 |       - Rewrites /api/v1 -> Backend   |
                 +---------------------------------------+
                                     |
                   Internal Docker Network (rakshakgis_prod_network)
                                     v
                 +---------------------------------------+
                 |       Backend (FastAPI / Uvicorn)     |
                 |       Container: unprivileged 'appuser'|
                 |       - REST API / Auth / Spatial Alg |
                 |       - Auto-runs Alembic migrations  |
                 +---------------------------------------+
                                     |
                   Internal Docker Network (No host port published)
                                     v
                 +---------------------------------------+
                 |       Database (PostgreSQL 15+PostGIS)|
                 |       - Persistent Volume:            |
                 |         rakshakgis_prod_pgdata        |
                 |       - Port 5432 strictly internal   |
                 +---------------------------------------+
```

### Key Security & Isolation Guarantees
1. **Unprivileged Runtimes:** Both the backend (`appuser`, UID 1001) and frontend (`nextjs`, UID 1001) containers execute as unprivileged system users without root privileges.
2. **Private Database Network:** In production Compose (`docker-compose.prod.yml`), the PostgreSQL database has **no host port published** (`ports: []`). Only containers attached to `rakshakgis_prod_network` can communicate with the database on port 5432.
3. **Same-Origin API Routing:** Browsers communicate exclusively with the frontend on port 3000 (or reverse proxy 80/443). The Next.js server proxies `/api/v1/*` requests internally to `http://backend:8000`, eliminating CORS vulnerabilities, browser mixed-content blocks, and hardcoded `localhost` IP dependencies.
4. **Automated Migrations on Startup:** The backend container entrypoint automatically executes `alembic upgrade head` before spawning the Uvicorn application server, guaranteeing database schema alignment upon release.

---

## 2. Container Images & Semantic Versioning

RakshakGIS releases follow Semantic Versioning (`vMAJOR.MINOR.PATCH`). Production deployments must **never** reference mutable tags like `:latest` in production manifests.

### Release Image Tags (Baseline: `v0.1.0`)
- **Backend:** `rakshakgis-backend:v0.1.0`
- **Frontend:** `rakshakgis-frontend:v0.1.0`

### Building Production Images Locally
```bash
# Build & tag hardened backend image
docker build -f backend/Dockerfile -t rakshakgis-backend:v0.1.0 backend/

# Build & tag standalone frontend image
docker build -f frontend/Dockerfile -t rakshakgis-frontend:v0.1.0 frontend/
```

### Container Verification Probes
Confirm non-root user execution:
```bash
docker run --rm rakshakgis-backend:v0.1.0 id
# Expected: uid=1001(appuser) gid=1001(appgroup)

docker run --rm rakshakgis-frontend:v0.1.0 id
# Expected: uid=1001(nextjs) gid=1001(nodejs)
```

---

## 3. Environment Variables & Separation

Configuration differs strictly between development and production environments.

### Environment Matrix

| Variable | Description | Development Default (`.env`) | Production Standard (`docker-compose.prod.yml`) |
| :--- | :--- | :--- | :--- |
| `POSTGRES_DB` | PostgreSQL database name | `rakshakgis` | `rakshakgis` |
| `POSTGRES_USER` | PostgreSQL superuser | `rakshak` | `rakshak` |
| `POSTGRES_PASSWORD` | PostgreSQL superuser password | `rakshak123` (dev only) | **Mandatory Secret** (Must be passed externally) |
| `DATABASE_URL` | SQLAlchemy connection string | `postgresql://...@localhost:5433/...` | N/A (Dev host port) |
| `PROD_DATABASE_URL` | Production SQLAlchemy URL | N/A | `postgresql://rakshak:${POSTGRES_PASSWORD}@db:5432/rakshakgis` |
| `JWT_SECRET` | Secret key for JWT signing | `rakshak_dev_secret...` | **Mandatory Secret** (Must be passed externally) |
| `ALGORITHM` | JWT cryptographic algorithm | `HS256` | `HS256` |
| `ACCESS_TOKEN_EXPIRE_MINUTES` | Token expiration window | `480` (8 hours) | `60` (1 hour recommended) |
| `FRONTEND_PORT` | Published host port for frontend | `3000` | `3000` (or `80`/`443` via reverse proxy) |
| `BACKEND_PORT` | Published host port for backend | `8000` | Optional for direct debug; omitted or internal |
| `BACKEND_INTERNAL_URL` | URL frontend uses to reach backend | `http://localhost:8000` | `http://backend:8000` |
| `NEXT_PUBLIC_API_BASE_URL` | Base API path used by browser | `/api/v1` | `/api/v1` (same-origin relative proxy) |
| `ALLOW_DEMO_SEED` | Guard allowing sample data seed | `true` | `false` (set `true` only for staging demos) |
| `SEED_DEMO_DATA` | Flag triggering seed at startup | `false` | `false` (set `true` only for staging demos) |
| `NEXT_PUBLIC_MAP_STYLE` | MapLibre basemap style URL | Omitted (OSM raster default) | Configurable if using custom tile server |

---

## 4. Production Secrets Management

> [!CAUTION]
> Never commit real secrets, passwords, or production `.env` files to git. `.gitignore` strictly excludes `.env` and `.env.*` (except `.env.example`).

### Mandatory Production Secrets
In `docker-compose.prod.yml`, the two critical secrets use Docker Compose parameter expansion with the `?` error operator:
```yaml
POSTGRES_PASSWORD: ${POSTGRES_PASSWORD:?Error: POSTGRES_PASSWORD must be set in production}
JWT_SECRET: ${JWT_SECRET:?Error: JWT_SECRET must be set in production}
```
If either variable is missing, `docker compose` will abort immediately with an error before starting any container.

### Generating Cryptographically Secure Secrets
Generate strong 256-bit secrets on the command line:
```bash
# Generate POSTGRES_PASSWORD
openssl rand -base64 24

# Generate JWT_SECRET
openssl rand -hex 32
```

### Storing Production Secrets
1. **On AWS EC2 / Linux Host:**
   Create a dedicated production environment file outside the git repository (e.g., `/etc/rakshakgis/production.env`) with strict file permissions:
   ```bash
   sudo mkdir -p /etc/rakshakgis
   sudo nano /etc/rakshakgis/production.env
   # Set permissions: accessible only by deployer/root
   sudo chmod 600 /etc/rakshakgis/production.env
   sudo chown root:root /etc/rakshakgis/production.env
   ```
2. **Cloud Secret Managers (Enterprise / AWS):**
   Store values in **AWS Systems Manager (SSM) Parameter Store** (`SecureString`) or **AWS Secrets Manager**, retrieving them during the deployment pipeline or instance cloud-init.

---

## 5. Local Production Stack Operations (`docker-compose.prod.yml`)

The production Compose configuration enables exact production-fidelity validation on any Docker-compatible host.

### Starting the Production Stack
```bash
# Export mandatory secrets for the session
export POSTGRES_PASSWORD="YourStrongProdPasswordHere"
export JWT_SECRET="YourStrong64CharRandomHexSecretHere"

# Start the stack detached
docker compose -f docker-compose.prod.yml up -d
```

### Checking Health & Container Status
```bash
docker compose -f docker-compose.prod.yml ps
```
All services should report `Up` with `(healthy)`:
- `rakshakgis-prod-db`: Healthcheck runs `pg_isready -U rakshak -d rakshakgis`.
- `rakshakgis-prod-backend`: Healthcheck probes `http://127.0.0.1:8000/health`.
- `rakshakgis-prod-frontend`: Serves HTTP 200 on port 3000.

### Verifying End-to-End Connectivity
```bash
# Check backend health
curl -f http://127.0.0.1:8000/health
# Expected: {"status":"healthy"}

# Check frontend health rewrite
curl -f http://127.0.0.1:3000/health
# Expected: {"status":"healthy"}

# Check frontend-to-backend API proxying (returns JSON)
curl -s http://127.0.0.1:3000/api/v1/villages | grep -o "Uttarkashi"
# Confirms PostGIS query resolved and returned through Next.js proxy
```

### Stopping and Restarting
```bash
# Stop containers safely (PRESERVES all database data in named volume)
docker compose -f docker-compose.prod.yml down

# Restart containers
docker compose -f docker-compose.prod.yml up -d

# CAUTION: NEVER pass the '-v' flag in production:
# docker compose down -v  <-- THIS WILL PERMANENTLY DESTROY DATABASE VOLUMES!
```

---

## 6. Database Persistence, Backup & Restore Runbook

PostgreSQL/PostGIS data is stored in the Docker named volume `rakshakgis_prod_pgdata`.

### Database Backup Procedure (`pg_dump`)
To take an atomic, compressed snapshot of the production database:
```bash
# Create timestamped backup file
BACKUP_FILE="rakshakgis_backup_$(date +%Y%m%d_%H%M%S).dump"

docker exec -t rakshakgis-prod-db pg_dump \
  -U rakshak \
  -d rakshakgis \
  -F c \
  -b -v \
  -f "/tmp/${BACKUP_FILE}"

docker cp "rakshakgis-prod-db:/tmp/${BACKUP_FILE}" "./backups/${BACKUP_FILE}"
docker exec -t rakshakgis-prod-db rm "/tmp/${BACKUP_FILE}"

echo "Backup saved to ./backups/${BACKUP_FILE}"
```

### Database Restore Procedure (`pg_restore`)
To restore an existing backup into a fresh or existing database:
```bash
# Copy dump into database container
docker cp "./backups/${BACKUP_FILE}" "rakshakgis-prod-db:/tmp/restore.dump"

# Restore schema and data
docker exec -t rakshakgis-prod-db pg_restore \
  -U rakshak \
  -d rakshakgis \
  --clean \
  --if-exists \
  --no-owner \
  --no-acl \
  -v "/tmp/restore.dump"

docker exec -t rakshakgis-prod-db rm "/tmp/restore.dump"
```

---

## 7. Map Tile Provider & Basemap Audit

### MapLibre GL Integration Audit
Inspection of [`frontend/src/components/map/mapStyle.ts`](file:///c:/Users/swapn/projects/rakshakgis/frontend/src/components/map/mapStyle.ts) confirms:
- **Baseline Provider:** OpenStreetMap standard raster tiles via `CREDENTIAL_FREE_OSM_STYLE`:
  ```typescript
  tiles: ['https://tile.openstreetmap.org/{z}/{x}/{y}.png']
  ```
- **Authentication:** **No API key, account, or credit card is required.** The platform runs completely out-of-the-box with zero third-party cloud tile dependencies.

### Production Map Tile Recommendations
While the default OpenStreetMap tile server works without credentials, the OpenStreetMap Foundation Tile Usage Policy discourages high-volume automated production traffic.

For large-scale public deployments:
1. **Configurable Style URL:**
   The frontend supports overriding the basemap style using the environment variable `NEXT_PUBLIC_MAP_STYLE`.
2. **Supported Options:**
   - **Self-Hosted Vector/Raster Tiles:** Run a lightweight tile server (e.g., Martin, TileServer-GL, or Protomaps PMTiles) on the same host or via S3/CloudFront.
   - **Managed Vector Providers:** Set `NEXT_PUBLIC_MAP_STYLE` to a MapTiler or Stadia Maps style JSON URL with an authorized domain key.

---

## 8. AWS Cloud Deployment Runbook

The `terraform/` directory contains automated Infrastructure as Code (IaC) to provision a secure, single-node AWS environment.

### Target Cloud Sizing & Memory Considerations
- **Recommended Instance Type:** `t3.small` (2 vCPU, 2.0 GiB RAM) or `t3.medium` (2 vCPU, 4.0 GiB RAM).
- **`t2.micro` Caveat:** AWS Free Tier `t2.micro` instances provide only 1.0 GiB of RAM. PostgreSQL with PostGIS extensions and Next.js server runtimes can experience Out-Of-Memory (OOM) kernel terminations during heavy geospatial queries or initial schema migrations if run on `t2.micro` without swap. If `t2.micro` must be used for budget tests, the automated cloud-init user data script (`terraform/user_data.sh`) provisions a **2 GiB swapfile** (`/swapfile`) to ensure operational stability.

### Deployment Sequence
1. Navigate to the `terraform/` directory:
   ```bash
   cd terraform
   ```
2. Create `terraform.tfvars` from `terraform.tfvars.example`:
   ```bash
   cp terraform.tfvars.example terraform.tfvars
   # Configure your AWS region, instance type, and admin SSH CIDR
   ```
3. Initialize and provision:
   ```bash
   terraform init
   terraform plan -out=tfplan
   terraform apply tfplan
   ```
4. Note the output Elastic IP (`public_ip`).
5. SSH into the instance using the output SSH command:
   ```bash
   ssh -i ~/.ssh/your-key.pem ubuntu@<PUBLIC_IP>
   ```
6. Clone the RakshakGIS repository, configure production secrets, and launch:
   ```bash
   git clone https://github.com/OjaswiJoshi13/rakshakgis.git /opt/rakshakgis
   cd /opt/rakshakgis
   POSTGRES_PASSWORD="<prod-pass>" JWT_SECRET="<prod-secret>" docker compose -f docker-compose.prod.yml up -d
   ```
