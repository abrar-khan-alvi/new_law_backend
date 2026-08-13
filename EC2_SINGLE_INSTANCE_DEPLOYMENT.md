# Klyvorek single-instance deployment

This is the low-cost beta architecture for an ARM64 `t4g.xlarge`. PostgreSQL,
Redis, Django, Celery, the React frontend, Nginx, and Ollama all run in Docker on the same EC2 host.
The model is `llama3.2:latest`. No RDS or NVIDIA runtime is required.

## Server installation

```bash
sudo apt update
sudo apt install -y docker.io docker-compose-v2 git
sudo usermod -aG docker ubuntu
sudo systemctl enable --now docker
```

Log out and reconnect after adding the Docker group.

## Application configuration

```bash
git clone https://github.com/abrar-khan-alvi/new_law_backend.git klyvorek
cd klyvorek
cp .env.aws.example .env
mkdir -p secrets
openssl rand -base64 48
openssl rand -base64 32
nano .env
```

Use the first generated value for `DJANGO_SECRET_KEY` and the second for
`DB_PASSWORD`. Complete every other production credential in `.env`; never copy
the development `.env` to the server.

The database settings must remain:

```env
USE_SQLITE=False
DB_NAME=klyvorek
DB_USER=klyvorek_app
DB_HOST=db
DB_PORT=5432
DB_SSLMODE=disable
```

The model settings must remain:

```env
AI_MODE=ollama
LOCAL_MODEL_URL=http://ollama:11434
LOCAL_MODEL_NAME=llama3.2:latest
OLLAMA_CONTEXT_LENGTH=4096
OLLAMA_REQUEST_TIMEOUT=300
```

## TLS and startup

Create a Cloudflare Origin Certificate for `api.klyvorek.com` and save it as:

```text
secrets/cloudflare-origin.pem
secrets/cloudflare-origin.key
```

Then start the stack:

```bash
chmod 600 secrets/cloudflare-origin.key
docker compose -f docker-compose.aws.yml up -d --build
docker compose -f docker-compose.aws.yml ps
docker compose -f docker-compose.aws.yml logs -f ollama-pull-model
```

After the model download finishes:

```bash
docker compose -f docker-compose.aws.yml exec backend python manage.py ai_check
docker compose -f docker-compose.aws.yml exec backend python manage.py createsuperuser
```

Create a proxied Cloudflare `A` record: `api` -> the EC2 Elastic IP. Set the
same proxied `A` record for `www` and the apex (`@`). Set the Cloudflare zone TLS
mode to Full (Strict), then verify:

```bash
curl https://api.klyvorek.com/health/
```

## Local database backup

This creates a backup on the same EC2 disk. Download copies off the instance
regularly because a single-instance deployment has no managed failover.

```bash
mkdir -p backups
docker compose -f docker-compose.aws.yml exec -T db pg_dump -U klyvorek_app -d klyvorek -Fc > backups/klyvorek.dump
```
