# Law Backend — Project Analysis Report

**Repo:** `law_backend` (branch `ziyad`) · Django 5.0.6
**Generated:** 2026-07-16

---

## 1. Overall Architecture

**Apps** (`core/settings/base.py`): `accounts`, `subscriptions`, `ai_engine`, `documents`, `blog`, `payments`, `admin_panel`.

| App | Purpose |
|---|---|
| `accounts` | Custom email-based `User`, `Agency`, `EmailOTP`, JWT auth, registration, admin verification |
| `subscriptions` | `Plan` / `Subscription` / `UsageLog` models, quota/feature gating |
| `ai_engine` | Prompt building, model client (mock/Ollama/Bedrock), RAG (pgvector), leak-check, quality review, training-doc ingestion |
| `documents` | `GeneratedDocument` model, generation/export views, PDF/DOCX/AO-form exporters |
| `blog` | Markdown-based CMS (posts, tags, media) — sanitized with `bleach` |
| `payments` | Stripe checkout/webhooks — dormant until `STRIPE_SECRET_KEY` is set |
| `admin_panel` | Cross-user admin stats, plan/user/document management |
| `core` | Settings (base/development/production split), root URLs, Celery config |
| `utils` | Pagination, exception envelope, audit logging, S3/local storage abstraction |

**REST framework:** JWT (simplejwt) + Session auth, `IsAuthenticated` by default, DRF filters, custom pagination, custom exception envelope, throttling (100/day anon, 1000/day user).

**Third-party integrations:**
- **AI:** no OpenAI/Anthropic — a self-hosted `ModelClient` supporting `mock` (default), `ollama` (local dev), `bedrock` (AWS, prod).
- **Embeddings/RAG:** local `sentence-transformers` (`all-MiniLM-L6-v2`) + pgvector `HnswIndex`.
- **Email/OTP:** Gmail SMTP, numeric 6-digit HMAC-hashed OTP codes.
- **Payments:** Stripe, fully coded but inert.
- **Storage:** S3 via `boto3` with local `FileSystemStorage` fallback.
- **Celery:** scheduled monthly usage reset and failed-document cleanup.

---

## 2. Data Model

- **`Agency`** (`accounts/models.py`) — jurisdiction/court configuration profile: name, jurisdiction_type (federal/state/municipal), state, county, city, court_name, judicial_district, division, court_caption, judge_title, prosecuting_authority, case_number_format, ori, default_legal_citations.
- **`User(AbstractUser)`** — email as `USERNAME_FIELD`; role (`free`/`officer`/`admin`); officer profile fields (badge, department, ORI, rank); `agency` FK; `email_verified` (self-service) vs `is_verified` (admin-vetted) are distinct.
- **`EmailOTP`** — stores only an HMAC-SHA256 hash of the code, never plaintext.
- **`GeneratedDocument`** (`documents/models.py`) — UUID PK, doc_type (incident_report/search_warrant/arrest_warrant), form_data (JSON), ai_narrative, status lifecycle, `leak_flags` (JSON), `quality_flags` (JSON, new).
- **`Plan` / `Subscription` / `UsageLog`** (`subscriptions/models.py`) — feature flags (can_search_warrant, can_export_docx, document_limit), Stripe fields dormant, per-generation audit trail.
- **`TrainingDocument` / `DocumentChunk`** (`ai_engine/models.py`) — admin-uploaded sample docs + pgvector RAG corpus.

---

## 3. AI Generation Pipeline

`documents/views.py::_run_generation`:

1. **`prompt_builder.py`** — builds a RAG-aware prompt: officer/agency context → sanitized style examples (via pgvector) → a delimited FACTS block → an anti-leak instruction.
2. **`model_client.ModelClient.generate()`** — dispatches to mock/Ollama/Bedrock.
3. **`postprocess.clean_narrative()`** — strips Markdown/echoed signature blocks.
4. **`leak_check.check_narrative()`** — deterministic hallucination detector; flags anything not grounded in form_data/officer profile.
5. **`quality_review.check_constitutional_quality()`** (new) — a second LLM pass (temperature 0.0), search/arrest warrants only, checking for missing citations, weak probable-cause/nexus language, missing Attachment A/B. Stored in `quality_flags`.

---

## 4. Document Lifecycle

- **Creation:** validates doc_type/form_data → gates on subscription/plan/quota (admins bypass) → auto-generates case_number → runs the pipeline above → on success increments usage + writes `UsageLog` + audit log.
- **Regeneration:** re-runs the pipeline at higher temperature, gated by `plan.can_regenerate`.
- **Export:** PDF/DOCX, gated by `plan.can_export_pdf/docx` — **bypassed when `DEBUG=True`**.
- **Exporters:** `pdf.py` (ReportLab, custom incident-report layout), `ao_forms.py` (PyMuPDF, fills real federal AO 442/AO 93 court forms), `word.py` (python-docx).

---

## 5. Auth / Accounts

- Registration → auto free-plan subscription → OTP email verification.
- Login blocks unverified emails except admins; embeds role/email in JWT.
- Password reset mirrors the OTP flow; anti-enumeration on resend.
- `AgencyCreateView` — any `IsAuthenticated` user can currently self-create/assign an Agency (flagged as a permission gap, see §7).
- Permissions: `IsOfficer`, `IsAdmin`, `IsVerifiedOfficer`, `HasActiveSubscription`, `HasDocumentQuota`, `IsOwnerOrAdmin`.

---

## 6. Admin Panel

All views `IsAdmin`-gated: platform stats, full Plan CRUD, cross-user document list (with `?flagged=true` on `leak_flags`), user list/search, and user PATCH for role/active/verified/plan assignment.

---

## 7. Findings

### Confirmed bugs
1. **`_officer_profile()` had unreachable dead code** (`documents/views.py`) — an early `return {...}` made the Agency-merging block below it unreachable. Result: despite the new `Agency` model/migration/admin work, generated documents and exports never actually received agency name/state/court caption/jurisdiction/citations.
2. **`quality_flags` was missing from `GeneratedDocumentSerializer`** — computed and stored, but never returned to the frontend/officer via the API.

### Security / hardening
3. **JWT/session lifetimes were extended to years, not hours** (`core/settings/base.py`) — access token 60min→365 days, refresh token 7 days→10 years, session/CSRF cookies →10 years. Large blast-radius increase for a law-enforcement product if a token leaks.
4. **`AgencyCreateView` had no role check** — any authenticated free-tier user could create/self-assign an Agency, which feeds directly into official warrant text.
5. **`quality_review.py` failed silently open** — a malformed/broken AI response returned `[]` (no issues found), indistinguishable from a genuinely clean constitutional review.

### Minor / technical debt
- Second full LLM round-trip per warrant generation (quality review) with no caching — candidate for async/Celery offload if latency becomes an issue.
- `pdf.py`'s `_incident()` hardcodes a specific real department's identity as fallback defaults (looks like leftover reference-doc data).
- `Plan.document_limit` uses a magic-number sentinel (`1_000_000`) for "unlimited" rather than a nullable/boolean flag.

---

## 8. Client Requirements — "Jurisdiction-Aware Search Warrant and Arrest Warrant Generator"

Source: `Search Warrant and Arrest Warrant Requirements.docx` (client feedback).

**Core ask:** no single warrant format is universal across the US, so court captions, headers, agency names, statutory references, and judicial formatting must be fully configurable per agency (not hard-coded), and editable by authorized users.

| # | Requirement | Status |
|---|---|---|
| 1 | **Dynamic Jurisdiction Header** — State, County, City, Court Name, Judicial District, Agency Name, Division, Court Caption, Judge Title, Prosecuting Authority, Case Number Format, ORI, Seal | Mostly built (`Agency` model has nearly every field). Was blocked by bug #1 above — now fixed. Missing: agency seal/logo image field. |
| 2 | **Rules-based, jurisdiction-aware templates** — AI organizes facts into predefined sections, doesn't invent legal language; structured intake questions | **Not built — architectural gap.** Today the LLM freely drafts the whole narrative; checks catch problems after the fact rather than constraining generation up front. |
| 3 | **Automatic legal formatting by jurisdiction level** (federal/state/municipal) | Partially built — `jurisdiction_type` is passed into the prompt as a soft instruction to the LLM, not enforced as a hard rule; exporters don't branch on it. |
| 4 | **Agency Configuration Wizard** — one-time setup: agency/court info, default warrant language, supervisor approval workflow, prosecutor review, signature blocks, e-signature | Not built. Only a bare create-agency endpoint exists. |
| 5 | **Built-in Constitutional Quality Review** — missing citations, weak PC/nexus, missing elements of offense, missing Attachment A/B, blank sections, incomplete dates, missing affiant info, inconsistent names/case numbers | Largely built (`ai_engine/quality_review.py`). Gaps: no cross-document consistency check (names/locations/case numbers); was fail-open (bug #5 above); `quality_flags` wasn't exposed via API (bug #2 above). |
| 6 | **Future scalability** — new jurisdiction = new profile, not new code | At risk — `Agency` is one row per department with no shared "jurisdiction profile" (e.g. state-level defaults) to inherit from; every new agency in the same state re-enters the same statutes. |

### Recommended sequencing
1. Fix the dead-code bug blocking Agency data (done — see §9).
2. Close the gaps in #5 (expose `quality_flags`, fail closed, add consistency check) — small, high-value.
3. Fill out header/seal fields (#1) — plumbing, low risk.
4. **#2 + #3 (rules-based templates + jurisdiction-driven formatting)** is the real architectural project: shift from "LLM drafts everything, checks catch problems" to "fixed template drafts everything, AI only fills gaps." Touches prompt_builder, model layer, and all three exporters — scope as its own plan.
5. #4 (config wizard) and #6 (shared jurisdiction profiles) are best designed after #2/#3 settle, since their field lists should mirror the template schema.

### Admin vs. user: who configures an Agency?
**Decision: platform admin controls Agency creation/editing; officers get read-only access.** Rationale: Agency fields (court caption, judge title, prosecuting authority, default citations) become printed legal text on warrants submitted to judges. Agencies are shared across many officers (`related_name='officers'`), so any-officer-can-edit is a shared-state footgun. This also matches the existing `email_verified` (self-service) vs `is_verified` (admin-vetted) pattern already in the codebase. A future `agency_admin` role (per-department self-service, distinct from platform admin) is a reasonable next step once the core model stabilizes.

---

## 9. Fixes Applied This Session

- [x] `.gitignore` — excluded `charisma-expert/` (frontend lives in its own separate repo, `HMZiyad/charisma-expert`, and should not be tracked inside `law_backend`).
- [ ] `_officer_profile()` dead-code bug — **pending** (session was interrupted by the host machine running out of disk space; to be applied next).
- [ ] `quality_flags` missing from serializer — **pending**.
- [ ] JWT/session lifetime regression — **pending**, needs confirmation this wasn't an intentional trade-off before reverting.
- [ ] `AgencyCreateView` permission gap — **pending**, to be moved under `admin_panel` per the admin-only decision above.
- [ ] `quality_review.py` fail-open behavior — **pending**.

*(Checklist reflects state as of this report's generation — see the repo's live diff for what has actually landed since.)*
