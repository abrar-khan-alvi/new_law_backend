Yes. Several significant bottlenecks remain. Removing supervisor approval solved only one part of the testing journey.

No code changes were made during this audit.

## Critical bottlenecks

| Bottleneck | Current behavior | Recommended change |
|---|---|---|
| Google authentication | Currently disabled because neither Google client ID is configured | Configure Google OAuth before inviting testers |
| Email registration | Requires OTP email verification before login | Automatically sign in users with limited “tester” access, or make Google the primary path |
| Signup form | Requires badge, phone, rank, department, address, and state upfront | Reduce signup to name, email, and password; collect professional information later |
| Agency assignment | An administrator must assign an agency before any export | Permit watermarked “Test/Demo” exports without an agency |
| DOCX export | Disabled on the Free plan | Allow a limited number of free DOCX exports |
| AI infrastructure | Generation depends on Redis, Celery, and Bedrock all working | Add infrastructure health checks and a clearly labeled demo fallback |
| Default subscription | New users get no subscription if plans were not seeded | Ensure Free plan creation automatically during deployment |

## 1. Authentication bottlenecks

### Google login is not operational

I checked the active configuration:

- `GOOGLE_OAUTH_CLIENT_ID`: not configured
- `VITE_GOOGLE_CLIENT_ID`: not configured

The button is visible but disabled. Users cannot use the fastest onboarding path yet.

Relevant implementation: [GoogleSignInButton.jsx](C:/Users/abrar/Downloads/new_law_backend/charisma-expert/src/components/GoogleSignInButton.jsx), [accounts/views.py](C:/Users/abrar/Downloads/new_law_backend/accounts/views.py:129)

### Email signup asks for too much information

The frontend requires all of these before registration:

- First and last name
- Email
- Password and confirmation
- Badge number
- Phone number
- Rank/title
- Department name
- Department address
- State

This is a major conversion bottleneck. Most of this information is only necessary before official export—not before testing generation.

See [SignUp.jsx](C:/Users/abrar/Downloads/new_law_backend/charisma-expert/src/pages/SignUp.jsx:145).

Recommended flow:

```text
Name + email + password
          ↓
Immediate tester dashboard
          ↓
Generate sample documents
          ↓
Complete professional profile before official export
```

### Email verification is mandatory

Email/password users cannot log in until they enter the OTP. The verification email is sent synchronously during registration.

See [accounts/serializers.py](C:/Users/abrar/Downloads/new_law_backend/accounts/serializers.py:130).

A more serious edge case exists: if SMTP fails after the database user is created, registration can return an error while the account already exists. A retry may then fail because the email is already registered.

### Older `free` role accounts may be blocked

Generation accepts only `officer` and `admin` roles. Registration and new Google accounts use `officer`, but an existing account with the model’s default `free` role can enter the frontend dashboard and still receive a backend permission error.

See [accounts/permissions.py](C:/Users/abrar/Downloads/new_law_backend/accounts/permissions.py:4).

## 2. Subscription and quota bottlenecks

### Free usage is limited

The seeded Free plan currently allows:

- 7 incident reports per month
- 2 search/arrest warrants combined
- PDF export
- No DOCX export

See [seed_plans.py](C:/Users/abrar/Downloads/new_law_backend/subscriptions/management/commands/seed_plans.py:24).

The description is also inconsistent: it says five incident reports and implies two warrants of each type, while the actual limits are seven incidents and two combined warrants.

### Regeneration consumes another quota slot

Correcting or retrying a generated document consumes the same quota as generating a new one. A tester can exhaust the two-warrant allowance quickly through regeneration.

See [documents/views.py](C:/Users/abrar/Downloads/new_law_backend/documents/views.py:140).

For product testing, the first regeneration should be free, or failed/correction regenerations should not consume quota.

### Free DOCX export is blocked

Production export checks the plan, and Free has `can_export_docx=False`. A tester cannot evaluate one of the product’s primary outputs without starting a trial.

See [documents/views.py](C:/Users/abrar/Downloads/new_law_backend/documents/views.py:249).

Recommended Free testing allowance:

- 7 generations across all document types
- 2 PDF exports
- 2 DOCX exports
- At least one free regeneration per document

### Trial visibility is weak

A no-card seven-day trial exists, but users only encounter it on the Pricing page. The main paid-plan button attempts Stripe checkout, while the trial is a secondary action.

See [Pricing.jsx](C:/Users/abrar/Downloads/new_law_backend/charisma-expert/src/pages/Pricing.jsx:151).

### Trial counter-reset bug

When a trial expires or is cancelled, only the incident-report counter is reset. The warrant counters remain unchanged. A user can return to Free and immediately be over the Free warrant limit.

See [subscriptions/tasks.py](C:/Users/abrar/Downloads/new_law_backend/subscriptions/tasks.py:18) and [subscriptions/views.py](C:/Users/abrar/Downloads/new_law_backend/subscriptions/views.py:96).

## 3. Agency and profile export bottlenecks

### Every export requires administrator intervention

PDF and DOCX exports require an admin-assigned agency. This is now the largest remaining self-service bottleneck.

See [documents/views.py](C:/Users/abrar/Downloads/new_law_backend/documents/views.py:284).

A new tester can:

- Register
- Generate a document
- Edit the narrative
- Sign the document

But cannot export until an administrator manually assigns an agency.

Recommended solution: introduce two export modes.

```text
Test Export
- No agency assignment required
- Uses “KLYVOREK DEMO” heading
- Large TEST / NOT FOR OFFICIAL USE watermark
- Limited PDF and DOCX allowance

Official Export
- Complete profile required
- Admin-assigned agency required
- Agency identity, ORI and templates applied
```

This removes the testing bottleneck without allowing users to impersonate an agency.

### Profile requirements still block export

Every export requires:

- First name
- Last name
- Badge number
- Rank/title
- Agency assignment
- Officer review acknowledgment

Incident reports additionally need:

- Department name
- ORI
- Badge number

The agency can supply department name and ORI, but an agency with a blank ORI will still cause export failure.

There is also a UI inconsistency: Officer Profile may display “Ready for export” once an agency exists, even if that agency has no ORI and incident-report export will later fail.

See [accounts/serializers.py](C:/Users/abrar/Downloads/new_law_backend/accounts/serializers.py:55) and [documents/views.py](C:/Users/abrar/Downloads/new_law_backend/documents/views.py:267).

## 4. Form bottlenecks

The warrant forms require many fields before a tester can see any output.

Search warrant requires, among other fields:

- Court district
- Location/property description
- Address
- Items to seize
- Affiant background
- Connection between evidence and location
- Investigation summary
- Officer acknowledgment

See [CreateSearchWarrant.jsx](C:/Users/abrar/Downloads/new_law_backend/charisma-expert/src/pages/dashboard/CreateSearchWarrant.jsx:145).

Arrest warrant requires:

- Court district
- Defendant name
- Code section
- Offense description
- Affiant background
- Probable-cause facts
- Officer acknowledgment

See [CreateArrestWarrant.jsx](C:/Users/abrar/Downloads/new_law_backend/charisma-expert/src/pages/dashboard/CreateArrestWarrant.jsx:139).

These fields make sense for real documents, but a first-time tester needs either:

- “Load fictional example” buttons, or
- A guided demo with prepopulated fictional facts.

That would let users experience generation in one click without weakening the real workflow.

## 5. Runtime and infrastructure bottlenecks

### Generation requires the full async stack

A successful generation depends on:

- Django
- Database
- Redis
- Celery worker
- Bedrock
- Valid AWS credentials
- Model access
- Correct Bedrock region/model ID

The active environment is configured for Bedrock, not mock mode. Bedrock credentials and a model ID are present, but configuration does not prove that the account is authorized to invoke that model.

See [model_client.py](C:/Users/abrar/Downloads/new_law_backend/ai_engine/model_client.py:1).

### Redis/Celery failure can strand a request

Generation reserves quota, creates the document, and then calls Celery. If task submission fails because Redis is unavailable, the request is not safely rolled back.

The document can remain in `generating`, and quota may remain reserved. The recovery task also depends on Celery Beat and Redis, so the same outage can prevent recovery.

See [documents/views.py](C:/Users/abrar/Downloads/new_law_backend/documents/views.py:108) and [documents/tasks.py](C:/Users/abrar/Downloads/new_law_backend/documents/tasks.py:68).

### Only one generation runs at a time

Production Celery uses concurrency `1`. Multiple testers will queue behind one another. Warrants are particularly slow because they make two model calls:

1. Narrative generation
2. Constitutional quality review

A slow Bedrock request can delay everyone behind it.

### Frontend polling has no practical timeout

The generated-document screen polls every four seconds while the status is pending or generating. It has no user-facing queue position or timeout. A stuck request can appear to load indefinitely until the backend reclamation process runs.

See [GeneratedDocument.jsx](C:/Users/abrar/Downloads/new_law_backend/charisma-expert/src/pages/dashboard/GeneratedDocument.jsx:115).

### Model failure gives no demo fallback

If Bedrock rejects the request, generation fails completely. There is a mock model, but no controlled runtime fallback.

For testers, a good compromise is:

- Try Bedrock.
- If unavailable, explicitly offer “Generate labeled demo output.”
- Never silently substitute mock text for a real legal document.

## 6. Rate limiting

Anonymous traffic is limited to 100 requests per day per IP. Multiple testers behind the same department, office, VPN, or NAT gateway can share one IP and collectively reach this limit.

Authenticated users receive 1,000 requests per day, which polling and repeated generation can consume faster than expected.

See [core/settings/base.py](C:/Users/abrar/Downloads/new_law_backend/core/settings/base.py:188).

Login also locks after five failures for 30 minutes.

## Controls that are not currently bottlenecks

These no longer prevent export:

- Supervisor approval
- Prosecutor approval
- Quality-review flags
- Hallucination/leak flags
- Electronic signature

The signature is optional for export. The final officer-review checkbox is required, but it is a reasonable low-friction safety control.

## Recommended implementation order

1. Add a watermarked **Test Export** that needs no agency assignment.
2. Enable limited PDF and DOCX exports on Free.
3. Reduce email signup to name, email, and password.
4. Configure Google OAuth so one-click signup works.
5. Add “Load fictional example” to all three generators.
6. Make initial tester access independent of SMTP delivery.
7. Make Celery task submission transactional and recover quota immediately on broker failure.
8. Fix trial-expiry warrant-counter resets.
9. Add health monitoring for Redis, Celery, Bedrock and email.
10. Correct Free-plan descriptions and export-readiness calculations.

The most effective product structure is to separate **testing access** from **official agency use**. Testers should be able to generate and download clearly watermarked sample documents immediately; official exports should retain profile and admin-controlled agency requirements.s