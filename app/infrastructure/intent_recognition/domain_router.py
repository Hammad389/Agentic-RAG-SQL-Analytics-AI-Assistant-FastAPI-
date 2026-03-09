"""
Domain Router — keyword-based domain inference.

NOTE: This is intentionally easy to customize.
To add a new domain, just add a new key + keyword list to DOMAIN_KEYWORDS below.
To remove a domain, delete its entry.
"""

import re
from typing import List, Optional

# ─────────────────────────────────────────────
# CUSTOMIZE THIS: Add / remove domains freely
# ─────────────────────────────────────────────
DOMAIN_KEYWORDS = {
    "notifications": ["notification", "notifications", "unread", "read", "alerts", "alert", "digest"],
    "tasks": ["task", "tasks", "overdue", "assigned", "assignee", "priority", "backlog", "to_do", "todo"],
    "payments": ["payment", "payments", "invoice", "invoices", "rent", "paid", "failed", "processing"],
    "property": ["property", "properties", "unit", "units", "listing", "listings", "vacant", "occupied", "building", "buildings"],
    "rental": ["application", "applications", "tenant", "tenants", "lease", "leases", "under_review"],
    "teams": ["team", "teams", "members", "member"],
    "rbac": ["role", "roles", "permission", "permissions", "rbac", "access"],
    "attachments": ["attachment", "attachments", "file", "files", "upload", "uploaded", "document", "documents"],
    "user": ["user", "users", "owner", "owners", "vendor", "vendors", "signup", "signed up"],
}


def infer_domains(text: str) -> Optional[List[str]]:
    t = text.lower()
    found = []
    for domain, kws in DOMAIN_KEYWORDS.items():
        for kw in kws:
            if re.search(rf"\b{re.escape(kw)}\b", t):
                found.append(domain)
                break
    found = list(dict.fromkeys(found))   # dedupe, stable order
    return found or None
