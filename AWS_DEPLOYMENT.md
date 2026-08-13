# Deploy Klyvorek on AWS

> The current low-cost ARM64 deployment is documented in
> `EC2_SINGLE_INSTANCE_DEPLOYMENT.md`. The GPU/RDS architecture below is retained
> only for the later production upgrade.

Target architecture:

```text
www.klyvorek.com -> Cloudflare -> S3 static website
api.klyvorek.com -> Cloudflare Full (Strict) -> EC2 g4dn.xlarge
  EC2: nginx + Django/Gunicorn + Celery + Redis + Ollama llama3.1:8b (NVIDIA T4)
  EC2 -> private RDS PostgreSQL 16
  EC2 -> private S3 media bucket through an IAM role
```

Examples use `us-east-1`. Keep EC2, RDS, and S3 in one Region. The model tag is
`llama3.1:8b` (not `ollama3.1:8b`).

## 0. Rotate exposed development credentials

Before deploying, revoke and replace the AWS access key, Stripe secret/webhook
secret, and email app password currently present in the local development `.env`.
Never copy that file to EC2. Production uses `.env.aws.example` as its starting point.

## 1. Create the EC2 server

In EC2 -> Launch instance:

1. Name: `klyvorek-api-gpu`.
2. AMI: latest **Deep Learning Base OSS Nvidia Driver GPU AMI (Ubuntu 22.04)**,
   x86_64. This AWS AMI supports G4dn and includes the NVIDIA driver/toolkit.
3. Instance type: `g4dn.xlarge` (4 vCPU, 16 GiB RAM, one NVIDIA T4/16 GiB VRAM).
4. Key pair: create/select one, or configure AWS Systems Manager Session Manager.
5. Root EBS: 60 GiB gp3, encrypted, 3,000 IOPS. Enable delete-on-termination only
   after snapshots/backups are configured.
6. Advanced details: IMDS enabled, IMDSv2 required, response hop limit `2` so
   Dockerized boto3 can use the EC2 IAM role.
7. Launch in the same VPC you will use for RDS.

If AWS reports a G-instance vCPU quota error, request a quota increase for
**Running On-Demand G and VT instances** to at least 4 vCPUs.

Allocate and associate an Elastic IP. Record it for Cloudflare DNS.

### EC2 security group

- TCP 22: your fixed IP only (omit if using Session Manager).
- TCP 80 and 443: temporarily Anywhere during setup; after DNS works, restrict
  these rules to Cloudflare's published IPv4/IPv6 ranges.
- Never expose 8000, 11434, 5432, or 6379.

## 2. Create RDS PostgreSQL

In RDS -> Create database:

1. Engine: PostgreSQL 16.
2. Template: Production or Dev/Test for the beta.
3. Identifier: `klyvorek-production`.
4. Initial database: `klyvorek`.
5. Master username: `klyvorek_app`; generate a strong password.
6. Instance: `db.t4g.small` to start.
7. Storage: 20 GiB gp3, encryption and storage autoscaling enabled.
8. Connectivity: same VPC as EC2; **Public access: No**.
9. Automated backups: at least 7 days; enable deletion protection.
10. Single-AZ minimizes beta cost. Enable Multi-AZ before promising an SLA.

Use **Actions -> Set up EC2 connection**, select `klyvorek-api-gpu`, and let AWS
create linked security groups. RDS port 5432 must accept traffic only from the EC2
security group. Record the RDS endpoint, not its IP.

RDS PostgreSQL supports pgvector. Django's first migration creates the `vector`
extension and HNSW index.

## 3. Create both S3 buckets

### Frontend bucket

Create `www.klyvorek.com`:

- Enable static website hosting.
- Index document: `index.html`.
- Error document: `index.html` for React Router routes.
- This website-origin pattern requires public read access. Add only `s3:GetObject`
  for `arn:aws:s3:::www.klyvorek.com/*`.
- Record its regional website endpoint (the `s3-website-...` hostname).

### Private media bucket

Create a globally unique bucket such as `klyvorek-production-media-<account-id>`:

- Keep Block Public Access enabled.
- Enable default encryption and versioning.
- Add a lifecycle rule for incomplete multipart uploads.
- Do not enable website hosting.

## 4. Create and attach the EC2 IAM role

Create an EC2 role named `KlyvorekApiRole` with this scoped policy, replacing the
bucket name:

```json
{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Effect": "Allow",
      "Action": ["s3:GetObject", "s3:PutObject", "s3:DeleteObject"],
      "Resource": "arn:aws:s3:::klyvorek-production-media-ACCOUNT_ID/*"
    },
    {
      "Effect": "Allow",
      "Action": "s3:ListBucket",
      "Resource": "arn:aws:s3:::klyvorek-production-media-ACCOUNT_ID"
    }
  ]
}
```

Attach it via EC2 -> instance -> Actions -> Security -> Modify IAM role. Leave
`AWS_ACCESS_KEY_ID` and `AWS_SECRET_ACCESS_KEY` blank in production.

## 5. Prepare the GPU host

SSH to the Elastic IP. First verify the DLAMI driver:

```bash
nvidia-smi
```

Install Docker Engine if the selected DLAMI does not already provide it:

```bash
sudo apt-get update
sudo apt-get install -y ca-certificates curl gnupg git
sudo install -m 0755 -d /etc/apt/keyrings
curl -fsSL https://download.docker.com/linux/ubuntu/gpg | sudo gpg --dearmor -o /etc/apt/keyrings/docker.gpg
sudo chmod a+r /etc/apt/keyrings/docker.gpg
echo "deb [arch=$(dpkg --print-architecture) signed-by=/etc/apt/keyrings/docker.gpg] https://download.docker.com/linux/ubuntu $(. /etc/os-release && echo $VERSION_CODENAME) stable" | sudo tee /etc/apt/sources.list.d/docker.list >/dev/null
sudo apt-get update
sudo apt-get install -y docker-ce docker-ce-cli containerd.io docker-buildx-plugin docker-compose-plugin
sudo usermod -aG docker "$USER"
```

Install/configure NVIDIA Container Toolkit if `nvidia-ctk` is unavailable:

```bash
curl -fsSL https://nvidia.github.io/libnvidia-container/gpgkey | sudo gpg --dearmor -o /usr/share/keyrings/nvidia-container-toolkit-keyring.gpg
curl -s -L https://nvidia.github.io/libnvidia-container/stable/deb/nvidia-container-toolkit.list | sed 's#deb https://#deb [signed-by=/usr/share/keyrings/nvidia-container-toolkit-keyring.gpg] https://#g' | sudo tee /etc/apt/sources.list.d/nvidia-container-toolkit.list
sudo apt-get update
sudo apt-get install -y nvidia-container-toolkit
sudo nvidia-ctk runtime configure --runtime=docker
sudo systemctl restart docker
```

Log out/in after the Docker group change, then verify container GPU access:

```bash
docker run --rm --gpus all nvidia/cuda:12.6.2-base-ubuntu22.04 nvidia-smi
```

Do not continue until this shows the NVIDIA T4.

## 6. Install and configure Klyvorek

```bash
git clone YOUR_REPOSITORY_URL klyvorek
cd klyvorek
cp .env.aws.example .env
nano .env
mkdir -p secrets
```

Set every placeholder in `.env`. Critical values:

```env
DJANGO_SECRET_KEY=<output of openssl rand -base64 48>
ALLOWED_HOSTS=api.klyvorek.com
CORS_ALLOWED_ORIGINS=https://www.klyvorek.com,https://klyvorek.com
CSRF_TRUSTED_ORIGINS=https://www.klyvorek.com,https://klyvorek.com,https://api.klyvorek.com
FRONTEND_URL=https://www.klyvorek.com

DB_HOST=<RDS endpoint>
DB_NAME=klyvorek
DB_USER=klyvorek_app
DB_PASSWORD=<RDS password>
DB_SSLMODE=require

AI_MODE=ollama
LOCAL_MODEL_URL=http://ollama:11434
LOCAL_MODEL_NAME=llama3.1:8b
OLLAMA_CONTEXT_LENGTH=8192
OLLAMA_REQUEST_TIMEOUT=300
CELERY_CONCURRENCY=1

AWS_S3_BUCKET=<private media bucket>
AWS_S3_BUCKET_REGION=us-east-1
AWS_ACCESS_KEY_ID=
AWS_SECRET_ACCESS_KEY=
```

## 7. Add the Cloudflare origin certificate

Cloudflare -> SSL/TLS -> Origin Server -> Create certificate:

- Hostname: `api.klyvorek.com`.
- Key type: RSA 2048 or ECC.
- Validity: your operational preference.

On EC2, save the certificate and private key exactly as:

```text
secrets/cloudflare-origin.pem
secrets/cloudflare-origin.key
```

Then:

```bash
chmod 600 secrets/cloudflare-origin.key
```

These files and `.env` are Git-ignored.

## 8. Start the complete backend

```bash
docker compose -f docker-compose.aws.yml up -d --build
docker compose -f docker-compose.aws.yml ps
docker compose -f docker-compose.aws.yml logs -f ollama-pull-model
```

The one-time pull service downloads `llama3.1:8b`; backend and Celery wait for it.
Then verify GPU placement and AI generation:

```bash
docker compose -f docker-compose.aws.yml exec ollama nvidia-smi
docker compose -f docker-compose.aws.yml exec ollama ollama ps
docker compose -f docker-compose.aws.yml exec backend python manage.py ai_check
```

`ollama ps` should report GPU usage. Create the administrator:

```bash
docker compose -f docker-compose.aws.yml exec backend python manage.py createsuperuser
```

## 9. Configure Cloudflare

DNS records:

- Proxied `A`: `api` -> EC2 Elastic IP.
- Proxied `CNAME`: `www` -> the S3 website endpoint.
- Redirect `klyvorek.com/*` to `https://www.klyvorek.com/$1` with a Redirect Rule.

TLS configuration:

- Zone default: **Full (Strict)**.
- Configuration Rule for `http.host eq "www.klyvorek.com"`: set SSL mode to
  **Flexible**, because S3 website endpoints support HTTP only.
- Never apply Flexible mode to `api.klyvorek.com`.
- Enable Always Use HTTPS and minimum TLS 1.2.
- Add a Cache Rule bypassing cache when hostname equals `api.klyvorek.com`.

Verify:

```bash
curl https://api.klyvorek.com/health/
```

Expected: `{"status":"ok"}`.

## 10. Build and deploy the frontend

On a trusted build machine:

```bash
cd charisma-expert
cp .env.production.example .env.production
nano .env.production
npm ci
npm run build
aws s3 sync dist/ s3://www.klyvorek.com --delete
```

Production build values:

```env
VITE_API_BASE_URL=https://api.klyvorek.com
VITE_GOOGLE_CLIENT_ID=<Google Web OAuth client ID>
```

Purge Cloudflare cache for `https://www.klyvorek.com/index.html`, then open the site.

## 11. Configure third parties

Google OAuth Web client:

- Authorized JavaScript origin: `https://www.klyvorek.com`.
- Use the same client ID in frontend and backend environments.

Stripe:

- Webhook: `https://api.klyvorek.com/api/payments/webhook/`.
- Subscribe to the event types used by `payments/webhooks.py`.
- Put the new signing secret in production `.env`, then recreate backend/Celery.

## 12. Final smoke test

```bash
docker compose -f docker-compose.aws.yml ps
docker compose -f docker-compose.aws.yml logs --tail=100 backend celery celery-beat ollama nginx
curl https://api.klyvorek.com/health/
```

In the browser verify: signup, Google login, OTP email, profile, all three document
types, PDF/DOCX test export, blog images/video, S3 media URL, and Stripe test checkout.
Watch the GPU during generation:

```bash
watch -n 1 nvidia-smi
```

## 13. Releases and cost controls

Backend release:

```bash
git pull --ff-only
docker compose -f docker-compose.aws.yml up -d --build
docker image prune -f
```

Enable CloudWatch alarms for instance status, GPU utilization/memory, CPU, disk,
RDS storage/connections, and failed health checks. Create EBS/RDS backup policies.
After usage stabilizes, consider a Compute Savings Plan; do not use Spot for the only
API/GPU instance because interruption takes the whole application offline.
