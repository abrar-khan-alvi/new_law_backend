# API Reference — Law Enforcement Workflow Automation System

**Base URL (local Docker):** `http://localhost:8000`
**Auth:** JWT Bearer. Log in, then send `Authorization: Bearer <access_token>` on protected routes.
**Content-Type:** `application/json` unless noted as `multipart/form-data` (file uploads).

Error shape (most endpoints):
```json
{ "error": { "detail": "Human readable message", "code": "machine_code" } }
```
DRF validation errors look like: `{ "field_name": ["error message"] }`.

Roles: `free`, `officer`, `admin`. Most document routes require an **officer** (or admin). Admin-only routes are marked 🔒 **admin**.

---

## Postman quick-start
1. `POST /api/auth/register/` → create an officer account.
2. Verify email (dev: see the link in the backend logs, or have an admin verify) — login is blocked until `email_verified` is true.
3. `POST /api/auth/login/` → copy `access`. Set a Postman collection variable `token`.
4. Add header `Authorization: Bearer {{token}}` to protected requests.
5. `POST /api/documents/generate/` → generate. `POST /api/documents/{id}/export/` → download PDF/DOCX.

> Tip: to skip email verification while testing, an admin can verify accounts, or set `email_verified=True` in Django admin / shell.

---

# 1. Authentication — `/api/auth/`

### POST `/api/auth/register/` — public
Create an account (role defaults to `officer`). Sends a verification email.
**Request:**
```json
{
  "email": "officer@dept.gov",
  "password": "StrongPass123!",
  "password2": "StrongPass123!",
  "first_name": "Edward",
  "last_name": "Brown",
  "badge_number": "2911",
  "department_name": "Life University Police Department",
  "department_address": "1269 Barclay Cir SE, Marietta, GA",
  "department_state": "GA",
  "ori": "GA0331100",
  "phone_number": "770-426-2911",
  "rank": "Police Officer",
  "division": "Patrol"
}
```
**Response `201`:**
```json
{
  "message": "Account created. Check your email to verify your address.",
  "user": { "id": 5, "email": "officer@dept.gov", "full_name": "Edward Brown", "role": "officer", "email_verified": false, "...": "..." }
}
```

### POST `/api/auth/verify-email/` — public
**Request:** `{ "uid": "<from email link>", "token": "<from email link>" }`
**Response `200`:** `{ "message": "Email verified. You can now log in." }`

### POST `/api/auth/resend-verification/` — public
**Request:** `{ "email": "officer@dept.gov" }`
**Response `200`:** `{ "message": "If the account exists and is unverified, an email was sent." }`

### POST `/api/auth/login/` — public
**Request:** `{ "email": "officer@dept.gov", "password": "StrongPass123!" }`
**Response `200`:**
```json
{
  "refresh": "eyJhbGciOi...",
  "access": "eyJhbGciOi...",
  "user": { "id": 5, "email": "officer@dept.gov", "full_name": "Edward Brown", "role": "officer", "subscription": { "plan": "free", "...": "..." } }
}
```
Login fails with `400` if the email isn't verified.

### POST `/api/auth/token/refresh/` — public
**Request:** `{ "refresh": "<refresh_token>" }`
**Response `200`:** `{ "access": "<new_access_token>" }`

### POST `/api/auth/logout/` — auth
Blacklists the refresh token.
**Request:** `{ "refresh": "<refresh_token>" }`
**Response `205`:** `{ "message": "Logged out." }`

### GET `/api/auth/profile/` — auth
**Response `200`:**
```json
{
  "id": 5, "email": "officer@dept.gov", "full_name": "Edward Brown",
  "first_name": "Edward", "last_name": "Brown", "role": "officer",
  "badge_number": "2911", "department_name": "Life University Police Department",
  "department_address": "...", "department_state": "GA", "ori": "GA0331100",
  "phone_number": "770-426-2911", "rank": "Police Officer", "division": "Patrol",
  "email_verified": true, "is_verified": false,
  "subscription": {
    "plan": "free", "plan_display": "Free", "status": "active",
    "documents_generated_this_month": 0, "document_limit": 3,
    "current_period_end": "2026-07-20T00:00:00Z"
  },
  "last_active": "2026-06-20T10:00:00Z", "created_at": "2026-06-01T09:00:00Z"
}
```

### PATCH `/api/auth/profile/` — auth
Update editable profile fields (any subset).
**Request:** `{ "rank": "Sergeant", "division": "Investigations", "phone_number": "770-000-0000" }`
**Response `200`:** full profile (as GET).

### POST `/api/auth/change-password/` — auth
**Request:** `{ "old_password": "StrongPass123!", "new_password": "EvenStronger456!" }`
**Response `200`:** `{ "message": "Password changed." }`

### POST `/api/auth/password-reset/` — public
**Request:** `{ "email": "officer@dept.gov" }`
**Response `200`:** `{ "message": "If the account exists, a reset email was sent." }`

### POST `/api/auth/password-reset/confirm/` — public
**Request:** `{ "uid": "<from email>", "token": "<from email>", "new_password": "NewPass789!" }`
**Response `200`:** `{ "message": "Password has been reset. You can now log in." }`

### POST `/api/auth/verify-officer/<pk>/` — 🔒 admin
Vets an officer account (`is_verified=true`).
**Response `200`:** `{ "message": "officer@dept.gov has been verified." }`

### GET `/api/auth/users/` — 🔒 admin
List all users (array of profile objects).

---

# 2. Documents — `/api/documents/`

### POST `/api/documents/generate/` — officer
Creates a document, builds the prompt (with RAG style examples), calls the model, runs the leak-check, and returns the result.

**Request envelope:** `{ "doc_type": "...", "narrative_style": "first_person|third_person", "form_data": { ... } }`

**Example — incident report:**
```json
{
  "doc_type": "incident_report",
  "narrative_style": "third_person",
  "form_data": {
    "case_number": null,
    "incident": {
      "categories": ["Larceny", "General Information"],
      "urgency": "normal",
      "date": "2026-01-06", "time": "19:30",
      "location": "University Commons Room #1240-B"
    },
    "involved_parties": [
      { "role": "complainant", "full_name": "Justin Kim", "id_number": "0281984", "phone": "267-752-0534" },
      { "role": "alleged", "full_name": "Martrece Smith", "id_number": "0271959" }
    ],
    "property_items": [{ "type": "currency", "value": 400, "status": "missing" }],
    "notifications": { "weapon_involved": false, "alcohol_drugs": false, "is_hazing": false },
    "facts": {
      "who": "Complainant Justin Kim; alleged party Martrece Smith (roommate)",
      "what": "Report of $400 in currency missing from a wallet",
      "when": "Between 1930 on 01/04 and 1930 on 01/06",
      "where": "Dorm room NC1 1240B",
      "how": "Wallet found under bed, cash missing, no other contents taken",
      "officer_actions": "Took report at 1945; called Smith at 2001, left voicemail; Smith returned call 2010 and denied knowledge."
    },
    "attachments": []
  }
}
```

**Example — search warrant** (`doc_type: "search_warrant"`):
```json
{
  "doc_type": "search_warrant",
  "narrative_style": "first_person",
  "form_data": {
    "case_number": "2:23-mj-281",
    "court": { "district": "Central District of California", "judge_name": "Patricia Donahue" },
    "offenses": [{ "code_section": "18 U.S.C. § 1030", "description": "Computer fraud" }],
    "place_to_search": { "type": "server", "description": "Servers at the data center", "address": "Los Angeles, CA" },
    "items_to_seize": ["All data and logs relating to the offense"],
    "execution": { "execute_by_date": "2026-07-01", "time_window": "anytime" },
    "probable_cause": {
      "affiant_background": "FBI Special Agent, cybercrime since 2018.",
      "investigation_summary": "Servers used to host the operation.",
      "timeline": ["2026-06-01: forensic images obtained"],
      "nexus_to_place": "Evidence physically resides on these servers."
    }
  }
}
```

**Example — arrest warrant** (`doc_type: "arrest_warrant"`):
```json
{
  "doc_type": "arrest_warrant",
  "narrative_style": "third_person",
  "form_data": {
    "case_number": null,
    "court": { "district": "Northern District of Georgia" },
    "defendant": { "full_name": "John A. Doe" },
    "charging_document": "complaint",
    "offense": { "code_section": "18 U.S.C. § 2113(a)", "brief_description": "Bank robbery by force and violence" },
    "identifiers": {
      "aliases": ["Johnny D"], "date_of_birth": "1990-04-12",
      "height": "5'11\"", "weight": "180 lbs", "sex": "M", "race": "White",
      "last_known_residence": "123 Peachtree St, Atlanta, GA",
      "vehicle_description": "Black 2018 Honda Civic, GA tag ABC1234"
    },
    "probable_cause": {
      "include_affidavit": true,
      "affiant_background": "Detective, Atlanta PD, 8 years.",
      "facts": "Surveillance and eyewitness ID place the defendant at the scene.",
      "timeline": ["2026-05-01: Robbery occurred"]
    }
  }
}
```
> `charging_document` enum: `indictment`, `superseding_indictment`, `information`, `superseding_information`, `complaint`, `probation_violation`, `supervised_release_violation`, `violation_notice`, `court_order`.

**Response `201`:**
```json
{
  "id": "86b9d0dd-590d-4b49-a78e-3b0285a05132",
  "doc_type": "incident_report",
  "case_number": "LE-Y44AGTELBM",
  "form_data": { "...": "..." },
  "ai_narrative": "On 2026-01-06 at 1945 hours, Police Officer Edward Brown ...",
  "narrative_style": "third_person",
  "status": "completed",
  "error_message": "",
  "model_used": "llama3.1:8b",
  "tokens_used": 0,
  "generation_time_ms": 95304,
  "leak_flags": [ { "type": "proper_noun", "value": "Chicago" } ],
  "created_at": "2026-06-20T10:05:00Z",
  "updated_at": "2026-06-20T10:05:00Z"
}
```
- `leak_flags` lists details in the narrative **not** found in the officer's input (possible hallucination / RAG leak) — for officer review. Empty `[]` = clean.

**Error responses:** `403` (no subscription / plan doesn't include doc_type / quota exceeded), `503` (AI generation failed), `400` (validation).

### GET `/api/documents/` — officer
Paginated history of the current officer's documents.
**Response `200`:**
```json
{
  "count": 15, "next": "http://localhost:8000/api/documents/?page=2", "previous": null,
  "results": [
    { "id": "uuid", "doc_type": "incident_report", "case_number": "LE-...", "status": "completed", "narrative_style": "third_person", "created_at": "..." }
  ]
}
```

### GET `/api/documents/<uuid:pk>/` — auth (owner or admin)
Full document (same shape as the generate `201` response).

### POST `/api/documents/<uuid:pk>/regenerate/` — officer
Re-runs generation (slightly higher temperature). Requires a plan with `can_regenerate`.
**Request:** *(no body required)*
**Response `200`:** full document object (new narrative + leak_flags).

### POST `/api/documents/<uuid:pk>/export/` — officer
Returns a **binary file** (set Postman to "Send and Download").
**Request:**
```json
{ "format": "pdf", "edited_text": "(optional) officer-edited narrative to use instead of ai_narrative" }
```
- `format`: `"pdf"` or `"docx"`.
- Warrants render on the **official AO 442 / AO 93** forms; incident reports use the generic template.
**Response `200`:** file bytes (`application/pdf` or the DOCX content type), `Content-Disposition: attachment`.
**Errors:** `400` (bad format), `403` (plan doesn't allow that export format), `404`.

---

# 3. AI Engine (training data / RAG) — `/api/ai/` — 🔒 admin

### GET `/api/ai/training-docs/` — 🔒 admin
Optional `?doc_type=incident_report`.
**Response `200`:**
```json
[
  { "id": 1, "doc_type": "incident_report", "title": "Sample IR", "original_filename": "ir.pdf",
    "is_indexed": true, "chunk_count": 5, "uploaded_by_email": "admin@dept.gov", "created_at": "..." }
]
```

### POST `/api/ai/training-docs/upload/` — 🔒 admin — `multipart/form-data`
Parses text, stores the file, and queues async embedding/indexing into pgvector.
**Form fields:** `file` (pdf/docx/txt), `doc_type` (`incident_report|search_warrant|arrest_warrant`), `title` (optional).
**Response `201`:**
```json
{ "message": "Uploaded. Indexing queued.",
  "training_document": { "id": 2, "doc_type": "incident_report", "is_indexed": false, "chunk_count": 0, "...": "..." } }
```

---

# 4. Subscriptions — `/api/subscriptions/`

### GET `/api/subscriptions/plans/` — public
**Response `200`:**
```json
[
  { "id": 1, "name": "free", "display_name": "Free", "description": "...",
    "price_monthly": "0.00", "price_yearly": "0.00", "document_limit": 3,
    "can_incident_report": true, "can_search_warrant": false, "can_arrest_warrant": false,
    "can_export_pdf": true, "can_export_docx": false, "can_save_history": true,
    "can_regenerate": false, "support_level": "community", "is_active": true, "sort_order": 0 }
]
```

### GET `/api/subscriptions/status/` — auth
**Response `200`:**
```json
{
  "id": 10, "plan": { "id": 1, "name": "free", "...": "..." }, "status": "active",
  "billing_period": "monthly", "current_period_start": "...", "current_period_end": "...",
  "documents_generated_this_month": 0, "usage_reset_date": "...", "created_at": "..."
}
```
`404` if no subscription.

### POST `/api/subscriptions/cancel/` — auth
Currently dormant (billing disabled).
**Response `503`:** `{ "error": { "detail": "Billing is not enabled yet.", "code": "payments_disabled" } }`

---

# 5. Payments (Stripe) — `/api/payments/` — **DORMANT** until billing is enabled

### POST `/api/payments/create-checkout/` — auth
**Request:** `{ "plan": "pro", "billing_period": "monthly" }`
**Response (now):** `503` `{ "error": { "detail": "Payments are not enabled yet.", "code": "payments_disabled" } }`
**Response (when enabled):** `{ "checkout_url": "https://checkout.stripe.com/...", "session_id": "cs_..." }`

### POST `/api/payments/webhook/` — public (Stripe)
Stripe event receiver. Returns `503` while dormant; `{ "received": true }` when enabled.

### GET `/api/payments/billing-history/` — auth
**Response `200`:** `{ "payments": [ ... ], "invoices": [ ... ] }`

---

# 6. Admin Panel — `/api/admin-panel/` — 🔒 admin

### GET `/api/admin-panel/stats/` — 🔒 admin
**Response `200`:**
```json
{
  "users": { "total": 42, "officers": 38, "verified": 30, "new_7d": 5 },
  "documents": { "total": 120, "last_30d": 45, "by_type": [ { "doc_type": "incident_report", "count": 80 } ] },
  "subscriptions": { "active": 40, "by_plan": [ { "plan__name": "free", "count": 35 } ] }
}
```

### GET `/api/admin-panel/plans/` — 🔒 admin
All plans (incl. inactive). Same item shape as public plans.

### POST `/api/admin-panel/plans/` — 🔒 admin
Create a plan. **Request:** a Plan object (see fields in §4). **Response `201`:** the created plan.

### GET / PATCH / DELETE `/api/admin-panel/plans/<pk>/` — 🔒 admin
- `GET` → plan object.
- `PATCH` → partial update, e.g. `{ "price_monthly": "29.00", "can_arrest_warrant": true }`.
- `DELETE` → `204` (fails `400` if the plan has active subscriptions).

### GET `/api/admin-panel/users/` — 🔒 admin
Paginated. Filters: `?q=<email substring>`, `?role=officer`.
**Response `200`:**
```json
{ "count": 42, "next": null, "previous": null,
  "results": [ { "id": 5, "email": "...", "full_name": "...", "role": "officer", "department_name": "...",
                 "is_active": true, "is_verified": false, "email_verified": true, "plan": "free",
                 "last_active": "...", "created_at": "..." } ] }
```

### PATCH `/api/admin-panel/users/<pk>/` — 🔒 admin
Activate/deactivate, set role, verify.
**Request (any subset):** `{ "is_active": false }` or `{ "role": "officer", "is_verified": true }`
**Response `200`:** the updated admin-user object.

---

# 7. Blog — `/api/blog/`

### GET `/api/blog/posts/` — public
Paginated published posts. Filters via query params (see `BlogPostFilter`, e.g. category/tag/search).
**Response `200`:** standard paginated list of post summaries (title, slug, excerpt, cover_image_url, author_name, tags, counts, dates).

### POST `/api/blog/posts/` — 🔒 admin
**Request:**
```json
{ "title": "Welcome", "content": "# Markdown body", "excerpt": "Short summary",
  "category": "news", "tags": ["update", "release"], "is_featured": false, "publish": true }
```
**Response `201`:** full post (with rendered `content_html`).

### GET `/api/blog/posts/<slug>/` — public
Full post detail (increments view count). Includes `content`, `content_html`, `media`.

### PATCH `/api/blog/posts/<slug>/` — 🔒 admin
Partial update; include `"publish": true|false` to toggle publication.

### DELETE `/api/blog/posts/<slug>/` — 🔒 admin → `204`

### POST `/api/blog/posts/<slug>/media/` — 🔒 admin — `multipart/form-data` or JSON
- File upload: form fields `media_type` (`image|video`), `file`, optional `alt_text`, `caption`, `order`.
- Embed: JSON `{ "media_type": "video_url", "video_url": "https://youtube.com/watch?v=...", "caption": "..." }`
**Response `201`:** the media object (with `url` / `embed_html`).

### DELETE `/api/blog/posts/<slug>/media/<media_id>/` — 🔒 admin → `204`

### GET `/api/blog/tags/` — public
**Response `200`:** `[ { "id": 1, "name": "update", "slug": "update" } ]`

---

# 8. Health
### GET `/health/` — public → `{ "status": "ok" }`

---

## Notes for testing
- **Plan gating:** the `free` plan only allows `incident_report` + PDF export, no regenerate, 3 docs/month. Use an admin to put a test officer on `pro` for full access (or run `python manage.py smoke_test`, which provisions `smoke_officer@example.com` / `SmokeTest123!` on Pro).
- **AI mode:** with `AI_MODE=ollama`, the first generation can take ~100–170s (model load); subsequent ones are faster. With `AI_MODE=mock` generation is instant but returns a placeholder narrative.
- **Binary downloads:** for `/export/`, use Postman's **Send and Download** to save the PDF/DOCX.
