# law_backend

Law Enforcement Workflow Automation System — Django REST backend.

Secure, AI-assisted document generation (incident reports, search warrants,
arrest warrants) with subscriptions, a blog/media module, and an admin panel.

## Stack
Python 3.11 · Django 5 · Django REST Framework · PostgreSQL (pgvector) · Redis · AWS · Llama 3.1 8B
Self-hosted JWT auth (email + password) · Docker.

## Run (Docker)
```bash
cp .env.example .env        # then fill in your values
docker compose up --build
docker compose exec backend python manage.py seed_plans
docker compose exec backend python manage.py createsuperuser
```
API: http://localhost:8000/  ·  Admin: http://localhost:8000/admin/

See `BACKEND_STRUCTURE.md` for the full architecture and `docs/FORM_DATA_SCHEMAS.md`
for the document-generation request contract.
