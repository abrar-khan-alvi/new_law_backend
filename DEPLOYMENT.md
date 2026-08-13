# Deployment

The current production deployment target is Klyvorek on AWS:

- `www.klyvorek.com`: Cloudflare + S3 static frontend
- `api.klyvorek.com`: Cloudflare Full (Strict) + EC2 `g4dn.xlarge`
- NVIDIA T4 + Ollama `llama3.1:8b`
- Private RDS PostgreSQL and private S3 media storage

Follow [AWS_DEPLOYMENT.md](AWS_DEPLOYMENT.md) from top to bottom. The previous
`aiforlawenforcement.tech`/Flexible-TLS guide has been retired; Flexible TLS must never
be used for the authenticated API.
