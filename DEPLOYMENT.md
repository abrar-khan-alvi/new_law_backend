# Deployment Guide — aiforlawenforcement.tech

Two parts: the static frontend on **S3 + Cloudflare**, and the Django backend on an
**EC2** instance (also fronted by Cloudflare).

```
Frontend:  Browser → Cloudflare (proxied, HTTPS/CDN) → S3 static website endpoint
Backend:   Browser → Cloudflare (proxied, HTTPS/CDN) → EC2 (nginx :80 → gunicorn :8000)
```

Both use Cloudflare **Flexible** SSL — Cloudflare terminates HTTPS at the edge and talks
plain HTTP to the origin (S3 website endpoints and a bare EC2 instance are both
HTTP-only without extra cert setup).

---

# Part 1 — Frontend (S3 + Cloudflare)

The S3 bucket name must exactly match the domain (`aiforlawenforcement.tech`) for the
website endpoint / CNAME setup to work.

## Prerequisites

- AWS account with access to S3
- Cloudflare account with the `aiforlawenforcement.tech` zone added
- Node.js + npm (for building the frontend)

## 1. Build the frontend

```bash
cd charisma-expert
npm install
npm run build
```

This produces a `dist/` folder containing `index.html`, `favicon.ico`, `favicon.png`, and `assets/`.

The build reads `VITE_API_BASE_URL` from `.env.production` (defaults to
`http://localhost:8000` if unset). Update `.env.production` with the real backend URL
before building for production:

```
VITE_API_BASE_URL=https://api.aiforlawenforcement.tech
```

> Currently set to a placeholder since the backend isn't deployed yet. Rebuild and
> re-upload once the backend has a real URL.

## 2. Create the S3 bucket (AWS Console)

1. S3 → **Create bucket**
2. Bucket name: `aiforlawenforcement.tech` (must match the domain exactly)
3. Region: `us-east-1`
4. Uncheck **"Block all public access"** → check the acknowledgment box
5. Leave everything else default → **Create bucket**

## 3. Enable static website hosting

1. Open the bucket → **Properties** tab → scroll to **"Static website hosting"** → Edit
2. Enable it, hosting type: "Host a static website"
3. Index document: `index.html`
4. Error document: `index.html` (the app uses client-side routing, so unknown paths must
   still serve `index.html`)
5. Save, and note the **bucket website endpoint** shown, e.g.:
   ```
   http://aiforlawenforcement.tech.s3-website-us-east-1.amazonaws.com
   ```
   You'll need this for the Cloudflare DNS record.

## 4. Add a bucket policy for public read access

**Permissions** tab → Bucket policy → Edit → paste:

```json
{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Sid": "PublicReadGetObject",
      "Effect": "Allow",
      "Principal": "*",
      "Action": "s3:GetObject",
      "Resource": "arn:aws:s3:::aiforlawenforcement.tech/*"
    }
  ]
}
```

Save.

## 5. Upload the build

**Objects** tab → Upload → Add folder → select `charisma-expert/dist` → upload the
*contents* (`index.html`, `favicon.ico`, `favicon.png`, `assets/`) directly into the
bucket root — not the `dist` folder itself.

Alternatively, once the AWS CLI is installed and configured (`aws configure`):

```bash
aws s3 sync dist/ s3://aiforlawenforcement.tech --delete
```

## 6. Configure Cloudflare DNS

1. DNS → **Add record**
   - Type: `CNAME`
   - Name: `@` (root domain)
   - Target: the S3 website endpoint from step 3
     (e.g. `aiforlawenforcement.tech.s3-website-us-east-1.amazonaws.com`)
   - Proxy status: **Proxied** (orange cloud) — required for HTTPS, since the S3
     website endpoint is HTTP-only
2. **SSL/TLS → Overview** → set encryption mode to **Flexible**
   (browser ↔ Cloudflare is HTTPS; Cloudflare ↔ S3 stays HTTP)

Once DNS propagates, `https://aiforlawenforcement.tech` serves the app.

## Redeploying after changes

```bash
cd charisma-expert
npm run build
aws s3 sync dist/ s3://aiforlawenforcement.tech --delete
```

(Or repeat the manual upload in step 5, replacing existing objects.)

No cache invalidation step is needed for CloudFront since it isn't used — Cloudflare's
cache may need a manual **Purge Cache** (Caching → Configuration → Purge Everything) if
updates don't show up immediately.

---

# Part 2 — Backend (EC2)

Runs the existing `Dockerfile` / a production `docker-compose.prod.yml` on a single EC2
instance: Postgres (pgvector), Redis, the Django app (gunicorn), Celery worker, Celery
beat, and an nginx reverse proxy in front of gunicorn.

## Prerequisites

- AWS account with access to EC2
- An SSH key pair for the instance
- Cloudflare zone for `aiforlawenforcement.tech` (already set up in Part 1)

## 1. Launch the EC2 instance (AWS Console)

1. EC2 → **Launch instance**
2. Name: `law-backend`
3. AMI: **Ubuntu Server 22.04 LTS**
4. Instance type: **t3.medium** (2 vCPU / 4 GB) minimum — Postgres, Redis, gunicorn, and
   two Celery processes all run on the same box, plus the embedding model
   (`all-MiniLM-L6-v2`) loads into memory
5. Key pair: select/create one and download the `.pem` — you'll need it for SSH
6. Network settings → **Edit** → security group rules:
   - SSH (22) — source: **My IP** (not `0.0.0.0/0`)
   - HTTP (80) — source: **Anywhere (0.0.0.0/0)** — this is what Cloudflare connects to
   - Do **not** open 8000 or 5432/6379 publicly — those stay internal to the instance
7. Storage: 20 GB gp3 is enough to start
8. Launch instance

## 2. Allocate an Elastic IP

EC2's default public IP changes if the instance stops/restarts, which would break DNS.

1. EC2 → **Elastic IPs** → Allocate Elastic IP address
2. Select it → **Actions → Associate Elastic IP address** → choose the `law-backend`
   instance
3. Note the address — this is what the Cloudflare DNS record will point to

## 3. Install Docker on the instance

SSH in and install Docker + the Compose plugin:

```bash
ssh -i your-key.pem ubuntu@<elastic-ip>

sudo apt-get update
sudo apt-get install -y ca-certificates curl gnupg
sudo install -m 0755 -d /etc/apt/keyrings
curl -fsSL https://download.docker.com/linux/ubuntu/gpg | sudo gpg --dearmor -o /etc/apt/keyrings/docker.gpg
sudo chmod a+r /etc/apt/keyrings/docker.gpg
echo \
  "deb [arch=$(dpkg --print-architecture) signed-by=/etc/apt/keyrings/docker.gpg] https://download.docker.com/linux/ubuntu \
  $(. /etc/os-release && echo $VERSION_CODENAME) stable" | sudo tee /etc/apt/sources.list.d/docker.list > /dev/null
sudo apt-get update
sudo apt-get install -y docker-ce docker-ce-cli containerd.io docker-compose-plugin

sudo usermod -aG docker $USER
# log out and back in for the group change to take effect
```

## 4. Clone the repo and configure `.env`

```bash
git clone <your-repo-url> law_backend
cd law_backend
cp .env.example .env
nano .env
```

Set at minimum:

```
DJANGO_SECRET_KEY=<generate a real 50-char random secret>
DEBUG=False
DJANGO_SETTINGS_MODULE=core.settings.production
ALLOWED_HOSTS=api.aiforlawenforcement.tech
CORS_ALLOWED_ORIGINS=https://aiforlawenforcement.tech
FRONTEND_URL=https://aiforlawenforcement.tech

USE_SQLITE=False
DB_NAME=law_enforcement_db
DB_USER=le_user
DB_PASSWORD=<a strong password, not the docker-compose.yml dev default>

REDIS_URL=redis://redis:6379/0

# AI: start with 'mock' (no extra infra) until Bedrock/Ollama is actually wired up
AI_MODE=mock

# Leave AWS_ACCESS_KEY_ID/SECRET blank and attach an IAM instance role instead
# (see step 7) if this instance also needs S3/Bedrock access.
AWS_REGION=us-east-1

EMAIL_HOST_USER=...
EMAIL_HOST_PASSWORD=...

STRIPE_SECRET_KEY=...
STRIPE_WEBHOOK_SECRET=...
```

`DJANGO_SECRET_KEY` must be set to a real value — `core/settings/production.py` refuses
to start with the dev default.

## 5. Start the stack

The repo now has `docker-compose.prod.yml` (Postgres, Redis, gunicorn, Celery worker,
Celery beat, nginx — no dev `runserver`, no live code mount, no Ollama) and
`nginx/nginx.conf` (reverse proxy from :80 to the `backend` container's :8000).

```bash
docker compose -f docker-compose.prod.yml up -d --build
docker compose -f docker-compose.prod.yml logs -f backend   # watch migrate/collectstatic/gunicorn start
```

Migrations and `collectstatic` run automatically on container start (see the `backend`
service's `command` in `docker-compose.prod.yml`).

Create an admin user:

```bash
docker compose -f docker-compose.prod.yml exec backend python manage.py createsuperuser
```

## 6. Configure Cloudflare DNS

1. DNS → **Add record**
   - Type: `A`
   - Name: `api`
   - IPv4 address: the Elastic IP from step 2
   - Proxy status: **Proxied** (orange cloud)
2. SSL/TLS mode should already be **Flexible** from Part 1 (it's zone-wide, not
   per-record) — Cloudflare will talk HTTP to nginx on port 80.

`nginx/nginx.conf` is already set to relay Cloudflare's original `X-Forwarded-Proto`
header rather than overwrite it — this matters because `production.py` sets
`SECURE_SSL_REDIRECT = True`, and getting that header wrong causes a redirect loop.

Once DNS propagates, `https://api.aiforlawenforcement.tech` should hit the Django app.

## 7. (Optional) IAM instance role instead of static AWS keys

If the backend needs S3 (media uploads) or Bedrock (AI) access, attach an IAM role to
the EC2 instance (EC2 → instance → Actions → Security → Modify IAM role) with the
needed S3/Bedrock permissions, and leave `AWS_ACCESS_KEY_ID` /
`AWS_SECRET_ACCESS_KEY` blank in `.env` — boto3 picks up instance-role credentials
automatically, which avoids long-lived keys sitting in a `.env` file on the server.

## Redeploying backend changes

```bash
cd law_backend
git pull
docker compose -f docker-compose.prod.yml up -d --build
```

## Notes / open items

- Frontend: `VITE_API_BASE_URL` was set to the placeholder
  `https://api.aiforlawenforcement.tech` when it was built (Part 1, step 1) — that
  matches the `api.` subdomain used here, so once the backend is live no frontend
  rebuild should be needed. Verify with a real login/API call once both are deployed.
- AWS CLI v2 is installed locally (`C:\Program Files\Amazon\AWSCLIV2\aws.exe`) but not
  yet authenticated — run `aws configure` to enable CLI-based S3 uploads instead of the
  manual console upload in Part 1.
- `AI_MODE=mock` above is a starting point, not a final choice — switch to `bedrock` (set
  `BEDROCK_MODEL_ID`/`BEDROCK_REGION`, grant Bedrock access via the IAM role in step 7)
  or `ollama` (needs a much bigger/GPU instance to run `llama3.1:8b`) when ready.
- `docker-compose.prod.yml` runs Postgres/Redis as containers on the same instance for
  simplicity — fine to start, but has no automated backups. Consider migrating to RDS
  (Postgres + pgvector is supported) and ElastiCache once this is past initial setup.
