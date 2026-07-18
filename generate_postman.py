import json

collection = {
    "info": {
        "name": "Law Enforcement Workflow Automation System",
        "schema": "https://schema.getpostman.com/json/collection/v2.1.0/collection.json"
    },
    "variable": [
        {"key": "base_url", "value": "http://localhost:8000"},
        {"key": "token", "value": ""}
    ],
    "item": []
}

def auth_item():
    return {
        "type": "bearer",
        "bearer": [{"key": "token", "value": "{{token}}", "type": "string"}]
    }

def create_request(name, method, path, body=None, auth=False, test_script=None):
    req = {
        "name": name,
        "request": {
            "method": method,
            "url": {
                "raw": "{{base_url}}" + path,
                "host": ["{{base_url}}"],
                "path": [p for p in path.split("/") if p]
            }
        }
    }
    if auth:
        req["request"]["auth"] = auth_item()
    if body:
        if isinstance(body, dict):
            req["request"]["body"] = {
                "mode": "raw",
                "raw": json.dumps(body, indent=4),
                "options": {"raw": {"language": "json"}}
            }
        elif body == "form-data":
            req["request"]["body"] = {
                "mode": "formdata",
                "formdata": []
            }
    if test_script:
        req["event"] = [
            {
                "listen": "test",
                "script": {
                    "exec": test_script.split("\n"),
                    "type": "text/javascript"
                }
            }
        ]
    return req

def create_folder(name, items):
    return {
        "name": name,
        "item": items
    }

# 1. Auth
auth_items = [
    create_request("Register", "POST", "/api/auth/register/", {
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
    }),
    create_request("Verify Email", "POST", "/api/auth/verify-email/", {"email": "officer@dept.gov", "code": "123456"}),
    create_request("Resend Verification", "POST", "/api/auth/resend-verification/", {"email": "officer@dept.gov"}),
    create_request("Login", "POST", "/api/auth/login/", {"email": "officer@dept.gov", "password": "StrongPass123!"}, test_script="if (pm.response.code === 200) {\n    pm.collectionVariables.set(\"token\", pm.response.json().access);\n}"),
    create_request("Token Refresh", "POST", "/api/auth/token/refresh/", {"refresh": "<refresh_token>"}),
    create_request("Logout", "POST", "/api/auth/logout/", {"refresh": "<refresh_token>"}, auth=True),
    create_request("Profile", "GET", "/api/auth/profile/", auth=True),
    create_request("Update Profile", "PATCH", "/api/auth/profile/", {"rank": "Sergeant", "division": "Investigations", "phone_number": "770-000-0000"}, auth=True),
    create_request("Change Password", "POST", "/api/auth/change-password/", {"old_password": "StrongPass123!", "new_password": "EvenStronger456!"}, auth=True),
    create_request("Password Reset Request", "POST", "/api/auth/password-reset/", {"email": "officer@dept.gov"}),
    create_request("Password Reset Confirm", "POST", "/api/auth/password-reset/confirm/", {"email": "officer@dept.gov", "code": "123456", "new_password": "NewPass789!"}),
    create_request("List Users (Admin)", "GET", "/api/auth/users/", auth=True)
]
collection["item"].append(create_folder("1. Authentication", auth_items))

# 2. Documents
doc_items = [
    create_request("Generate Document (IR)", "POST", "/api/documents/generate/", {
        "doc_type": "incident_report",
        "narrative_style": "third_person",
        "form_data": {
            "case_number": None,
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
            "notifications": { "weapon_involved": False, "alcohol_drugs": False, "is_hazing": False },
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
    }, auth=True),
    create_request("Generate Document (Search Warrant)", "POST", "/api/documents/generate/", {
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
    }, auth=True),
    create_request("Generate Document (Arrest Warrant)", "POST", "/api/documents/generate/", {
        "doc_type": "arrest_warrant",
        "narrative_style": "third_person",
        "form_data": {
            "case_number": None,
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
                "include_affidavit": True,
                "affiant_background": "Detective, Atlanta PD, 8 years.",
                "facts": "Surveillance and eyewitness ID place the defendant at the scene.",
                "timeline": ["2026-05-01: Robbery occurred"]
            }
        }
    }, auth=True),
    create_request("List Documents", "GET", "/api/documents/", auth=True),
    create_request("Get Document", "GET", "/api/documents/:pk/", auth=True),
    create_request("Regenerate Document", "POST", "/api/documents/:pk/regenerate/", auth=True),
    create_request("Export Document", "POST", "/api/documents/:pk/export/", {"format": "pdf", "edited_text": ""}, auth=True),
    create_request("Supervisor Review", "POST", "/api/documents/:pk/supervisor-review/", {"approved": True, "notes": ""}, auth=True),
    create_request("Prosecutor Review", "POST", "/api/documents/:pk/prosecutor-review/", {"reviewer_name": "A.D.A. Jane Smith", "approved": True, "notes": ""}, auth=True),
    create_request("Sign Document", "POST", "/api/documents/:pk/sign/", {"full_name": "Officer Edward Brown"}, auth=True)
]
collection["item"].append(create_folder("2. Documents", doc_items))

# 3. AI Engine
ai_items = [
    create_request("List Training Docs", "GET", "/api/ai/training-docs/", auth=True),
    create_request("Upload Training Doc", "POST", "/api/ai/training-docs/upload/", "form-data", auth=True)
]
collection["item"].append(create_folder("3. AI Engine", ai_items))

# 4. Subscriptions
sub_items = [
    create_request("List Plans", "GET", "/api/subscriptions/plans/"),
    create_request("Subscription Status", "GET", "/api/subscriptions/status/", auth=True),
    create_request("Start Trial", "POST", "/api/subscriptions/start-trial/", {"plan": "pro"}, auth=True),
    create_request("Cancel Subscription", "POST", "/api/subscriptions/cancel/", auth=True)
]
collection["item"].append(create_folder("4. Subscriptions", sub_items))

# 5. Payments
pay_items = [
    create_request("Create Checkout Session", "POST", "/api/payments/create-checkout/", {"plan": "pro", "billing_period": "monthly"}, auth=True),
    create_request("Webhook", "POST", "/api/payments/webhook/"),
    create_request("Billing History", "GET", "/api/payments/billing-history/", auth=True)
]
collection["item"].append(create_folder("5. Payments", pay_items))

# 6. Admin Panel
admin_items = [
    create_request("Platform Stats", "GET", "/api/admin-panel/stats/", auth=True),
    create_request("List Plans", "GET", "/api/admin-panel/plans/", auth=True),
    create_request("Create Plan", "POST", "/api/admin-panel/plans/", {
        "name": "pro",
        "display_name": "Pro Plan",
        "description": "Unlimited access",
        "price_monthly": "59.00",
        "price_yearly": "590.00",
        "document_limit": None,
        "warrant_document_limit": None,
        "can_incident_report": True,
        "can_search_warrant": True,
        "can_arrest_warrant": True,
        "can_export_pdf": True,
        "can_export_docx": True,
        "can_save_history": True,
        "support_level": "priority",
        "is_active": True,
        "sort_order": 2
    }, auth=True),
    create_request("Get Plan", "GET", "/api/admin-panel/plans/:pk/", auth=True),
    create_request("Update Plan", "PATCH", "/api/admin-panel/plans/:pk/", {"price_monthly": "29.00", "can_arrest_warrant": True}, auth=True),
    create_request("Delete Plan", "DELETE", "/api/admin-panel/plans/:pk/", auth=True),
    create_request("List Users", "GET", "/api/admin-panel/users/", auth=True),
    create_request("Update User", "PATCH", "/api/admin-panel/users/:pk/", {"role": "officer", "is_supervisor": True, "agency": 3}, auth=True),
    create_request("List Documents", "GET", "/api/admin-panel/documents/", auth=True),
    create_request("Get Document", "GET", "/api/admin-panel/documents/:pk/", auth=True),
    create_request("List Jurisdiction Profiles", "GET", "/api/admin-panel/jurisdiction-profiles/", auth=True),
    create_request("Create Jurisdiction Profile", "POST", "/api/admin-panel/jurisdiction-profiles/", {
        "name": "Georgia — State", "jurisdiction_type": "state", "state": "GA",
        "default_legal_citations": "O.C.G.A. § 17-5-21"
    }, auth=True),
    create_request("Update Jurisdiction Profile", "PATCH", "/api/admin-panel/jurisdiction-profiles/:pk/", {"default_legal_citations": "O.C.G.A. § 17-5-21, as amended"}, auth=True),
    create_request("Delete Jurisdiction Profile", "DELETE", "/api/admin-panel/jurisdiction-profiles/:pk/", auth=True),
    create_request("List Agencies", "GET", "/api/admin-panel/agencies/", auth=True),
    create_request("Create Agency", "POST", "/api/admin-panel/agencies/", {
        "name": "Smyrna Police Department", "jurisdiction_type": "municipal",
        "state": "GA", "county": "Cobb", "city": "Smyrna", "ori": "GA0330400",
        "requires_supervisor_review": True, "requires_prosecutor_review": False
    }, auth=True),
    create_request("Update Agency", "PATCH", "/api/admin-panel/agencies/:pk/", {"requires_prosecutor_review": True}, auth=True),
    create_request("Delete Agency", "DELETE", "/api/admin-panel/agencies/:pk/", auth=True),
    create_request("Upload Agency Seal", "POST", "/api/admin-panel/agencies/:pk/seal/", auth=True),
    create_request("Activity Log", "GET", "/api/admin-panel/activity/", auth=True)
]
collection["item"].append(create_folder("6. Admin Panel", admin_items))

# 7. Blog
blog_items = [
    create_request("List Posts", "GET", "/api/blog/posts/"),
    create_request("Create Post", "POST", "/api/blog/posts/", {
        "title": "Welcome",
        "content": "# Markdown body",
        "excerpt": "Short summary",
        "category": "news",
        "tags": ["update", "release"],
        "is_featured": False,
        "publish": True
    }, auth=True),
    create_request("Get Post", "GET", "/api/blog/posts/:slug/"),
    create_request("Update Post", "PATCH", "/api/blog/posts/:slug/", {"publish": False}, auth=True),
    create_request("Delete Post", "DELETE", "/api/blog/posts/:slug/", auth=True),
    create_request("Upload Media", "POST", "/api/blog/posts/:slug/media/", "form-data", auth=True),
    create_request("Upload Media (Embed)", "POST", "/api/blog/posts/:slug/media/", {
        "media_type": "video_url",
        "video_url": "https://youtube.com/watch?v=...",
        "caption": "Demo video"
    }, auth=True),
    create_request("Delete Media", "DELETE", "/api/blog/posts/:slug/media/:media_id/", auth=True),
    create_request("List Tags", "GET", "/api/blog/tags/")
]
collection["item"].append(create_folder("7. Blog", blog_items))

# 8. Health
collection["item"].append(create_request("Health Check", "GET", "/health/"))

import os

_OUTPUT_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), "law_backend_postman_collection.json")

with open(_OUTPUT_PATH, "w", encoding="utf-8") as f:
    json.dump(collection, f, indent=2)
print(f"Wrote {_OUTPUT_PATH}")
